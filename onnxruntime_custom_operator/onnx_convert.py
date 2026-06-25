# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def ensure_python_package(import_name: str, package_name: str | None = None):
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name or import_name]
        )


def get_yolov8_model(onnx_model_name: Path):
    ensure_python_package("ultralytics")
    import ultralytics

    onnx_model_name.parent.mkdir(parents=True, exist_ok=True)
    pt_model = Path("yolov8n.pt")
    model = ultralytics.YOLO(str(pt_model))  # load a pretrained model
    success = model.export(format="onnx")  # export the model to ONNX format
    assert success, "Failed to export yolov8n.pt to onnx"

    shutil.move(pt_model.with_suffix('.onnx'), onnx_model_name)


def add_pre_post_processing_to_yolo(input_model_file: Path, output_model_file: Path):
    """Construct the pipeline for an end2end model with pre and post processing. 
    The final model can take raw image binary as inputs and output the result in raw image file.

    Args:
        input_model_file (Path): The onnx yolo model.
        output_model_file (Path): where to save the final onnx model.
    """
    if not Path(input_model_file).is_file():
        get_yolov8_model(input_model_file)

    ensure_python_package("onnxruntime_extensions", "onnxruntime-extensions")
    from onnxruntime_extensions.tools import add_pre_post_processing_to_model as add_ppp

    output_model_file.parent.mkdir(parents=True, exist_ok=True)
    add_ppp.yolo_detection(input_model_file, output_model_file, "jpg", onnx_opset=18)


def convert_onnx_to_ort(
    onnx_model_file: Path,
    ort_model_file: Path,
    custom_op_library: Path | None = None,
):
    """Convert an ONNX model to ORT format for minimal/mobile ONNX Runtime builds."""
    ensure_python_package("onnx")
    ensure_python_package("onnxruntime")

    output_dir = ort_model_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    convert_command = [
        sys.executable,
        "-m",
        "onnxruntime.tools.convert_onnx_models_to_ort",
        str(onnx_model_file),
        "--output_dir",
        str(output_dir),
        "--optimization_style",
        "Fixed",
    ]
    if custom_op_library:
        convert_command.extend(["--custom_op_library", str(custom_op_library)])

    try:
        subprocess.check_call(convert_command)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "ONNX-to-ORT conversion failed. If the model contains custom ops "
            "such as mmdeploy:NMSRotated, pass the ONNX Runtime custom-op "
            "library with --custom-op-library."
        ) from error

    generated_model = output_dir / f"{onnx_model_file.stem}.ort"
    if generated_model != ort_model_file:
        generated_model.replace(ort_model_file)


def copy_model_to_android_raw(model_file: Path, raw_resource_file: Path):
    raw_resource_file.parent.mkdir(parents=True, exist_ok=True)

    # Android resources cannot contain two files with the same resource name.
    for existing_model in raw_resource_file.parent.glob(f"{raw_resource_file.stem}.*"):
        if existing_model != raw_resource_file:
            backup_file = Path("app/src/main/ml") / existing_model.name
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(existing_model, backup_file)

    if model_file.resolve() != raw_resource_file.resolve():
        shutil.copyfile(model_file, raw_resource_file)


def test_inference(model_file: Path):
    ensure_python_package("onnxruntime")
    ensure_python_package("onnxruntime_extensions", "onnxruntime-extensions")

    import onnxruntime as ort
    import numpy as np
    import onnxruntime_extensions

    providers = ['CPUExecutionProvider']
    session_options = ort.SessionOptions()
    session_options.register_custom_ops_library(onnxruntime_extensions.get_library_path())

    image_file = Path("app/src/main/assets/test_object_detection_0.jpg")
    image = np.frombuffer(image_file.read_bytes(), dtype=np.uint8)
    session = ort.InferenceSession(str(model_file), providers=providers, sess_options=session_options)

    inname = [i.name for i in session.get_inputs()]
    inp = {inname[0]: image}
    outputs = session.run(['image_out'], inp)[0]
    result_file = Path("test/data/result.jpg")
    result_file.parent.mkdir(parents=True, exist_ok=True)
    result_file.write_bytes(outputs)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert an ONNX model to ORT format for Android."
    )
    parser.add_argument(
        "--onnx-model",
        type=Path,
        default=Path("app/src/main/res/raw/security_zone.onnx"),
        help="Path for the ONNX model to convert.",
    )
    parser.add_argument(
        "--android-raw-dir",
        type=Path,
        default=Path("app/src/main/res/raw"),
        help="Android raw resource directory that receives the ORT model.",
    )
    parser.add_argument(
        "--conversion-dir",
        type=Path,
        default=Path("build/converted-models"),
        help="Temporary output directory for generated ORT files.",
    )
    parser.add_argument(
        "--custom-op-library",
        type=Path,
        default=None,
        help="Path to a native ONNX Runtime custom-op library required by the model.",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip a local inference smoke test after conversion.",
    )
    parser.add_argument(
        "--with-pre-post-processing",
        action="store_true",
        help=(
            "Generate the older end-to-end model with ONNX Runtime Extensions "
            "DecodeImage/EncodeImage custom ops. Leave this off for the Android "
            "minimal runtime build."
        ),
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    onnx_model_name = args.onnx_model
    if not onnx_model_name.is_file() and args.with_pre_post_processing:
        print("Generating YOLOv8 ONNX model...")
        get_yolov8_model(onnx_model_name)
    elif not onnx_model_name.is_file():
        raise FileNotFoundError(f"ONNX model not found: {onnx_model_name}")

    if args.with_pre_post_processing:
        onnx_e2e_model_name = onnx_model_name.with_name("yolov8n_with_pre_post_processing.onnx")
        print("Adding ONNX Runtime Extensions pre/post processing...")
        add_pre_post_processing_to_yolo(onnx_model_name, onnx_e2e_model_name)
        model_to_convert = onnx_e2e_model_name
    else:
        model_to_convert = onnx_model_name

    ort_e2e_model_name = args.conversion_dir / model_to_convert.with_suffix(".ort").name
    android_ort_model = args.android_raw_dir / ort_e2e_model_name.name

    print(f"Converting {model_to_convert} to ORT format...")
    convert_onnx_to_ort(model_to_convert, ort_e2e_model_name, args.custom_op_library)
    print(f"Copying {ort_e2e_model_name} to {android_ort_model}...")
    copy_model_to_android_raw(ort_e2e_model_name, android_ort_model)

    if not args.skip_test:
        print("Running local ORT-format inference smoke test...")
        if args.with_pre_post_processing:
            test_inference(ort_e2e_model_name)
        else:
            print("Skipping smoke test for the base model; Android performs preprocessing/postprocessing.")

    print(f"Done. Android model resource: {android_ort_model}")
