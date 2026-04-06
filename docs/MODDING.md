# Mod Support (Lovely)

Balatro Portrait Mobile supports the [Lovely](https://github.com/ethangreen-dev/lovely-injector) runtime Lua injector for loading mods (such as [Steamodded](https://github.com/Steamodded/smods)) on Android.

> **Root Required**: Installing mods requires a **rooted Android device** (e.g. via [Magisk](https://github.com/topjohnwu/Magisk)). The mod directory is located at `/data/user/0/`, which is only accessible with root privileges.

## Building with Lovely

When running `build_apk.py`, select **yes** when asked about Lovely mod support:

```
Enable Lovely mod support? (y/n): y
```

Or use the CLI flag:

```
python build_apk.py --with-lovely
```

This builds the APK using [Lovely Mobile Maker](https://github.com/WilsontheWolf/lovely-mobile-maker)'s base, which has `liblovely.so` embedded.

## Installing Mods

### Requirements

- [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files) (free on Play Store)
- A Lovely-enabled Balatro APK (built with `--with-lovely`)

### Steps

1. **Install and launch the game once** — this creates the required folder structure
2. **Open Material Files**
3. **Navigate to the mod directory:**

```
/ > data > user > 0 > com.unofficial.balatro > files > save > ASET > Mods
```

> This path is in the **root directory** (`/`), NOT in `Android/data/`. You must navigate from the root `/` of the filesystem in Material Files.

4. **Copy your mod folders** into the `Mods` directory
5. **Restart Balatro**

### Full Path

```
/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/
```

### Mod Folder Structure Example

```
Mods/
├── Steamodded/
│   ├── core/
│   ├── lovely.toml
│   └── ...
├── YourMod/
│   └── YourMod.lua
└── lovely/
    └── log/        ← created automatically by Lovely
```

## Troubleshooting

### "Can't find /data/user/0/ in Material Files"

Material Files needs root-level filesystem access. When browsing:
- Tap the path bar at the top
- Type `/` and press Enter
- Navigate through `data > user > 0 > com.unofficial.balatro`

### "Mods folder doesn't exist"

Launch the game at least once after installing the APK. Lovely creates the `ASET/Mods/` directory on first run.

### "Game crashes after adding mods"

- Not all PC mods are compatible with Android
- Shader-dependent mods may crash — remove the `resources/shaders/` folder from the mod if present
- Check `ASET/Mods/lovely/log/` for error logs

### "Mod doesn't load / game runs vanilla"

- Ensure the mod folder is inside `ASET/Mods/`, not nested deeper
- Ensure you built with `--with-lovely` (vanilla builds don't have Lovely)

## Using ADB (Alternative)

If you have ADB set up, you can push mods directly:

```bash
adb push MyMod /data/local/tmp/MyMod
adb shell run-as com.unofficial.balatro cp -r /data/local/tmp/MyMod files/save/ASET/Mods/
```

## Notes

- Lovely is embedded in the APK at build time via [LMM](https://github.com/WilsontheWolf/lovely-mobile-maker)
- The Lovely version depends on what LMM provides in its base APK
- Not all PC mods are compatible with Android — see the mod's documentation for platform support
