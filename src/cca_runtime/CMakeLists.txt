cmake_minimum_required(VERSION 3.16)
project(cca_runtime LANGUAGES CXX)

find_package(ament_cmake REQUIRED)
find_package(cca_control REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(ROS_DEPENDENCIES
  geometry_msgs
  nav_msgs
  rclcpp
  sensor_msgs
  std_msgs
  tf2
  tf2_geometry_msgs
)

add_executable(cca_reference_node src/cca_reference_node.cpp)
add_executable(cca_nmpc_node src/cca_nmpc_node.cpp)
foreach(target cca_reference_node cca_nmpc_node)
  target_link_libraries(${target} cca_control::cca_control_core)
  target_compile_features(${target} PRIVATE cxx_std_20)
  ament_target_dependencies(${target} ${ROS_DEPENDENCIES})
  if(MSVC)
    target_compile_options(${target} PRIVATE /W4 /permissive-)
  else()
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
  endif()
endforeach()

install(TARGETS cca_reference_node cca_nmpc_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)
install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
ament_export_dependencies(cca_control ${ROS_DEPENDENCIES})
ament_package()
