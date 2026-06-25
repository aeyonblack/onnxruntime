# ONNX Runtime C++ Custom Operator Build

This readme demonstrates how to build a **custom ONNX Runtime C++ operator** that links against a local ONNX Runtime installation.  
It supports **Linux**, **macOS**, and **Windows** builds using **CMake**.

---

##  Build Instructions

### **1. Prerequisites**

Before building, make sure you have the following dependencies installed:

| Dependency | Version / Notes | Install Command |
|-------------|----------------|------------------|
| **CMake** | ≥ 3.18 | See below per OS |
| **ONNX Runtime** | ≥ 1.15.1 | [Download prebuilt package](https://github.com/microsoft/onnxruntime/releases) or build from source |
| **C++ Compiler** | GCC ≥ 9 / Clang ≥ 12 / MSVC ≥ 2019 | Preinstalled on most systems |

---

## **Linux**

### **Install dependencies**
```bash
sudo apt update
sudo apt install -y build-essential cmake git
```

### **Set up environment**
```bash
export ONNXRUNTIME_DIR="$HOME/libs/onnxruntime-1.15.1"
```

### **Build**
```bash
cd ./api/src/onnxruntime/csrc

rm -rf build && mkdir build && cd build

cmake ..   -DONNXRUNTIME_DIR="$ONNXRUNTIME_DIR"   -DCMAKE_BUILD_TYPE=Release

cmake --build . --config Release -j$(nproc)
```

### **Result**
Your compiled library will be located in:
```
build/libnms_rotated_ort.so
```

---

## **macOS**

### **Install dependencies**
Using Homebrew:
```bash
brew install cmake
```

### **Set up environment**
```bash
export ONNXRUNTIME_DIR="$HOME/libs/onnxruntime-1.15.1"
```

### **Build**
```bash
cd ./api/src/onnxruntime/csrc

rm -rf build && mkdir build && cd build

cmake .. -DONNXRUNTIME_DIR="$ONNXRUNTIME_DIR"   -DCMAKE_OSX_ARCHITECTURES=x86_64   -DCMAKE_BUILD_TYPE=Release

cmake --build . --config Release -j$(sysctl -n hw.logicalcpu)
```

### **Result**
The compiled shared library will appear as:
```
build/libnms_rotated_ort.dylib
```

---

## **Windows (MSVC + PowerShell)**

### **Install dependencies**
- [CMake for Windows](https://cmake.org/download/)
- [ONNX Runtime Windows package](https://github.com/microsoft/onnxruntime/releases)
- Visual Studio 2019 or newer (with C++ build tools)

### **Set up environment**
```powershell
$Env:ONNXRUNTIME_DIR = "C:\libs\onnxruntime-1.15.1"
```

### **Build**
```powershell
cd ./api/src/onnxruntime/csrc

mkdir build
cd build

cmake .. -A x64 -DCMAKE_BUILD_TYPE=Release -DONNXRUNTIME_DIR=$Env:ONNXRUNTIME_DIR
cmake --build . --config Release
```

### **Result**
The output will be in:
```
build\bin\Release\nms_rotated_ort.dll
```

---

## **Usage**

Once built, you can place the custom op into the location:
```
.\api\lib
```

Also add the ONNX Runtime `onnxruntime1.15.1` library to:
```
.\api\lib
```

This ensures both the custom operator and ONNX Runtime library can be found at runtime.

---

##  **Troubleshooting**

| Issue | Cause | Fix |
|--------|--------|-----|
| `CMakeCache.txt directory ... is different` | You reused a build folder from another path | Run `rm -rf build && mkdir build` |
| `onnxruntime_providers.h not found` | Incorrect or missing ONNXRUNTIME_DIR | Set `ONNXRUNTIME_DIR` to the correct include/lib path |
| Linking errors | Missing or mismatched ONNX Runtime version | Use the same ONNX Runtime version you built your op against |
| `illegal instruction` on macOS | Architecture mismatch | Add `-DCMAKE_OSX_ARCHITECTURES=x86_64` or `arm64` |

---

## **Clean Build**

To clean the project safely:
```bash
rm -rf build
mkdir build && cd build
```

or
```bash
cmake --build . --target clean
```

---