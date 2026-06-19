#!/usr/bin/env python3
"""
import_save.py - Recover a Balatro save for the portrait build.

Two sources are supported:

  * A Google Takeout export of the official Play Store save (no root, no Shizuku).
    Each save is a Play Games snapshot folder like "1-meta.jkr" with the real blob
    inside as "Data.bin".
  * A desktop Balatro save folder (Steam/standalone), e.g. %APPDATA%\\Balatro on
    Windows, which already stores plain "1/meta.jkr", "1/profile.jkr", ... files.

Run standalone it writes the recovered files to game/<slot>/, ready to drop into
the portrait app's save folder. build.py imports collect_saves() to bake a save
straight into the APK (see docs/SAVE_TRANSFER.md).

Usage:
    python tools/import_save.py <takeout.zip | save-folder> [-o OUTDIR]
"""

import argparse
import os
import re
import sys
import zipfile

# Takeout snapshot: ".../Saved Games/1-meta.jkr/Data.bin". The leading number is
# the Balatro profile slot.
SNAPSHOT_RE = re.compile(
    r"(?:^|/)(\d+)-(meta|profile|save|unlock_notify)\.jkr/Data\.bin$",
    re.IGNORECASE,
)

# Desktop/Android layout: ".../1/profile.jkr".
PLAIN_RE = re.compile(
    r"(?:^|/)(\d+)/(meta|profile|save|unlock_notify)\.jkr$",
    re.IGNORECASE,
)


def find_in_zip(zip_path):
    found = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            match = SNAPSHOT_RE.search(name.replace("\\", "/"))
            if match:
                found.append((match.group(1), match.group(2).lower(), archive.read(name)))
    return found


def _walk(root, pattern):
    found = []
    for dirpath, _dirs, files in os.walk(root):
        for filename in files:
            full = os.path.join(dirpath, filename)
            match = pattern.search(full.replace("\\", "/"))
            if match:
                with open(full, "rb") as handle:
                    found.append((match.group(1), match.group(2).lower(), handle.read()))
    return found


def collect_saves(source):
    """Return {slot: {kind: bytes}} for the saves found in a Takeout export
    (zip or folder) or a plain Balatro save folder."""
    if not os.path.exists(source):
        raise FileNotFoundError(f"'{source}' does not exist")

    if os.path.isdir(source):
        found = _walk(source, SNAPSHOT_RE) or _walk(source, PLAIN_RE)
    elif zipfile.is_zipfile(source):
        found = find_in_zip(source)
    else:
        raise ValueError(f"'{source}' is not a folder or a .zip")

    saves = {}
    for slot, kind, data in found:
        saves.setdefault(slot, {})[kind] = data
    return saves


def main():
    parser = argparse.ArgumentParser(
        description="Recover Balatro .jkr save files from a Takeout export or a desktop save folder."
    )
    parser.add_argument("source", help="The Takeout .zip, or a Balatro save folder")
    parser.add_argument(
        "-o", "--out", default="balatro-save-import",
        help="Output folder (default: balatro-save-import)",
    )
    args = parser.parse_args()

    try:
        saves = collect_saves(args.source)
    except Exception as exc:
        sys.exit(f"error: {exc}")

    if not saves:
        sys.exit(
            "No Balatro saves found.\n"
            "For the official app, export \"Google Play Game Services\" in Takeout.\n"
            "For desktop, point at your Balatro save folder (e.g. %APPDATA%\\Balatro)."
        )

    print("Recovered save files:")
    for slot in sorted(saves):
        slot_dir = os.path.join(args.out, "game", slot)
        os.makedirs(slot_dir, exist_ok=True)
        for kind, data in saves[slot].items():
            with open(os.path.join(slot_dir, f"{kind}.jkr"), "wb") as handle:
                handle.write(data)
        print(f"  profile {slot}: " + ", ".join(f"{k}.jkr" for k in sorted(saves[slot])))

    out_game = os.path.abspath(os.path.join(args.out, "game"))
    print()
    print(f"Written to: {out_game}")
    print("Copy the game/<slot>/ folder into the portrait app's save, or just build")
    print("with  python build.py --import-save <this source>  to bake it into the APK.")


if __name__ == "__main__":
    main()
