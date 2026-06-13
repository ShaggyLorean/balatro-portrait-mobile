# Termux Build Guide

This is the no-PC, no-root path. It builds a separate
`com.unofficial.balatro` APK directly on your Android phone.

You still need to own Balatro. The builder reads resources from the official
Play Store install already on your phone; it does not download or include the
game.

## What You Need

- The official Google Play Balatro installed
- Termux from F-Droid or GitHub
- Internet connection for the first build
- A few GB of free storage for Termux packages and build files

Do not use the old Play Store Termux build. It is outdated and package installs
are broken on many devices.

## Build

1. Install the official Google Play Balatro.
2. Launch Balatro once, then close it.
3. Open Termux.
4. Allow Termux to write the finished APK to Downloads:

```sh
termux-setup-storage
```

Tap **Allow** when Android asks for storage access.

5. Run the build:

```sh
pkg update
pkg install git
git clone https://github.com/ShaggyLorean/balatro-portrait-mobile.git
cd balatro-portrait-mobile
bash termux-build.sh --force
```

The helper installs missing Python/Java packages, runs `build.py`, downloads the
Android build tools it needs, builds the portrait APK, signs it, and copies it to:

```text
/sdcard/Download/balatro-portrait-mobile.apk
```

Open that APK from your file manager and install it.

## What The Script Does

On Termux, `build.py` detects the installed official app by calling:

```sh
/system/bin/pm path com.playstack.balatro.android
```

It uses the official app's `base.apk` as the resource source, then extracts:

```text
assets/resources/
assets/localization/
```

Those files are copied into the local build only. The output is a separate
rootless APK with package name:

```text
com.unofficial.balatro
```

The official Play Store app is not modified.

## If You Already Have Balatro.exe Or Game.love

You can still build from a copied desktop game file:

```sh
python build.py --balatro ~/Balatro.exe --force
```

The automatic Play Store app detection is only used when you do not pass
`--balatro`.

## Troubleshooting

### `termux-setup-storage` was not run

The build can still finish, but the helper may not be able to copy the APK to
Downloads. Run:

```sh
termux-setup-storage
```

Then rerun:

```sh
bash termux-build.sh --force
```

### `Balatro game file` prompt appears

That means `build.py` could not find the official Play Store package. Make sure
the official game is installed and the package name is:

```text
com.playstack.balatro.android
```

Then rerun the helper.

### Build is slow

The first build installs Python/Java and downloads apktool, aapt2, signer tools,
and the Lovely base APK. Later builds reuse the downloaded files and are much
faster.

### Android says the APK is unsafe or unknown

Enable **Install unknown apps** for your file manager. This is normal for a
locally built APK.

### App already installed / signature conflict

Uninstall the old `com.unofficial.balatro` build, then install the new APK.
Your official Play Store Balatro is a different package and does not need to be
removed.
