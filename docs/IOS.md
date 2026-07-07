# iOS Build (EXPERIMENTAL)

> **Status: experimental and untested by the maintainer** (no iOS device available).
> The build pipeline is sound, it mirrors how
> [balatro-mobile-maker](https://github.com/blake502/balatro-mobile-maker) builds
> its iOS package, but layout, safe-area/notch behavior, and performance on real
> devices have not been verified. If you try it, **please
> [open an issue](https://github.com/ShaggyLorean/balatro-portrait-mobile/issues)**
> with your device model and screenshots, working or not. We'll help you debug.

## How it works

There is no Xcode and no macOS involved. The build:

1. Downloads a prebuilt, unsigned LÖVE iOS app shell
   (`balatro-base.ipa` from [balatro-apk-maker](https://github.com/blake502/balatro-apk-maker)'s
   Additional Tools, SHA-256 verified, contains **no game data**)
2. Inserts your locally built `Game.love` (made from **your** copy of Balatro)
   into `Payload/Balatro.app/`
3. Locks `Info.plist` to portrait orientation and stamps the mod version
4. Writes `balatro-portrait.ipa`

The IPA is **unsigned by design**. Sideloading tools re-sign it with your own
Apple ID at install time.

## Building

```
python build.py --ios
```

Or answer **yes** to "Build iOS .ipa?" during the interactive build.
The output is `balatro-portrait.ipa` in the project root.

> **Note:** Lovely mod support is Android-only (`liblovely.so`). The iOS build
> is always vanilla, regardless of the Lovely setting.

## Sideloading

You need a free Apple ID. Two common options:

### Sideloadly (Windows/macOS)

1. Install [Sideloadly](https://sideloadly.io/)
2. Connect your iPhone/iPad via USB
3. Drag `balatro-portrait.ipa` into Sideloadly
4. Enter your Apple ID and press **Start**
5. On the device: **Settings → General → VPN & Device Management** → trust your
   developer certificate

### AltStore (Windows/macOS)

1. Install [AltServer](https://altstore.io/) on your computer and AltStore on
   your device
2. Open the IPA with AltStore (**My Apps → + → balatro-portrait.ipa**)

### The 7-day limit

With a free Apple ID, sideloaded apps expire after **7 days** and must be
re-signed (re-install via Sideloadly, or let AltStore auto-refresh in the
background). A paid Apple Developer account extends this to a year. Your save
data survives re-signing as long as you don't delete the app.

## Known unknowns (testers wanted)

- **Notch/Dynamic Island overlap**, the top inset is read from the device at
  runtime since v2.6.4; `safe_area_extra_ios` in `src/portrait_config.lua` adds
  extra gap if the HUD still hugs the island
- **Home indicator**, the bottom inset is read at runtime since v2.6.5 so the
  title-screen buttons clear the swipe bar; `safe_area_bottom_extra_ios` in
  `src/portrait_config.lua` adds extra gap
- **High refresh rate**, `fps_cap = 'auto'` should pick up 120 Hz on ProMotion
  devices; unverified
- **Haptics**, `love.system.vibrate` support varies on iOS; worst case it's a
  silent no-op
- **Performance**, the CRT shader may behave differently on Apple GPUs; if you
  see artifacts, rebuild with `--crt`

## Troubleshooting

### "Unable to install" / signing errors
Free Apple IDs are limited to 3 sideloaded apps and ~10 app IDs per week.
Remove an old app or wait, then retry.

### Game opens in landscape or letterboxed
This shouldn't happen (orientation is locked in `Info.plist`), if it does,
open an issue with a screenshot; that's exactly the feedback we need.

### Game crashes on launch
Re-run `python build.py --ios --force` to rule out a stale `Game.love`, and
check that the first-run resource extraction completed (`src/resources/` must
exist). If it still crashes, open an issue with your device and iOS version.
