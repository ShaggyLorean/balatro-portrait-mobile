#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [ ! -d /data/data/com.termux/files/usr ]; then
  echo "ERROR: this helper is only for Termux on Android." >&2
  exit 1
fi

missing=()
command -v git >/dev/null 2>&1 || missing+=("git")
command -v python >/dev/null 2>&1 || missing+=("python")
command -v java >/dev/null 2>&1 || missing+=("openjdk-17")

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Installing Termux packages: ${missing[*]}"
  pkg update -y
  pkg install -y "${missing[@]}"
fi

# Build options. Termux runs in a real terminal, so ask through /dev/tty instead
# of stdin; that still works when this helper is launched from a pasted command
# chain. Explicit flags keep working for scripted builds.
opts=()
has_readabletro_flag=0
has_crt_flag=0
for arg in "$@"; do
  case "$arg" in
    --readabletro|--no-readabletro) has_readabletro_flag=1 ;;
    --crt|--no-crt) has_crt_flag=1 ;;
  esac
done

ask_yes_no() {
  local prompt="$1"
  local default="$2"
  local ans=""
  local hint="[y/N]"
  [ "$default" = "yes" ] && hint="[Y/n]"

  if [ -r /dev/tty ]; then
    while true; do
      printf '%s %s ' "$prompt" "$hint" > /dev/tty
      read -r ans < /dev/tty || ans=""
      case "$ans" in
        "") [ "$default" = "yes" ] && return 0 || return 1 ;;
        [Yy]|[Yy][Ee][Ss]) return 0 ;;
        [Nn]|[Nn][Oo]) return 1 ;;
        *) echo "Please answer y or n." > /dev/tty ;;
      esac
    done
  fi

  [ "$default" = "yes" ]
}

echo
echo "Balatro Portrait build options"
if [ "$has_readabletro_flag" -eq 0 ]; then
  if ask_yes_no "Apply Readabletro font and high-res textures?" "yes"; then
    opts+=("--readabletro")
  else
    opts+=("--no-readabletro")
  fi
fi

if [ "$has_crt_flag" -eq 0 ]; then
  if ask_yes_no "Disable CRT in portrait mode?" "no"; then
    opts+=("--crt")
  else
    opts+=("--no-crt")
  fi
fi

has_import_flag=0
for arg in "$@"; do
  case "$arg" in --import-save|--import-save=*) has_import_flag=1 ;; esac
done
if [ "$has_import_flag" -eq 0 ] && [ -r /dev/tty ]; then
  printf 'Import a save from a Google Takeout zip? Enter path (blank to skip): ' > /dev/tty
  read -r import_path < /dev/tty || import_path=""
  if [ -n "$import_path" ]; then opts+=("--import-save" "$import_path"); fi
fi

has_smods_flag=0
for arg in "$@"; do
  case "$arg" in --steamodded|--steamodded=*) has_smods_flag=1 ;; esac
done
if [ "$has_smods_flag" -eq 0 ] && [ -r /dev/tty ]; then
  if ask_yes_no "Bundle Steamodded (newest)?" "no"; then
    opts+=("--steamodded")
  fi
fi
echo

python build.py --no-ios "${opts[@]}" "$@"

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
