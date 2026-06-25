cmake_minimum_required(VERSION 3.14)
project(nms_rotated_ort LANGUAGES CXX)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Require ONNX Runtime SDK root
if(NOT DEFINED ONNXRUNTIME_DIR)
    message(FATAL_ERROR "Pass -DONNXRUNTIME_DIR pointing to your ONNX Runtime SDK root")
endif()

# Optional include/lib dirs
set(ONNXRUNTIME_INCLUDE_DIR "${ONNXRUNTIME_DIR}/include" CACHE PATH "ONNX Runtime include directory")
set(ONNXRUNTIME_LIB_DIR "${ONNXRUNTIME_DIR}/lib" CACHE PATH "ONNX Runtime library directory")

# Try to find the ONNX Runtime CMake package first (cleanest)
find_package(onnxruntime CONFIG QUIET
    HINTS "${ONNXRUNTIME_DIR}/lib/cmake/onnxruntime"
)

# Sources
add_library(nms_rotated_ort SHARED
    ${CMAKE_CURRENT_SOURCE_DIR}/nms_rotated/nms_rotated.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/common/ort_utils.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/onnxruntime_register.cpp
)

set_target_properties(nms_rotated_ort PROPERTIES OUTPUT_NAME "nms_rotated_ort")

# Include directories
target_include_directories(nms_rotated_ort PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/nms_rotated
    ${CMAKE_CURRENT_SOURCE_DIR}/common
)

# Export macro
target_compile_definitions(nms_rotated_ort PRIVATE MMDEPLOY_API_EXPORTS)

# Link libraries
if(onnxruntime_FOUND)
    message(STATUS "Using onnxruntime CMake package")
    target_link_libraries(nms_rotated_ort PRIVATE onnxruntime::onnxruntime)
else()
    message(WARNING "onnxruntime package not found; falling back to manual include/link")
    # **Add both include paths manually so headers can be found**
    target_include_directories(nms_rotated_ort PRIVATE
        ${ONNXRUNTIME_DIR}/include
        ${ONNXRUNTIME_DIR}/include/onnxruntime/core/session
    )
    target_link_directories(nms_rotated_ort PRIVATE ${ONNXRUNTIME_LIB_DIR})
    target_link_libraries(nms_rotated_ort PRIVATE
        $<$<PLATFORM_ID:Windows>:onnxruntime.lib>
        $<$<PLATFORM_ID:Linux>:onnxruntime>
        $<$<PLATFORM_ID:Darwin>:onnxruntime>
    )
endif()

# RPATH for Unix/macOS
if(APPLE)
    target_compile_options(nms_rotated_ort PRIVATE -mmacosx-version-min=11.0)
    set_target_properties(nms_rotated_ort PROPERTIES
        MACOSX_RPATH ON
        BUILD_WITH_INSTALL_RPATH ON
        INSTALL_RPATH "@loader_path"
    )
elseif(UNIX)
    set_target_properties(nms_rotated_ort PROPERTIES
        BUILD_RPATH "${ONNXRUNTIME_LIB_DIR}"
        BUILD_WITH_INSTALL_RPATH ON
        INSTALL_RPATH "\$ORIGIN"
    )
endif()

# Windows output dirs
if(WIN32)
    set_target_properties(nms_rotated_ort PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )
    target_compile_options(nms_rotated_ort PRIVATE /EHsc /permissive-)
endif()
