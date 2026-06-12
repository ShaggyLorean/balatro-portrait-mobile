# Mod Support

Balatro Portrait Mobile now has two Android paths. They use different package
names, so their mod folders are different.

## Path A — Rootless APK Builder

This is the normal recommended path for most players.

- Package name: `com.unofficial.balatro`
- Mod runtime: Lovely is always embedded in Android builds
- Root: not required
- Mod folder inside the app storage: `ASET/Mods/`
- Direct root path:

```text
/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/
```

### Install Mods Without Root

1. Build and install the APK from `python build.py`.
2. Launch the game once so Lovely creates the folder structure.
3. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files).
4. Open Material Files → menu → **Add storage...** → **External storage**.
5. In the Android picker menu, choose the **Balatro** app and tap **Use this folder**.
6. Open `ASET/Mods/`.
7. Copy mod folders there.
8. Restart Balatro.

This Material Files flow comes from Lovely Mobile Maker's FAQ and avoids root.

### Install Mods With Root

Open a root file manager and copy mod folders to:

```text
/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/
```

### Install Mods With ADB

```bash
adb push MyMod /data/local/tmp/MyMod
adb shell run-as com.unofficial.balatro cp -r /data/local/tmp/MyMod files/save/ASET/Mods/
```

## Path B — Experimental Zygisk Module

This is the root-only power-user path for the official Google Play app.

- Package name: `com.playstack.balatro.android`
- Root: required
- Zygisk: required
- APK patching/re-signing: not used
- Current scope: portrait runtime injection, orientation lock, shader/resource payload
- Modding parity: not complete yet; Lovely is not embedded in the official APK

The official app's matching save/mod folder is:

```text
/data/user/0/com.playstack.balatro.android/files/save/ASET/Mods/
```

That path is useful for future Zygisk mod-loader work, but the current Zygisk
module should not be advertised as a full Lovely/Steamodded replacement until a
runtime mod loader is implemented and tested.

## Mod Folder Structure

```text
Mods/
├── Steamodded/
│   ├── core/
│   ├── lovely.toml
│   └── ...
├── YourMod/
│   └── YourMod.lua
└── lovely/
    └── log/
```

## Troubleshooting

### "I can't see the Balatro app in Add storage → External storage"

- Launch the game at least once first.
- The app list is inside the Android document picker's menu, not Material Files'
  sidebar.
- Make sure you are picking the correct app:
  - Rootless builder: `com.unofficial.balatro`
  - Zygisk official app: `com.playstack.balatro.android`

### "Mods folder doesn't exist"

Launch the game at least once after installing the APK. Lovely creates
`ASET/Mods/` on first run for the rootless builder path.

### "Game crashes after adding mods"

- Not all PC mods are compatible with Android.
- Shader-dependent mods may crash; remove the mod's `resources/shaders/` folder
  if the mod bundles desktop shaders.
- Check `ASET/Mods/lovely/log/` for Lovely logs.

### "Mod doesn't load / game runs vanilla"

- Make sure the mod folder is directly inside `ASET/Mods/`, not nested one level
  deeper.
- Make sure you are using the rootless APK builder path. The Zygisk module does
  not yet provide full Lovely mod loading for the official Play package.

## Notes

- Android builds from `build.py` always use the Lovely base APK now.
- iOS builds remain vanilla; Lovely is Android-only.
- The Zygisk path keeps the official Play install intact and is intentionally
  documented separately from the rootless Lovely APK path.
