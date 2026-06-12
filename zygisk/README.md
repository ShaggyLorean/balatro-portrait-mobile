# Balatro Portrait Zygisk Module

Experimental root-only runtime module for the official Google Play Balatro.

This path does not patch or re-sign the APK. The official app stays installed
with its Play signature, and the module injects the portrait Lua/shader payload
when `com.playstack.balatro.android` starts.

## Status

- arm64-v8a only
- Requires root with Zygisk support: KernelSU + ReZygisk, Magisk + Zygisk, or APatch + Zygisk
- Targets the official Play package: `com.playstack.balatro.android`
- Does not redistribute Balatro game assets
- Experimental: Play updates may change `liblove.so`/SDL symbols and break hooks

## Build

Requirements:

- Python 3
- CMake + Ninja
- Android NDK r27c
- Git

```powershell
cd zygisk
$env:ANDROID_NDK_HOME = "C:\path\to\android-ndk-r27c"
.\build_pkg.ps1
```

The script fetches the pinned dependencies into `zygisk/deps/`, applies the
local shadowhook patch, builds all install variants, and writes:

```text
zygisk/dist/balatro_portrait.zip
```

## Install

1. Install the official Google Play Balatro and launch it once.
2. Download `balatro_portrait.zip` from GitHub Releases, or build it locally
   with the command above.
3. Install `balatro_portrait.zip` from your root manager.
4. During install, choose:
   - Readabletro on/off
   - CRT disable on/off
5. Reboot.
6. Launch the official Balatro app.

If your root manager does not provide Magisk's `chooseport` helper, the
installer falls back to reading volume keys directly with `getevent`. If both
methods are unavailable, it uses the default variant: Readabletro on, CRT
disable off.

## Release Artifact

The release ZIP is safe to publish because it does not include the game APK or
Balatro's packaged assets. It contains the native Zygisk module, hook support
library, portrait Lua/shader payload, and optional Readabletro resources.

## How It Works

- Hooks `luaL_loadbuffer` in `liblove.so` and swaps matching Lua chunks with
  embedded portrait sources.
- Hooks `Android_JNI_SetOrientation` and calls
  `SDLActivity.setRequestedOrientation(1)` without forwarding the original
  landscape request.
- Preloads `portrait_config`, portrait shaders, and optional Readabletro files
  from embedded Lua before the game loads.

## Why Not Rootless Runtime Injection?

Rootless Android cannot inject into another installed app process or replace
its in-memory Lua chunks without either modifying the APK on disk or using a
debuggable/instrumented target. Modifying the official paid APK requires
re-signing, and the Play build is protected by integrity checks. The rootless
path for normal users is therefore the APK builder in the repository root; this
Zygisk path is the power-user alternative for people who want to keep the
official Play install.
