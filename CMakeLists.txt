cmake_minimum_required(VERSION 3.20)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml" TAUON_PYPROJECT)
string(REGEX MATCH "version[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\"" TAUON_VERSION_MATCH "${TAUON_PYPROJECT}")
if(NOT CMAKE_MATCH_1)
	message(FATAL_ERROR "Unable to read project.version from pyproject.toml")
endif()
set(TAUON_PROJECT_VERSION "${CMAKE_MATCH_1}")

project(tauon VERSION "${TAUON_PROJECT_VERSION}" LANGUAGES C CXX)

include(GNUInstallDirs)

get_property(TAUON_MULTI_CONFIG GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(NOT TAUON_MULTI_CONFIG AND NOT CMAKE_BUILD_TYPE)
	set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

find_package(Python3 3.11 REQUIRED COMPONENTS Interpreter Development.Module Development.Embed)
find_package(SDL3 CONFIG REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(Threads REQUIRED)
find_package(Gettext)

# scikit-build-core installs relative to the wheel's platlib (site-packages)
# and provides the environment's scripts directory, a new staging directory
# on every build, so these are plain variables rather than cache entries.
# Plain CMake installs target the selected interpreter's site-packages and
# the prefix's bin.
if(SKBUILD)
	set(TAUON_PACKAGE_INSTALL_DIR "tauon")
	set(TAUON_SCRIPTS_INSTALL_DIR "${SKBUILD_SCRIPTS_DIR}")
else()
	set(TAUON_PACKAGE_INSTALL_DIR "${Python3_SITEARCH}/tauon" CACHE PATH "Install directory of the tauon Python package")
	set(TAUON_SCRIPTS_INSTALL_DIR "${CMAKE_INSTALL_BINDIR}" CACHE PATH "Install directory of the tauon launcher")
endif()

# Native launcher

add_executable(tauon-native
	src/tauon_native/ipc.cpp
	src/tauon_native/main.cpp
	src/tauon_native/native_render.cpp
)

target_compile_features(tauon-native PRIVATE cxx_std_17)
target_compile_definitions(tauon-native PRIVATE
	TAUON_VERSION="${PROJECT_VERSION}"
)
target_link_libraries(tauon-native PRIVATE
	Python3::Python
	SDL3::SDL3
	Threads::Threads
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
	target_link_libraries(tauon-native PRIVATE shell32 advapi32 user32 gdi32 ole32 uuid)
	set_target_properties(tauon-native PROPERTIES WIN32_EXECUTABLE TRUE)
endif()

# The bundle staging tool rewrites these for the bundled layout. Installed
# launchers also keep the non-system directories they were linked against,
# such as a locally built SDL3 prefix.
set_target_properties(tauon-native PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)
if(APPLE)
	target_link_libraries(tauon-native PRIVATE "-framework CoreFoundation")
	# GObject typelibs name their libraries by leaf name (libglib-2.0.0.dylib),
	# which dlopen resolves through the launcher's rpaths. The python
	# executable finds Homebrew's through its framework's /opt/homebrew/lib
	# rpath, so the launcher carries the embedded Python's absolute rpaths too.
	# The bundle staging tool removes absolute rpaths again.
	set(TAUON_MACOS_RPATHS "@executable_path/../Frameworks")
	find_program(TAUON_OTOOL otool)
	foreach(python_library IN LISTS Python3_LIBRARIES)
		if(TAUON_OTOOL AND EXISTS "${python_library}")
			execute_process(
				COMMAND "${TAUON_OTOOL}" -l "${python_library}"
				OUTPUT_VARIABLE python_load_commands
				ERROR_QUIET
			)
			string(REGEX MATCHALL "path /[^\n]* \\(offset" python_rpaths "${python_load_commands}")
			foreach(python_rpath IN LISTS python_rpaths)
				string(REGEX REPLACE "^path (.*) \\(offset$" "\\1" python_rpath "${python_rpath}")
				list(APPEND TAUON_MACOS_RPATHS "${python_rpath}")
			endforeach()
		endif()
	endforeach()
	list(REMOVE_DUPLICATES TAUON_MACOS_RPATHS)
	set_target_properties(tauon-native PROPERTIES
		BUILD_RPATH "${TAUON_MACOS_RPATHS}"
		INSTALL_RPATH "${TAUON_MACOS_RPATHS}"
	)
elseif(UNIX)
	set_target_properties(tauon-native PROPERTIES
		BUILD_RPATH "\$ORIGIN/_internal/lib"
		INSTALL_RPATH "\$ORIGIN/_internal/lib"
	)
endif()

set_target_properties(tauon-native PROPERTIES OUTPUT_NAME tauon)
install(TARGETS tauon-native RUNTIME DESTINATION "${TAUON_SCRIPTS_INSTALL_DIR}")

# Phazor audio backend, loaded by tauon.t_modules.t_phazor through ctypes as
# lib<name> from the tauon package directory

set(TAUON_PHAZOR_PACKAGES samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme)
pkg_check_modules(PHAZOR_DEPS REQUIRED IMPORTED_TARGET ${TAUON_PHAZOR_PACKAGES})

# Headers are included with their directory prefix (opus/opusfile.h,
# gme/gme.h), while some .pc files point inside that directory
set(TAUON_PHAZOR_INCLUDE_DIRS "")
foreach(package IN LISTS TAUON_PHAZOR_PACKAGES)
	pkg_get_variable(package_include_dir ${package} includedir)
	if(package_include_dir)
		list(APPEND TAUON_PHAZOR_INCLUDE_DIRS "${package_include_dir}")
	endif()
endforeach()
list(REMOVE_DUPLICATES TAUON_PHAZOR_INCLUDE_DIRS)

function(tauon_add_phazor target backend)
	add_library(${target} SHARED
		src/phazor/phazor.c
		src/phazor/kissfft/kiss_fft.c
		src/phazor/kissfft/kiss_fftr.c
	)
	target_compile_features(${target} PRIVATE c_std_17)
	target_compile_definitions(${target} PRIVATE ${backend})
	target_include_directories(${target} PRIVATE
		src/phazor
		${TAUON_PHAZOR_INCLUDE_DIRS}
	)
	# Python symbols resolve from the launcher that loads the library
	target_link_libraries(${target} PRIVATE
		Python3::Module
		PkgConfig::PHAZOR_DEPS
		Threads::Threads
		${CMAKE_DL_LIBS}
	)
	if(NOT MSVC)
		target_compile_options(${target} PRIVATE -Wall)
	endif()
	if(UNIX AND NOT APPLE)
		target_link_libraries(${target} PRIVATE m)
	endif()
	install(TARGETS ${target}
		LIBRARY DESTINATION "${TAUON_PACKAGE_INSTALL_DIR}"
		RUNTIME DESTINATION "${TAUON_PACKAGE_INSTALL_DIR}"
		ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}" EXCLUDE_FROM_ALL
	)
endfunction()

tauon_add_phazor(phazor MINI)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
	pkg_check_modules(PIPEWIRE IMPORTED_TARGET libpipewire-0.3)
	if(PIPEWIRE_FOUND)
		tauon_add_phazor(phazor-pw PIPE)
		target_link_libraries(phazor-pw PRIVATE PkgConfig::PIPEWIRE)
	else()
		message(STATUS "PipeWire not found, skipping phazor-pw")
	endif()
endif()

# Translations

if(GETTEXT_MSGFMT_EXECUTABLE)
	file(GLOB TAUON_PO_FILES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/locale/*/LC_MESSAGES/tauon.po")
	set(TAUON_MO_FILES "")
	foreach(po_file IN LISTS TAUON_PO_FILES)
		get_filename_component(messages_dir "${po_file}" DIRECTORY)
		get_filename_component(language_dir "${messages_dir}" DIRECTORY)
		get_filename_component(language "${language_dir}" NAME)
		set(mo_file "${CMAKE_CURRENT_BINARY_DIR}/locale/${language}/LC_MESSAGES/tauon.mo")
		add_custom_command(
			OUTPUT "${mo_file}"
			COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/locale/${language}/LC_MESSAGES"
			COMMAND "${GETTEXT_MSGFMT_EXECUTABLE}" -o "${mo_file}" "${po_file}"
			DEPENDS "${po_file}"
			VERBATIM
		)
		list(APPEND TAUON_MO_FILES "${mo_file}")
	endforeach()
	add_custom_target(tauon-translations ALL DEPENDS ${TAUON_MO_FILES})
	install(DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/locale" DESTINATION "${TAUON_PACKAGE_INSTALL_DIR}")
else()
	message(WARNING "msgfmt not found, translations will not be installed")
endif()
