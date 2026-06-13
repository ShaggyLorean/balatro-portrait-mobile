#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [ ! -d /data/data/com.termux/files/usr ]; then
  echo "ERROR: this helper is only for Termux on Android." >&2
  exit 1
fi

missing=()
command -v python >/dev/null 2>&1 || missing+=("python")
command -v java >/dev/null 2>&1 || missing+=("openjdk-17")

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Installing Termux packages: ${missing[*]}"
  pkg install -y "${missing[@]}"
fi

python build.py --no-crt --readabletro --no-ios "$@"

apk="balatro-mobile-maker/balatro-aligned-debugSigned.apk"
download_apk="/sdcard/Download/balatro-portrait-mobile.apk"

if [ ! -f "$apk" ]; then
  echo "ERROR: build finished, but APK was not found at $apk" >&2
  exit 1
fi

echo
echo "APK built:"
echo "  $(pwd)/$apk"

if [ -d /sdcard/Download ] && cp "$apk" "$download_apk" 2>/dev/null; then
  echo
  echo "Copied to:"
  echo "  $download_apk"
  echo
  echo "Open it from your file manager and install it."
else
  echo
  echo "Could not copy the APK to Downloads."
  echo "Run this once, tap Allow, then rerun the build:"
  echo "  termux-setup-storage"
fi
