cmake_minimum_required(VERSION 3.21)
project(control_runtime LANGUAGES CXX)

add_library(control_core
    src/can.cpp
    src/context.cpp
    src/controller.cpp
    src/snapshot_gate.cpp
    src/stm_serial.cpp
)
target_include_directories(control_core PUBLIC include)
target_compile_features(control_core PUBLIC cxx_std_20)
set_target_properties(control_core PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_library(control_transport SHARED src/stm_c_api.cpp src/controller_c_api.cpp)
target_link_libraries(control_transport PRIVATE control_core)
target_include_directories(control_transport PUBLIC include)
target_compile_features(control_transport PUBLIC cxx_std_20)
set_target_properties(control_transport PROPERTIES OUTPUT_NAME control_transport)

add_executable(stm_probe stm_probe.cpp)
target_link_libraries(stm_probe PRIVATE control_core)
target_compile_features(stm_probe PRIVATE cxx_std_20)

if(MSVC)
    target_compile_options(control_core PRIVATE /W4 /WX /permissive-)
    target_compile_options(control_transport PRIVATE /W4 /WX /permissive-)
else()
    target_compile_options(control_core PRIVATE -Wall -Wextra -Wpedantic -Werror)
    target_compile_options(control_transport PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

if(MSVC)
    target_compile_options(stm_probe PRIVATE /W4 /WX /permissive-)
else()
    target_compile_options(stm_probe PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(control_tests test_core.cpp)
    target_link_libraries(control_tests PRIVATE control_core control_transport)
    if(MSVC)
        target_compile_options(control_tests PRIVATE /W4 /WX /permissive-)
    else()
        target_compile_options(
            control_tests PRIVATE -Wall -Wextra -Wpedantic -Werror
        )
    endif()
    add_test(NAME control_tests COMMAND control_tests)
endif()
