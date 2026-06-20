# Mod Support

Balatro Portrait Mobile has two Android paths. They use different package names,
so their mod folders are different.

## Path A: Rootless APK builder

The normal path for most players.

- Package name: `com.unofficial.balatro`
- Mod runtime: Lovely is always embedded in Android builds
- Root: not required
- Mod folder: `game/Mods/` inside the app storage
- Direct root path:

```text
/data/user/0/com.unofficial.balatro/files/save/game/Mods/
```

### Bundle Steamodded at build time (easiest)

Most mods need Steamodded, and the build can fetch and bundle it for you:

```sh
python build.py --steamodded          # newest Steamodded
python build.py --steamodded <tag>    # a specific release
```

It installs itself on the first launch. Restart the game once and Steamodded is
active.

### Install mods without root

1. Build and install the APK from `python build.py`.
2. Launch the game once so the folder structure is created.
3. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files).
4. Material Files menu -> **Add storage...** -> **External storage**.
5. In the Android picker, choose the **Balatro** app and tap **Use this folder**.
6. Open `game/Mods/`.
7. Copy mod folders there.
8. Restart Balatro.

This Material Files flow comes from Lovely Mobile Maker's FAQ and avoids root.

### Install mods with root

Copy mod folders to:

```text
/data/user/0/com.unofficial.balatro/files/save/game/Mods/
```

## Path B: Experimental Zygisk module

The root-only path for the official Google Play app.

- Package name: `com.playstack.balatro.android`
- Root and Zygisk: required
- APK patching/re-signing: not used
- Current scope: portrait injection, orientation lock, shader/resource payload
- Modding: Lovely is not embedded in the official APK, so this path does not run
  Steamodded mods yet

The official app's matching mod folder is:

```text
/data/user/0/com.playstack.balatro.android/files/save/ASET/Mods/
```

That path is for future Zygisk mod-loader work. Until a runtime mod loader is in
place, treat the Zygisk module as portrait-only, not a Lovely/Steamodded
replacement.

## Mod folder structure

```text
Mods/
├── Steamodded/
│   ├── src/
│   ├── lovely/
│   └── ...
├── YourMod/
│   └── YourMod.lua
└── lovely/
    └── log/
```

## Troubleshooting

**"I can't see the Balatro app in Add storage."** Launch the game at least once
first. The app list is inside the Android document picker's menu, not the
Material Files sidebar. Pick the right package: `com.unofficial.balatro` for the
rootless builder, `com.playstack.balatro.android` for the Zygisk app.

**"Mods folder doesn't exist."** Launch the game once after installing. The
rootless builder creates `game/Mods/` on the first run.

**"Game crashes after adding mods."** Not every PC mod works on Android.
Shader-heavy mods can crash; remove the mod's `resources/shaders/` folder if it
ships desktop shaders. Check `game/Mods/lovely/log/` for Lovely logs.

**"Mod doesn't load / game runs vanilla."** Make sure the mod folder is directly
inside `game/Mods/`, not nested one level deeper, and that you are on the
rootless builder path.

## Notes

- `build.py` always uses the Lovely base APK for Android.
- iOS builds are vanilla; Lovely is Android-only.
- The Zygisk path keeps the official install intact and is documented separately
  from the rootless Lovely APK path.
