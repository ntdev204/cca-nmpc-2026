cmake_minimum_required(VERSION 3.16)
project(cca_hardware LANGUAGES CXX)

find_package(ament_cmake REQUIRED)
find_package(cca_control REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(cca_stm_bridge src/stm_bridge_node.cpp)
target_link_libraries(cca_stm_bridge cca_control::cca_control_core)
target_compile_features(cca_stm_bridge PRIVATE cxx_std_20)
ament_target_dependencies(cca_stm_bridge
  geometry_msgs nav_msgs rclcpp sensor_msgs std_msgs tf2 tf2_geometry_msgs tf2_ros
)
if(MSVC)
  target_compile_options(cca_stm_bridge PRIVATE /W4 /permissive-)
else()
  target_compile_options(cca_stm_bridge PRIVATE -Wall -Wextra -Wpedantic)
endif()

install(TARGETS cca_stm_bridge
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)
ament_export_dependencies(cca_control geometry_msgs nav_msgs rclcpp sensor_msgs std_msgs tf2 tf2_geometry_msgs tf2_ros)
ament_package()
