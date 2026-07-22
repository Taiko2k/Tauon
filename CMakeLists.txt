cmake_minimum_required(VERSION 3.20)

project(tauon-native VERSION 11.1.1 LANGUAGES CXX)

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter Development.Embed)
find_package(SDL3 CONFIG REQUIRED)

add_executable(tauon-native
	src/tauon_native/main.cpp
)
add_library(tauon-python-host SHARED
	src/tauon_native/python_host.cpp
)

target_compile_features(tauon-native PRIVATE cxx_std_17)
target_compile_features(tauon-python-host PRIVATE cxx_std_17)
target_compile_definitions(tauon-native PRIVATE
	TAUON_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/src"
	TAUON_PYTHON_SITE_PACKAGES="${Python3_SITELIB}"
	TAUON_PYTHON_HOST_FILENAME="$<TARGET_FILE_NAME:tauon-python-host>"
	TAUON_VERSION="${PROJECT_VERSION}"
)
target_link_libraries(tauon-native PRIVATE
	SDL3::SDL3
)
target_link_libraries(tauon-python-host PRIVATE Python3::Python)
add_dependencies(tauon-native tauon-python-host)

if(MSVC)
	target_compile_options(tauon-native PRIVATE /W4)
	target_compile_options(tauon-python-host PRIVATE /W4)
else()
	target_compile_options(tauon-native PRIVATE -Wall -Wextra -Wpedantic)
	target_compile_options(tauon-python-host PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(APPLE)
	target_link_libraries(tauon-native PRIVATE "-framework CoreFoundation")
endif()

install(TARGETS tauon-native tauon-python-host
	RUNTIME DESTINATION bin
	LIBRARY DESTINATION bin
)
