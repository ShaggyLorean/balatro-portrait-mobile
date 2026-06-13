
# Balatro Portrait Mobile

[![CI](https://github.com/ShaggyLorean/balatro-portrait-mobile/actions/workflows/ci.yml/badge.svg)](https://github.com/ShaggyLorean/balatro-portrait-mobile/actions/workflows/ci.yml)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20the%20mod-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/loreanxavier)

A portrait-mode mod for Balatro on Android, built for one-handed mobile play.

> ☕ Enjoying the mod? You can [**support it on Ko-fi**](https://ko-fi.com/loreanxavier). It really helps me keep this going.

## Demo

<p align="center">
  <img src="https://github.com/user-attachments/assets/7edcadc5-a828-4b6e-acf7-c3f684995f45" width="320" alt="demo"/>
</p>

## Screenshots

<table align="center">
<tr>
  <td><img src="https://github.com/user-attachments/assets/14852345-7ef5-4ec6-a6e7-c1cf6f2e0b89" width="280"/></td>
  <td><img src="https://github.com/user-attachments/assets/217ba77c-806a-4d97-8b2e-7190d2fd60cc" width="280"/></td>
  <td><img src="https://github.com/user-attachments/assets/6de70f06-d749-456f-8d96-f9f3d56a28ef" width="280"/></td>
</tr>
<tr>
  <td><img src="https://github.com/user-attachments/assets/b7449786-0ac3-4401-b2ba-021f16473862" width="280"/></td>
  <td><img src="https://github.com/user-attachments/assets/0b09babe-76d0-4fca-9c7f-331042da5b3a" width="280"/></td>
  <td><img src="https://github.com/user-attachments/assets/23f5d4e5-dd41-4594-a82e-27a9e343a50f" width="280"/></td>
</tr>
</table>

## Features

- **Portrait mode** with a vertical layout rebuilt for one-handed play
- **Touch controls** with anti-jitter, so a shaky tap doesn't turn into a drag
- **Swipe gestures**: flick a selected card up to play it, down to discard
- **Hand preview** — a floating chip above your cards shows the current poker hand (name, level, chips × mult)
- **Redesigned HUD**: score, buttons and panels moved around for portrait, with thumb-sized targets
- **High refresh rate**, matched to your display (90/120 Hz) automatically
- Everything else in Balatro works the way it normally does
- **Mod support** through [Lovely](https://github.com/ethangreen-dev/lovely-injector) (bundled in Android builds)
- **PC-free Termux builds** can use the installed official Play Store app as the resource source
- **Zygisk module** (experimental): a root-only runtime path for the official Google Play install
- **iOS** (experimental): build a sideloadable `.ipa` with `--ios` (see the [guide](docs/IOS.md))

## Requirements

- **Balatro** — You must own a legal copy of the game
- **Python 3.6+** — For the build script
- **Android device** — Android 5.0+ recommended
- **iOS device** — Experimental; sideload via Sideloadly/AltStore, see [docs/IOS.md](docs/IOS.md)

> **Cross-platform:** Builds on Windows, macOS, Linux, and even directly on your
> Android phone via [Termux](https://termux.dev) (no PC needed, see below).

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

The script handles everything. On first run it asks for your Balatro game file path and extracts the needed files automatically.

**Build options (asked once, saved for future runs):**

| Option | Default | Description |
|--------|---------|-------------|
| CRT patch | off | Applies the CRT-disabling portrait patch. The default 2.0 build keeps this off. |
| Readabletro | on | Applies the [Readabletro](https://github.com/bladeSk/readabletro) mod: TypoQuik-Bold font, high-res card and UI textures. |
| iOS build | off | **Experimental.** Also produces `balatro-portrait.ipa` for sideloading with Sideloadly/AltStore. See [docs/IOS.md](docs/IOS.md). |

Android APK builds always include Lovely now, so mod support is not a separate
question.

You can also pass flags to skip the prompts:

```
python build.py --no-crt --readabletro
python build.py --balatro "D:\Steam\steamapps\common\Balatro\Balatro.exe" --force
python build.py --balatro "~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app" --force
```

Run `python build.py --help` or check the top of `build.py` for all available flags.

### 3. Install on your device

**Android** — transfer the APK to your phone and install it, or deploy directly via ADB:

```
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

**iOS (experimental)** — build with `--ios`, then sideload `balatro-portrait.ipa`
with [Sideloadly](https://sideloadly.io/) or [AltStore](https://altstore.io/).
Full guide: [docs/IOS.md](docs/IOS.md). Untested by the maintainer — testers welcome!

### Building on Android itself (Termux, no PC)

You can build the APK directly on your phone with [Termux](https://termux.dev).
If the official Play Store Balatro is installed, the build script can use that
installed app as the resource source. No PC copy of `Balatro.exe` or `Game.love`
is needed.

First give Termux storage access:

```sh
termux-setup-storage
```

Tap **Allow** when Android asks. Then paste this:

```sh
pkg update -y && pkg install -y git && rm -rf balatro-portrait-mobile && git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git && cd balatro-portrait-mobile && bash termux-build.sh --force
```

`termux-build.sh` installs Python/Java if they are missing, then runs the normal
builder. During resource setup, `build.py` calls Android's system package manager
directly (`/system/bin/pm`) and reads the official app's `base.apk`; this does
not require root.

The finished APK is copied to:

```text
/sdcard/Download/balatro-portrait-mobile.apk
```

Full phone-only guide: [docs/TERMUX.md](docs/TERMUX.md).

If you want to build from a PC/Steam copy instead, that still works:

```
python build.py --balatro ~/Balatro.exe
```

The apktool jar bundles an x86-64 `aapt2` that can't run on Android. On Termux
the script handles this for you: it downloads a native ARM `aapt2` from
[ReVanced/aapt2](https://github.com/ReVanced/aapt2) and points apktool at it, so
no manual apktool install is needed. If you'd rather use a native apktool that's
already in your `PATH` (for example [rendiix/termux-apktool](https://github.com/rendiix/termux-apktool)),
the script detects it and uses it as-is.

Termux also signs the APK with Android's native `apksigner`. Install the produced
APK with your file manager (enable "install unknown apps").

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
│   ├── MODDING.md              # Mod installation guide (Android, Lovely)
│   ├── IOS.md                  # Experimental iOS build & sideloading guide
│   └── TERMUX.md               # Phone-only Android build guide
├── zygisk/                     # Experimental root-only Zygisk module source
├── termux-build.sh             # Android/Termux helper for PC-free builds
└── build.py                    # Unified build script (setup + Game.love + APK/IPA)
```

> `src/resources/`, `src/localization/`, and `game_original_files/` are generated
> locally from your Balatro copy and are not included in this repository.

## Install Paths

### Option A — Rootless APK Builder

This is the recommended path for most users. It builds a separate
`com.unofficial.balatro` APK with portrait mode and Lovely mod support already
included.

```bash
python build.py
```

### Option B — Experimental Zygisk Module

This is a root-only power-user path for people who want to keep the official
Google Play package (`com.playstack.balatro.android`) installed and inject
portrait mode at runtime. It requires root + Zygisk and is currently arm64-only.

Download `balatro_portrait.zip` from the GitHub Releases page, install it from
KernelSU, Magisk, or APatch, choose Readabletro/CRT options during install,
reboot, and launch the official Play Store Balatro.

To build the module locally instead:

```powershell
cd zygisk
$env:ANDROID_NDK_HOME = "C:\path\to\android-ndk-r27c"
.\build_pkg.ps1
```

The local build writes `zygisk/dist/balatro_portrait.zip`. See
[zygisk/README.md](zygisk/README.md).

The Zygisk path is experimental by design: it does not patch or re-sign the APK,
but official game updates can still break native symbol hooks.

## Mod Support (Lovely)

Android APK builds include Lovely automatically. After installation:

1. Launch the game once to create the folder structure
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files)
3. **No root needed:** in Material Files open the menu (top left) → *Add storage…*
   → *External storage* → pick the Balatro app → *Use this folder*. The app's
   storage appears in the sidebar — put your mod folders in `ASET/Mods/`
4. Restart the game

Root or ADB also work as alternatives — see [docs/MODDING.md](docs/MODDING.md)
for rootless APK paths, official Play/Zygisk paths, and troubleshooting.

## Troubleshooting

### Game won't start

Make sure the first-run resource extraction completed successfully.
`src/resources/` and `src/localization/` must exist. Re-run `python build.py` if they're missing.

### Build fails

- Check Python version: `python --version` (3.6+ required)
- JDK is downloaded automatically, so no manual install is needed
- Internet connection required for first build (downloads ~250 MB of tools)
- On Termux, use native `java`, `apktool`, and `aapt2`; desktop jars/binaries
  are not enough on ARM64 Android

### Black ellipse or colored sliver at the bottom of the screen

The CRT shader can cause visual artifacts on some devices in portrait mode.

**Solution:** Rebuild with the CRT patch enabled:

```
python build.py --crt
```

Or answer **yes** to "Apply CRT patch?" during the interactive build.

### Prices look higher than expected

In-game price increases are **base Balatro mechanics**, not a bug in this mod. Common causes:
- **Overpriced voucher** — multiplies Tarot/Planet pack prices by 1.5×
- **Inflation joker** — adds $1 to all item prices each round

## Support

If this mod made mobile Balatro better for you, you can buy me a coffee. It
genuinely helps me keep this maintained.

<p align="center">
  <a href="https://ko-fi.com/loreanxavier">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support me on Ko-fi"/>
  </a>
</p>

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

The build tooling, documentation, and portrait-mode modifications in this
repository are released under the [MIT License](LICENSE). All rights to
Balatro — including any game code and assets this project derives from —
belong to LocalThunk / Playstack. See the scope note in [LICENSE](LICENSE).
