# Mod Support (Lovely)

Balatro Portrait Mobile supports the [Lovely](https://github.com/ethangreen-dev/lovely-injector) runtime Lua injector for loading mods (such as [Steamodded](https://github.com/Steamodded/smods)) on Android.

> **No root required.** The recommended install method below uses Android's
> storage access framework via Material Files and works on stock, unrooted
> devices. Root (Magisk) and ADB remain available as alternatives.

## Building with Lovely

When running `build.py`, select **yes** when asked about Lovely mod support:

```
Enable Lovely mod support? (y/n): y
```

Or use the CLI flag:

```
python build.py --with-lovely
```

This builds the APK using [Lovely Mobile Maker](https://github.com/WilsontheWolf/lovely-mobile-maker)'s base, which has `liblovely.so` embedded.

## Installing Mods

### Requirements

- [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files) (free on Play Store)
- A Lovely-enabled Balatro APK (built with `--with-lovely`)

### Method 1 — No root (recommended)

1. **Install and launch the game once** — this creates the required folder structure
2. **Open Material Files**
3. Open the **menu** (hamburger icon, top left) → **Add storage…** → **External storage**
4. In the picker, open the menu again and choose the **Balatro** app, then tap
   **"Use this folder"** and allow access
5. The app's storage now appears in the Material Files sidebar — navigate to
   `ASET/Mods/`
6. **Copy your mod folders** into `Mods/`
7. **Restart Balatro**

> This method comes from Lovely Mobile Maker's FAQ.

### Method 2 — Root (Magisk)

With a rooted device you can browse to the directory directly. In Material
Files, tap the path bar, type `/` and navigate to:

```
/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/
```

> This path is in the **root directory** (`/`), NOT in `Android/data/`.

### Method 3 — ADB

If you have ADB set up, you can push mods directly:

```bash
adb push MyMod /data/local/tmp/MyMod
adb shell run-as com.unofficial.balatro cp -r /data/local/tmp/MyMod files/save/ASET/Mods/
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

### "I can't see the Balatro app in Add storage → External storage"

- Launch the game at least once first
- The picker's app list lives behind the **menu of the document picker** (top
  left in the file picker screen) — look for the app name there

### "Mods folder doesn't exist"

Launch the game at least once after installing the APK. Lovely creates the `ASET/Mods/` directory on first run.

### "Game crashes after adding mods"

- Not all PC mods are compatible with Android
- Shader-dependent mods may crash — remove the `resources/shaders/` folder from the mod if present
- Check `ASET/Mods/lovely/log/` for error logs

### "Mod doesn't load / game runs vanilla"

- Ensure the mod folder is inside `ASET/Mods/`, not nested deeper
- Ensure you built with `--with-lovely` (vanilla builds don't have Lovely)

## Notes

- Lovely is embedded in the APK at build time via [LMM](https://github.com/WilsontheWolf/lovely-mobile-maker)
- The Lovely version depends on what LMM provides in its base APK
- Not all PC mods are compatible with Android — see the mod's documentation for platform support
