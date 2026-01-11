# Balatro Portrait Mobile

🎴 A portrait mode mod for Balatro on Android - optimized for mobile gaming!
<img width="587" height="1290" alt="image" src="https://github.com/user-attachments/assets/1e509b4e-fe9d-4619-9b68-e223310f34d2" />

## Features

- **Portrait Mode**: Fully optimized vertical layout for mobile devices
- **Redesigned HUD**: Score, buttons, and info panels repositioned for portrait
- **Touch-Optimized**: Works perfectly with touchscreen controls
- **Full Game Support**: All features work in portrait mode

## Screenshots

*(Coming soon)*

## Requirements

- **Balatro** - You must own a legal copy of the game
- **Python 3.6+** - For build scripts
- **Java (JDK 8+)** - Automatically downloaded during build
- **Android device** - Android 5.0+ recommended

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
```

### Step 2: Get Original Game Files

⚠️ **You must own a legal copy of Balatro!**

1. Purchase Balatro from [Steam](https://store.steampowered.com/app/2379780/Balatro/)
2. Extract the game files:
   - **Steam**: Right-click Balatro → Manage → Browse Local Files
   - Extract `Balatro.exe` using 7-Zip or WinRAR
3. Copy the extracted folders to `game_original_files/`:
   ```
   game_original_files/
   ├── resources/
   │   ├── textures/
   │   ├── sounds/
   │   └── ...
   ├── localization/
   └── version.jkr
   ```

### Step 3: Prepare Source Files

Copy the required files from `game_original_files/` to `src/`:

```bash
cp -r game_original_files/resources src/
cp -r game_original_files/localization src/
cp game_original_files/version.jkr src/
```

### Step 4: Build the APK

```bash
# Step 1: Create Game.love (combines all game files)
python3 rebuild_game.py

# Step 2: Build the APK
python3 build_apk.py
```

The final APK will be at:
```
balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

### Step 5: Install on Android

```bash
# If you have ADB installed:
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk

# Or simply transfer the APK to your phone and install it
```

## Build Scripts

| Script | Description |
|--------|-------------|
| `rebuild_game.py` | Packages source files into Game.love |
| `build_apk.py` | Creates signed Android APK |

## Project Structure

```
balatro-portrait-mobile/
├── src/                    # Modified source files (portrait mode patches)
│   ├── main.lua           # Entry point with portrait resize handling
│   ├── game.lua           # Core game with portrait HUD positioning
│   ├── functions/         # UI and gameplay functions
│   └── engine/            # LÖVE engine utilities
├── game_original_files/   # ⚠️ PUT YOUR GAME FILES HERE
├── balatro-mobile-maker/  # APK building tools
├── rebuild_game.py        # Game.love builder
└── build_apk.py          # APK builder
```

## Troubleshooting

### "Game won't start"
- Make sure you copied ALL files from `game_original_files/` to `src/`
- Check that `src/resources/` and `src/localization/` exist

### "Build fails"
- Ensure Python 3.6+ is installed: `python3 --version`
- Try running with verbose output: `python3 build_apk.py`

### "Touch not working"
- The mod should handle touch automatically
- If issues persist, try clearing app data and reinstalling

## Credits

- **LocalThunk** - Original Balatro game
- **LÖVE** - 2D game framework
- **Contributors** - Portrait mode modifications

## Disclaimer

This is an unofficial mod. You must own a legal copy of Balatro to use this.
The original game files are NOT included in this repository.

## License

This mod is provided as-is for personal use. All rights to Balatro belong to LocalThunk.
