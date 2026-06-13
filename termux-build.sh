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

exec python build.py --no-crt --readabletro --no-ios "$@"
