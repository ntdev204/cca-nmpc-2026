cmake_minimum_required(VERSION 3.16)
project(cca_control LANGUAGES CXX)

find_package(ament_cmake REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(cca_control_core STATIC
  src/can.cpp
  src/context.cpp
  src/controller.cpp
  src/snapshot_gate.cpp
  src/stm_serial.cpp
)
target_include_directories(cca_control_core PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(cca_control_core PUBLIC cxx_std_20)
set_target_properties(cca_control_core PROPERTIES POSITION_INDEPENDENT_CODE ON)
if(MSVC)
  target_compile_options(cca_control_core PRIVATE /W4 /permissive-)
else()
  target_compile_options(cca_control_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

install(TARGETS cca_control_core
  EXPORT export_cca_control
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(EXPORT export_cca_control
  FILE cca_control_targets.cmake
  NAMESPACE cca_control::
  DESTINATION share/${PROJECT_NAME}/cmake
)
install(DIRECTORY include/ DESTINATION include)
ament_export_include_directories(include)
ament_export_targets(export_cca_control HAS_LIBRARY_TARGET)
ament_package()
