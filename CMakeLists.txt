cmake_minimum_required(VERSION 3.20)

project(tauon-native VERSION 11.1.1 LANGUAGES CXX)

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter Development.Embed)
find_package(SDL3 CONFIG REQUIRED)

add_executable(tauon-native
	src/tauon_native/main.cpp
)

target_compile_features(tauon-native PRIVATE cxx_std_17)
target_compile_definitions(tauon-native PRIVATE
	TAUON_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/src"
	TAUON_PYTHON_SITE_PACKAGES="${Python3_SITELIB}"
	TAUON_VERSION="${PROJECT_VERSION}"
)
target_link_libraries(tauon-native PRIVATE
	Python3::Python
	SDL3::SDL3
)

if(MSVC)
	target_compile_options(tauon-native PRIVATE /W4)
else()
	target_compile_options(tauon-native PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(APPLE)
	target_link_libraries(tauon-native PRIVATE "-framework CoreFoundation")
endif()

install(TARGETS tauon-native RUNTIME DESTINATION bin)
