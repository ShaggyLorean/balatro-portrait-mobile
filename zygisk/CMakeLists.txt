cmake_minimum_required(VERSION 3.22)
project(balatroportrait C CXX ASM)

set(SH "${CMAKE_SOURCE_DIR}/deps/shadowhook/shadowhook/src/main/cpp")

# ---- shadowhook (static, linked into our module) ----
file(GLOB SH_SRC
  "${SH}/*.c"
  "${SH}/arch/arm64/*.c" "${SH}/arch/arm64/*.S"
  "${SH}/common/*.c"
  "${SH}/third_party/xdl/*.c")
# sh_jni.c intentionally excluded — we don't want shadowhook's JNI_OnLoad
list(FILTER SH_SRC EXCLUDE REGEX "sh_jni\\.c$")

add_library(shadowhook STATIC ${SH_SRC})
target_include_directories(shadowhook PUBLIC "${SH}/include"
  PRIVATE "${SH}" "${SH}/arch/arm64" "${SH}/common"
          "${SH}/third_party/xdl" "${SH}/third_party/bsd" "${SH}/third_party/lss")
target_compile_options(shadowhook PRIVATE -Os -ffunction-sections -fdata-sections -Wno-everything)
target_link_libraries(shadowhook PUBLIC log)

# ---- shadowhook_nothing (separate .so, shipped to /system/lib64) ----
add_library(shadowhook_nothing SHARED "${SH}/nothing/sh_nothing.c")
target_compile_options(shadowhook_nothing PRIVATE -Oz -Wno-everything
  -fno-ident -fno-unwind-tables -fno-asynchronous-unwind-tables)
target_link_options(shadowhook_nothing PRIVATE
  -Wl,-z,max-page-size=16384 -Wl,--strip-all -Wl,--as-needed
  -Wl,--hash-style=sysv -Wl,--build-id=none
  -nostdlib -nostartfiles -nodefaultlibs)

# ---- our Zygisk module ----
add_library(balatro_portrait SHARED src/module.cpp)
target_include_directories(balatro_portrait PRIVATE
  "${SH}/include" "${CMAKE_SOURCE_DIR}/deps/zsample/module/jni" "${CMAKE_SOURCE_DIR}/src")
target_compile_options(balatro_portrait PRIVATE -Os)
target_link_libraries(balatro_portrait PRIVATE shadowhook log)
target_link_options(balatro_portrait PRIVATE -Wl,-z,max-page-size=16384)
