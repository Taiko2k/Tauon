cmake_minimum_required(VERSION 3.20)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" TAUON_PYPROJECT)
string(REGEX MATCH "version[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\"" TAUON_VERSION_MATCH "${TAUON_PYPROJECT}")
if(NOT CMAKE_MATCH_1)
	message(FATAL_ERROR "Unable to read project.version from pyproject.toml")
endif()
set(TAUON_PROJECT_VERSION "${CMAKE_MATCH_1}")

project(tauon-native VERSION "${TAUON_PROJECT_VERSION}" LANGUAGES CXX)

include(GNUInstallDirs)

option(
	TAUON_DEVELOPMENT_BUILD
	"Embed source-tree and selected Python environment paths for local development"
	ON
)

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter Development.Embed)
find_package(SDL3 CONFIG REQUIRED)

add_executable(tauon-native
	src/tauon_native/main.cpp
	src/tauon_native/native_render.cpp
)

target_compile_features(tauon-native PRIVATE cxx_std_17)
target_compile_definitions(tauon-native PRIVATE
	TAUON_VERSION="${PROJECT_VERSION}"
)
if(TAUON_DEVELOPMENT_BUILD)
	target_compile_definitions(tauon-native PRIVATE
		TAUON_DEVELOPMENT_BUILD=1
		TAUON_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}/src"
		TAUON_PYTHON_SITE_PACKAGES="${Python3_SITELIB}"
	)
endif()
target_link_libraries(tauon-native PRIVATE
	Python3::Python
	SDL3::SDL3
)

if(MSVC)
	target_compile_options(tauon-native PRIVATE /W4)
else()
	target_compile_options(tauon-native PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(WIN32)
	string(REPLACE "." "," TAUON_VERSION_COMMA "${PROJECT_VERSION}")
	configure_file(
		"${CMAKE_CURRENT_SOURCE_DIR}/src/tauon_native/tauon.rc.in"
		"${CMAKE_CURRENT_BINARY_DIR}/tauon.rc"
		@ONLY
	)
	target_sources(tauon-native PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/tauon.rc")
	target_link_libraries(tauon-native PRIVATE shell32 ws2_32)
	set_target_properties(tauon-native PROPERTIES WIN32_EXECUTABLE TRUE)
endif()

if(APPLE)
	target_link_libraries(tauon-native PRIVATE "-framework CoreFoundation")
	set_target_properties(tauon-native PROPERTIES
		BUILD_RPATH "@executable_path/../Frameworks"
		INSTALL_RPATH "@executable_path/../Frameworks"
	)
elseif(UNIX)
	set_target_properties(tauon-native PROPERTIES
		BUILD_RPATH "\$ORIGIN/_internal/lib"
		INSTALL_RPATH "\$ORIGIN/_internal/lib"
	)
endif()

install(TARGETS tauon-native RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
