
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

## Which Version Should I Use?

If you are not sure, use the rootless APK builder. It is the normal route and
does not need root. The Zygisk module is there for rooted users who want to keep
the official Play Store app installed.

| Path | Best for | Root | What you install |
|------|----------|------|------------------|
| **Rootless APK builder** | Most users | No | A separate `com.unofficial.balatro` portrait APK |
| **Termux phone build** | Users with no PC | No | The same rootless APK, built directly on Android |
| **Zygisk module** | Rooted users keeping the official Play app | Yes | `balatro_portrait.zip` from Releases |
| **iOS build** | Testers only | No jailbreak required | Experimental sideloadable `.ipa` |

I cannot upload ready-made rootless APKs here because those builds contain your
own Balatro files. The Zygisk ZIP is different: it only contains the portrait
runtime module, so it can live on the Releases page.

## What You Need

- A legal copy of Balatro
- Android 5.0+ for the rootless APK builder
- Python 3.6+ for PC builds
- Termux from F-Droid or GitHub for phone-only builds
- Root + Zygisk only if you choose the experimental Zygisk module

## Rootless APK Builder

Build a separate portrait APK on Windows, macOS, or Linux:

```sh
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
python build.py
```

On first run, the script asks where your Balatro install is and extracts the
files it needs. The APK ends up here:

```text
balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

Install it on your Android device:

```sh
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

Some useful command-line examples:

```sh
python build.py --no-crt --readabletro
python build.py --balatro "D:\Steam\steamapps\common\Balatro\Balatro.exe" --force
python build.py --balatro "~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app" --force
```

Android APK builds always include Lovely. You do not need to enable it manually.

## Phone Build (Termux, No PC)

If the official Play Store Balatro is already installed on your phone, Termux can
build the portrait APK from that install. No PC copy of `Balatro.exe` or
`Game.love` is needed.

1. Install the official Play Store Balatro and launch it once.
2. Install Termux from F-Droid or GitHub.
3. In Termux, run:

```sh
termux-setup-storage
```

Tap **Allow**, then paste:

```sh
pkg update -y && pkg install -y git && rm -rf balatro-portrait-mobile && git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git && cd balatro-portrait-mobile && bash termux-build.sh --force
```

The helper installs missing Python/Java packages, asks about Readabletro and CRT,
then builds and signs the APK. When it is done, the file is copied to:

```text
/sdcard/Download/balatro-portrait-mobile.apk
```

Full guide: [docs/TERMUX.md](docs/TERMUX.md).

## Zygisk Module (Experimental, Root Only)

This keeps the official Google Play app installed and injects portrait mode when
the game starts. It does not patch or re-sign the APK, but it requires root +
Zygisk and is currently arm64-only.

1. Install the official Play Store Balatro and launch it once.
2. Download `balatro_portrait.zip` from GitHub Releases.
3. Install the ZIP from KernelSU, Magisk, or APatch.
4. Choose Readabletro/CRT options during install.
5. Reboot and launch the official Balatro app.

More details: [zygisk/README.md](zygisk/README.md).

## iOS

Build with `--ios`, then sideload `balatro-portrait.ipa` with
[Sideloadly](https://sideloadly.io/) or [AltStore](https://altstore.io/).
Full guide: [docs/IOS.md](docs/IOS.md). This path still needs testers.

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
