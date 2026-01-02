# Balatro Portrait Mobile Mod
A layout modification for Balatro Mobile that enables a native Portrait (Vertical) experience.

## Features
* **Left Stack Layout:** Deck, Consumables, and Discard are stacked vertically on the left column to prevent overlapping.
* **Shop Sign Clearance:** The layout starts lower to ensure no UI elements block the Shop sign.
* **HUD Redesign:** Sidebar-based HUD optimized for vertical screens.
* **Native Orientation:** Logic to handle portrait rendering natively.

## How to Install
This repository only contains the modification files. You must own a legal copy of Balatro to use this.

### Prerequisites
* A copy of `Balatro.apk` (or the game header files).
* APKTool or similar decompilation tools.

### Steps
1. Decompile your `Balatro.apk`.
2. Navigate to the `assets/game` directory inside the decompiled folder.
3. Download the `src` folder from this repository.
4. Copy the contents of `src` and paste them into your game folder, overwriting the existing files:
   * `src/main.lua` -> `game/main.lua`
   * `src/conf.lua` -> `game/conf.lua`
   * `src/functions/*` -> `game/functions/*`
5. If you are building from scratch, apply the Smali patch found in `src/smali`.
6. Recompile and Sign the APK.
7. Install and play.

## Credits
* **Balatro Mobile Maker:** Base tools and build scripts.
* **LocalThunk:** Original Developer of Balatro.
