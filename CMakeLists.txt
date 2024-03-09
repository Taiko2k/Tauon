cmake_minimum_required(VERSION 3.10)
project(phazor)

add_library(phazor SHARED src/phazor/phazor.c)

find_package(PkgConfig REQUIRED)

pkg_check_modules(phazor REQUIRED flac libopenmpt libmpg123 opus opusfile wavpack samplerate)

find_package(kissfft CONFIG COMPONENTS float)
if(NOT kissfft_FOUND)
	add_subdirectory(src/phazor/kissfft)
endif()

target_include_directories(phazor PRIVATE ${phazor_INCLUDE_DIRS})
target_link_libraries(phazor kissfft::kissfft ${phazor_LIBRARIES})


install(TARGETS phazor DESTINATION ${CMAKE_SOURCE_DIR}/lib)
