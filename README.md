# Balatro Portrait Mobile

A portrait mode mod for Balatro on Android — optimized for mobile gaming.

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/98c0f4eb-68d6-43c4-9f8d-1908eea24711" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/1250c840-783b-41b7-9ff8-ed80e9771038" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/b9e61dbd-6ab2-490e-8804-cf91597aaa53" />

<img width="1080" height="2376" alt="image" src="https://github.com/user-attachments/assets/9ba49f0a-4e8b-4937-a095-ff21b31bab56" />


## Features

- **Portrait Mode** — Fully optimized vertical layout for mobile
- **Touch Controls** — Responsive touchscreen support with anti-jitter
- **Redesigned HUD** — Score, buttons, and panels repositioned for portrait
- **Full Game Support** — All Balatro features work in portrait mode
- **Mod Support** — Optional [Lovely](https://github.com/ethangreen-dev/lovely-injector) integration for loading mods on Android

## Requirements

- **Balatro** — You must own a legal copy of the game
- **Python 3.6+** — For the build script
- **Android device** — Android 5.0+ recommended

> **Cross-platform:** Builds on Windows, macOS, and Linux.

## Quick Start

### 1. Clone the repository

```
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
```

### 2. Run the build script

```
python build.py
```

The script handles everything — on first run it will ask for your Balatro.exe path and extract the necessary game files automatically.

**Build options (asked once, saved for future runs):**

| Option | Default | Description |
|--------|---------|-------------|
| CRT patch | off | Disables the CRT shader for desktop portrait testing. Android always disables CRT automatically — skip this unless you test on PC. |
| Readabletro | off | Applies the [Readabletro](https://github.com/bladeSk/readabletro) mod: TypoQuik-Bold font, high-res card and UI textures. |
| Lovely mod support | on | Embeds the [Lovely](https://github.com/ethangreen-dev/lovely-injector) runtime so mods can be loaded. Requires a rooted device. |

You can also pass flags to skip the prompts:

```
python build.py --no-crt --no-readabletro --with-lovely
python build.py --balatro "D:\Steam\steamapps\common\Balatro\Balatro.exe" --force
```

Run `python build.py --help` or check the top of `build.py` for all available flags.

### 3. Install on your device

Transfer the APK to your phone and install it, or deploy directly via ADB:

```
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

## Project Structure

```
balatro-portrait-mobile/
├── src/                        # Modified Lua source files (portrait mode)
│   ├── portrait_config.lua     # Centralized scaling and layout config
│   ├── game.lua                # Core game logic (portrait adaptations)
│   ├── globals.lua             # Feature flags, Android-specific settings
│   ├── main.lua                # Entry point, input handling, canvas setup
│   └── ...
├── patches/
│   └── readabletro/            # Optional Readabletro font and texture patch
├── docs/
│   └── MODDING.md              # Mod installation guide
└── build.py                    # Unified build script (setup + Game.love + APK)
```

> `src/resources/`, `src/localization/`, and `game_original_files/` are generated
> locally from your Balatro copy and are not included in this repository.

## Mod Support (Lovely)

Build with Lovely enabled (default) to embed the mod runtime. After installation:

1. Launch the game once to create the folder structure
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files)
3. Navigate to: `/data/user/0/com.unofficial.balatro/files/save/ASET/Mods/`
4. Place your mod folders there and restart the game

> **Root required** — mod directories are inside `/data/`, which needs root access (e.g. [Magisk](https://github.com/topjohnwu/Magisk)).

See [docs/MODDING.md](docs/MODDING.md) for detailed instructions.

## Troubleshooting

### Game won't start

Make sure the first-run resource extraction completed successfully.
`src/resources/` and `src/localization/` must exist. Re-run `python build.py` if they're missing.

### Build fails

- Check Python version: `python --version` (3.6+ required)
- JDK is downloaded automatically — no manual install needed
- Internet connection required for first build (downloads ~250 MB of tools)

### Display looks cut off or shows a colored sliver at the bottom

This was caused by the CRT shader not handling portrait mode correctly on tall devices (e.g. Samsung Galaxy S23+).

**Fixed in v1.9.6:** Android now automatically disables the CRT shader. No manual action needed — just rebuild.

### Prices look higher than expected

In-game price increases are **base Balatro mechanics**, not a bug in this mod. Common causes:
- **Overpriced voucher** — multiplies Tarot/Planet pack prices by 1.5×
- **Inflation joker** — adds $1 to all item prices each round

## Credits

- **LocalThunk** — Original Balatro game
- **LÖVE** — 2D game framework
- **KtourzaJeremy** — Pull requests
- **[ethangreen-dev](https://github.com/ethangreen-dev)** — Lovely injector
- **[WilsontheWolf](https://github.com/WilsontheWolf)** — Lovely Mobile Maker
- **[bladeSk](https://github.com/bladeSk)** — Readabletro mod (fonts, shaders, textures)
- **[blake502](https://github.com/blake502)** — Balatro APK Maker (APK patch tools)

## Disclaimer

This is an unofficial mod. You must own a legal copy of Balatro to use this.
Original game files are **not** included in this repository.

## License

Provided as-is for personal use. All rights to Balatro belong to LocalThunk.
