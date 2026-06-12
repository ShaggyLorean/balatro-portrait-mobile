// Balatro Portrait — Zygisk module.
// Injects portrait Lua (luaL_loadbuffer swap) + forces portrait orientation
// (Android_JNI_SetOrientation -> JNI setRequestedOrientation(1)) into Balatro.
#include <cstring>
#include <cstdio>
#include <unistd.h>
#include <dlfcn.h>
#include <jni.h>
#include <android/log.h>

#include "zygisk.hpp"
#include "shadowhook.h"
#include "assets_gen.h"

// Provided by our shadowhook patch (sh_linker.c): absolute path to load
// libshadowhook_nothing.so from, instead of the default linker search path.
extern "C" char sh_linker_nothing_override_path[512];

#define TARGET_PKG "com.playstack.balatro.android"
#define LOG_TAG "BalatroPortrait"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

using zygisk::Api;
using zygisk::AppSpecializeArgs;

static JavaVM *g_vm = nullptr;

// ---- luaL_loadbuffer hook ----
typedef int (*loadbuffer_t)(void *, const char *, size_t, const char *);
static loadbuffer_t orig_loadbuffer = nullptr;

static int my_loadbuffer(void *L, const char *buff, size_t sz, const char *name) {
  if (name && name[0] == '@') {
    const char *rel = name + 1;
    for (int i = 0; i < kAssetCount; i++) {
      if (strcmp(rel, kAssets[i].name) == 0) {
        return orig_loadbuffer(L, (const char *)kAssets[i].data, kAssets[i].len, name);
      }
    }
  }
  return orig_loadbuffer(L, buff, sz, name);
}

// ---- Android_JNI_SetOrientation hook (force portrait) ----
typedef void (*setorient_t)(int, int, int, const char *);
static setorient_t orig_setorient = nullptr;
static jclass g_sdlactivity_cls = nullptr;  // global ref, cached
static jfieldID g_singleton_fid = nullptr;
static jmethodID g_setreqorient_mid = nullptr;

static void force_portrait_jni() {
  if (!g_vm) return;
  JNIEnv *env = nullptr;
  if (g_vm->GetEnv((void **)&env, JNI_VERSION_1_6) != JNI_OK || env == nullptr) return;

  if (g_sdlactivity_cls == nullptr) {
    jclass cls = env->FindClass("org/libsdl/app/SDLActivity");
    if (cls == nullptr) { if (env->ExceptionCheck()) env->ExceptionClear(); return; }
    g_sdlactivity_cls = (jclass)env->NewGlobalRef(cls);
    g_singleton_fid = env->GetStaticFieldID(cls, "mSingleton", "Lorg/libsdl/app/SDLActivity;");
    jclass actcls = env->FindClass("android/app/Activity");
    g_setreqorient_mid = env->GetMethodID(actcls, "setRequestedOrientation", "(I)V");
    env->DeleteLocalRef(actcls);
    env->DeleteLocalRef(cls);
    if (env->ExceptionCheck()) env->ExceptionClear();
    if (g_singleton_fid == nullptr || g_setreqorient_mid == nullptr) return;
    LOGI("cached SDLActivity refs");
  }

  jobject singleton = env->GetStaticObjectField(g_sdlactivity_cls, g_singleton_fid);
  if (singleton != nullptr) {
    env->CallVoidMethod(singleton, g_setreqorient_mid, 1);  // SCREEN_ORIENTATION_PORTRAIT
    if (env->ExceptionCheck()) env->ExceptionClear();
    env->DeleteLocalRef(singleton);
  }
}

static void my_setorient(int w, int h, int resizable, const char *hint) {
  (void)w;
  (void)h;
  (void)resizable;
  (void)hint;
  force_portrait_jni();
}

static void install_hooks() {
  shadowhook_init(SHADOWHOOK_MODE_UNIQUE, true);

  void *s1 = shadowhook_hook_sym_name("liblove.so", "luaL_loadbuffer",
                                      (void *)my_loadbuffer, (void **)&orig_loadbuffer);
  LOGI("hook luaL_loadbuffer stub=%p errno=%d", s1, shadowhook_get_errno());

  void *s2 = shadowhook_hook_sym_name("liblove.so", "Android_JNI_SetOrientation",
                                      (void *)my_setorient, (void **)&orig_setorient);
  LOGI("hook Android_JNI_SetOrientation stub=%p errno=%d", s2, shadowhook_get_errno());
}

class BalatroPortrait : public zygisk::ModuleBase {
public:
  void onLoad(Api *api, JNIEnv *env) override {
    api_ = api;
    env_ = env;
    env->GetJavaVM(&g_vm);
  }

  void preAppSpecialize(AppSpecializeArgs *args) override {
    is_target_ = false;
    if (args->nice_name != nullptr) {
      const char *nm = env_->GetStringUTFChars(args->nice_name, nullptr);
      if (nm != nullptr) {
        is_target_ = (strcmp(nm, TARGET_PKG) == 0);
        env_->ReleaseStringUTFChars(args->nice_name, nm);
      }
    }
    if (!is_target_) {
      // not our target: let Zygisk unload us to save memory (no hooks installed)
      api_->setOption(zygisk::Option::DLCLOSE_MODULE_LIBRARY);
      return;
    }

    // We are in Balatro and still in the zygote context (can read /data/adb and
    // the module dir). Resolve the absolute path to libshadowhook_nothing.so and
    // install the hooks NOW, so shadowhook's linker-init memory scan can dlopen
    // nothing.so before the app sandbox / SuSFS hides the module overlay.
    int dirfd = api_->getModuleDir();
    if (dirfd >= 0) {
      char link[64];
      snprintf(link, sizeof link, "/proc/self/fd/%d", dirfd);
      char dir[400];
      ssize_t n = readlink(link, dir, sizeof dir - 1);
      if (n > 0) {
        dir[n] = '\0';
        snprintf(sh_linker_nothing_override_path, sizeof sh_linker_nothing_override_path,
                 "%s/system/lib64/libshadowhook_nothing.so", dir);
        LOGI("module dir = %s", dir);
      } else {
        LOGE("readlink module dir failed");
      }
    } else {
      LOGE("getModuleDir failed");
    }

    LOGI("installing hooks in preApp (assets=%d)", kAssetCount);
    install_hooks();
  }

  void postAppSpecialize(const AppSpecializeArgs *) override {
    if (is_target_) LOGI("postAppSpecialize done (hooks were installed in preApp)");
  }

private:
  Api *api_ = nullptr;
  JNIEnv *env_ = nullptr;
  bool is_target_ = false;
};

REGISTER_ZYGISK_MODULE(BalatroPortrait)
