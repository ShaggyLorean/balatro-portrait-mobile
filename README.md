# Balatro Portrait Mobile

[![CI](https://github.com/ShaggyLorean/balatro-portrait-mobile/actions/workflows/ci.yml/badge.svg)](https://github.com/ShaggyLorean/balatro-portrait-mobile/actions/workflows/ci.yml)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20the%20mod-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/loreanxavier)

A portrait-mode mod for Balatro on Android, built for one-handed play.

> ☕ Enjoying the mod? You can [support it on Ko-fi](https://ko-fi.com/loreanxavier).

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
- **Touch controls** with anti-jitter, so a shaky tap does not turn into a drag
- **Swipe gestures**: flick a selected card up to play it, down to discard
- **Hand preview**: a floating chip shows the current poker hand (name, level, chips x mult)
- **Redesigned HUD** with thumb-sized targets
- **High refresh rate** matched to your display (90/120 Hz)
- **Mods** through [Lovely](https://github.com/ethangreen-dev/lovely-injector), with optional one-command Steamodded install
- **Save transfer** from desktop Balatro or the official Play app, no root needed
- **Termux builds** with no PC, using the installed Play Store app as the source
- **Zygisk module** (experimental, root only) for the official Google Play install
- **iOS** (experimental) sideloadable `.ipa`

## Which build should I use?

If you are not sure, use the rootless APK builder. It does not need root.

| Path | Best for | Root | What you install |
|------|----------|------|------------------|
| **Rootless APK builder** | Most users | No | A separate `com.unofficial.balatro` portrait APK |
| **Termux phone build** | No PC | No | The same APK, built on the phone |
| **Zygisk module** | Rooted users keeping the official app | Yes | `balatro_portrait.zip` from Releases |
| **iOS** | Testers | No jailbreak | Experimental `.ipa` |

Ready-made rootless APKs are not uploaded here because they contain your own
Balatro files. The Zygisk ZIP only holds the portrait module, so it can live on
the Releases page.

## What you need

- A legal copy of Balatro
- Python 3.6+ for PC builds
- Termux (F-Droid or GitHub build) for phone-only builds
- Root + Zygisk only for the experimental Zygisk module

## Rootless APK builder

Build a portrait APK on Windows, macOS, or Linux:

```sh
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
python build.py
```

The first run asks where Balatro is installed and extracts what it needs. The
APK is written to:

```text
balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

Install it:

```sh
adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk
```

Common options:

```sh
python build.py --no-crt --readabletro
python build.py --steamodded                       # bundle Steamodded (newest)
python build.py --import-save "%APPDATA%\Balatro"   # bring your save across
python build.py --balatro "D:\Steam\steamapps\common\Balatro\Balatro.exe" --force
```

## Phone build (Termux, no PC)

If the official Play Store Balatro is installed, Termux can build the portrait
APK straight from it. No PC copy of `Balatro.exe` or `Game.love` is needed.

1. Install the official Play Store Balatro and launch it once.
2. Install Termux from F-Droid or GitHub.
3. In Termux run `termux-setup-storage`, tap **Allow**, then paste:

```sh
pkg update -y && pkg install -y git && rm -rf balatro-portrait-mobile && git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git && cd balatro-portrait-mobile && bash termux-build.sh --force
```

The helper installs what it needs, asks about Readabletro and CRT, then builds
and signs the APK. It is copied to `/sdcard/Download/balatro-portrait-mobile.apk`.

Full guide: [docs/TERMUX.md](docs/TERMUX.md).

## Zygisk module (experimental, root only)

This keeps the official Google Play app installed and injects portrait mode at
launch. It does not patch or re-sign the APK, but it needs root + Zygisk and is
arm64 only. It does not provide Lovely mods; that is the rootless build's job.

1. Install the official Play Store Balatro and launch it once.
2. Download `balatro_portrait.zip` from GitHub Releases.
3. Flash the ZIP from KernelSU, Magisk, or APatch.
4. Pick Readabletro/CRT options during install.
5. Reboot and launch the official Balatro app.

More details: [zygisk/README.md](zygisk/README.md).

## iOS (experimental, testers wanted)

Build with `--ios`, then sideload `balatro-portrait.ipa` with
[Sideloadly](https://sideloadly.io/) or [AltStore](https://altstore.io/). Full
guide: [docs/IOS.md](docs/IOS.md).

The notch / Dynamic Island inset (v2.6.4) and the home-indicator inset
(v2.6.5) are read from the device at runtime, but this project is developed
without an iPhone, so none of it is verified on real hardware. If the layout
still looks off on yours, `src/portrait_config.lua` has two knobs:
`safe_area_extra_ios` (more gap under the island) and
`safe_area_bottom_extra_ios` (more gap above the swipe bar).

**Testing takes five minutes and helps a lot.** [Open an issue](https://github.com/ShaggyLorean/balatro-portrait-mobile/issues)
with:

- your device model and iOS version
- a screenshot of the title screen and one mid-run
- anything clipped, overlapped, or unreachable

## Mods

The Android build ships with Lovely, so it can run mods. Most mods need
Steamodded, and the build can fetch and bundle it for you:

```sh
python build.py --steamodded          # newest Steamodded
python build.py --steamodded <tag>    # a specific release
```

A bundled mod installs itself on the first launch. Restart the game once and it
is active.

To add other mods by hand, put each one in the app's `Mods/` folder:

1. Launch the game once, then close it.
2. Install [Material Files](https://play.google.com/store/apps/details?id=me.zhanghai.android.files).
3. Menu -> **Add storage** -> **External storage** -> pick the **Balatro** app
   -> **Use this folder**.
4. Put the mod folder in `game/Mods/`, then restart.

Root and ADB work too. See [docs/MODDING.md](docs/MODDING.md).

## Save transfer

Carry your unlocks and progression into the portrait app from desktop Balatro or
the official Play Store app (via Google Takeout, no root). The build can bake a
save in, so it is there on first launch:

```sh
python build.py --import-save "%APPDATA%\Balatro"        # desktop save folder
python build.py --import-save takeout-XXXXXXXX-001.zip   # official-app export
```

Full walkthrough, including the manual copy route: [docs/SAVE_TRANSFER.md](docs/SAVE_TRANSFER.md).

## Troubleshooting

**Game will not start.** Make sure the first-run extraction finished;
`src/resources/` and `src/localization/` must exist. Re-run `python build.py`.

**Build fails.** Check `python --version` (3.6+ required). The JDK and build
tools download automatically on the first build (about 250 MB), so you need an
internet connection.

**Black ellipse or colored sliver at the bottom.** The CRT shader can cause this
in portrait on some devices. Rebuild with `python build.py --crt`, or answer
**yes** to "Apply CRT patch?" in the interactive build.

## Support

If this made mobile Balatro better for you, you can buy me a coffee.

<p align="center">
  <a href="https://ko-fi.com/loreanxavier">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support me on Ko-fi"/>
  </a>
</p>

## Credits

- **LocalThunk** for the original Balatro
- **LÖVE** for the 2D game framework
- **KtourzaJeremy** for pull requests
- **[ethangreen-dev](https://github.com/ethangreen-dev)** for the Lovely injector
- **[WilsontheWolf](https://github.com/WilsontheWolf)** for Lovely Mobile Maker
- **[bladeSk](https://github.com/bladeSk)** for the Readabletro mod
- **[blake502](https://github.com/blake502)** for the Balatro APK Maker

## Disclaimer

This is an unofficial mod. You must own a legal copy of Balatro to use it.
Original game files are **not** included in this repository.

## License

The build tooling, documentation, and portrait-mode changes here are under the
[MIT License](LICENSE). All rights to Balatro, including any game code and assets
this project derives from, belong to LocalThunk / Playstack. See the scope note
in [LICENSE](LICENSE).
