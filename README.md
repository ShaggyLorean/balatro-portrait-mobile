# Balatro Portrait Mobile

A portrait mode mod for Balatro on Android - optimized for mobile gaming.

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/98c0f4eb-68d6-43c4-9f8d-1908eea24711" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/1250c840-783b-41b7-9ff8-ed80e9771038" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/b9e61dbd-6ab2-490e-8804-cf91597aaa53" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/9ba49f0a-4e8b-4937-a095-ff21b31bab56" />


## Features

- **Portrait Mode**: Fully optimized vertical layout for mobile devices
- **Redesigned HUD**: Score, buttons, and info panels repositioned for portrait
- **Touch-Optimized**: Works perfectly with touchscreen controls
- **Full Game Support**: All features work in portrait mode
- **Mod Support (Lovely)**: Optional [Lovely](https://github.com/ethangreen-dev/lovely-injector) integration for loading mods on Android

## Requirements

- **Balatro** - You must own a legal copy of the game
- **Python 3.6+** - For build scripts
- **Android device** - Android 5.0+ recommended

> **Cross-Platform:** Works on Windows, MacOS and Linux.

## Quick Start

### Step 1: Clone the Repository

```
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
```

### Step 2: Get Balatro

**You must own a legal copy of Balatro.**

1. Purchase from [Steam](https://store.steampowered.com/app/2379780/Balatro/)
2. Find your Balatro.exe location:
   - **Steam**: Right-click Balatro → Manage → Browse Local Files
   - Default: `C:\Program Files\Steam\steamapps\common\Balatro\Balatro.exe`

### Step 3: Run the Auto Builder

```
python build.py
```

The unified `build.py` script will automatically handle the entire process. If this is your first time, it will:
1. **Ask for your Balatro.exe path** and automatically extract all necessary game files.
2. **Present Optional Patches**:

1. **CRT Shader Patch:**
   - If you see a **black ellipse** covering part of the screen, enable this to disable CRT.
   - If your game works fine, skip this to keep the CRT visual effects.

2. **Readabletro Typography & Textures:**
   - Enable to apply the [Readabletro](https://github.com/bladeSk/readabletro) mod.
   - Replaces the pixel font with a smoother typography (TypoQuik-Bold).
   - Resolves texture bugs and replaces card/UI textures with high-resolution, anti-aliased variants.

3. **Lovely Mod Support:**
   - Enable to embed the [Lovely](https://github.com/ethangreen-dev/lovely-injector) mod framework.
   - You can also run the build silently with flags: `python build.py --crt --readabletro --with-lovely`

*(Your configuration will be saved in `.buildconfig.json` for rapid, single-click rebuilds later)*

### Step 4: Install on Android

Transfer the generated APK to your phone and install it.

Or natively deploy via ADB if your device is plugged in:

```
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

## Project Structure

```
balatro-portrait-mobile/
├── src/                    # Modified source files (portrait mode)
├── game_original_files/    # Extracted game files (created by setup.py)
├── docs/
│   └── MODDING.md          # Mod installation guide
├── setup.py                # Setup script (extracts & copies files)
├── rebuild_game.py         # Creates Game.love
└── build_apk.py            # Builds the APK (with optional Lovely support)
```

## Mod Support (Lovely)

Balatro Portrait Mobile supports the [Lovely](https://github.com/ethangreen-dev/lovely-injector) mod framework for loading mods on Android.

> **Root Required**: Installing mods requires a **rooted Android device** (e.g. via [Magisk](https://github.com/topjohnwu/Magisk)). The mod directory is located in the root filesystem (`/data/user/0/`), which is not accessible without root.

Build with `--with-lovely` (or answer "yes" during the build prompt) to embed the Lovely runtime. After installation:

1. Launch the game once to create the folder structure
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files)
3. Navigate to: `/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/`
4. Place your mod folders there and restart the game

See [docs/MODDING.md](docs/MODDING.md) for detailed instructions and troubleshooting.

## Troubleshooting

### "Game won't start"

- Make sure setup.py completed successfully
- Check that `src/resources/` and `src/localization/` exist

### "Build fails"

- Ensure Python 3.6+ is installed: `python --version`
- JDK is downloaded automatically during build

### "Black ellipse covering part of the screen"

This is caused by the CRT shader not rendering correctly in portrait mode on some devices.

**Solution**: Rebuild with CRT patch enabled:

```
python rebuild_game.py
```

When asked "Apply CRT disable patch?", answer **yes**.

## Credits

- **LocalThunk** - Original Balatro game
- **LÖVE** - 2D game framework
- **Contributors** - Portrait mode modifications
- **KtourzaJeremy** - Some huge pull requests
- **[ethangreen-dev](https://github.com/ethangreen-dev)** - Lovely injector
- **[WilsontheWolf](https://github.com/WilsontheWolf)** - Lovely Mobile Maker & lmm-love-android
- **[bladeSk](https://github.com/bladeSk)** - Readabletro mod (fonts, shaders, textures)

## Disclaimer

This is an unofficial mod. You must own a legal copy of Balatro to use this.
The original game files are NOT included in this repository.

## License

This mod is provided as-is for personal use. All rights to Balatro belong to LocalThunk.
