#!/usr/bin/env python3
"""
import_save.py - Recover a Balatro save from a Google Takeout export.

The official Google Play build of Balatro backs its save up to Google Play Games
Services. You can export that data with Google Takeout (no root and no Shizuku)
and move it into the portrait build. This script handles the unzip-and-rename
step: it reads the Play Games snapshots out of the export and writes the plain
.jkr files Balatro expects.

See docs/SAVE_TRANSFER.md for the full walkthrough, including how to request the
Takeout export and where to drop the files afterwards.

Usage:
    python tools/import_save.py <takeout.zip | extracted-folder> [-o OUTDIR]
"""

import argparse
import os
import re
import sys
import zipfile

# Play Games stores each snapshot in a folder named like "1-meta.jkr" with the
# real save blob inside as "Data.bin". The leading number is the Balatro profile
# slot (1, 2, 3). We keep meta/profile/save and skip everything else.
SNAPSHOT_RE = re.compile(
    r"(?:^|/)(\d+)-(meta|profile|save|unlock_notify)\.jkr/Data\.bin$",
    re.IGNORECASE,
)


def find_in_zip(zip_path):
    found = []
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            match = SNAPSHOT_RE.search(name.replace("\\", "/"))
            if match:
                found.append((match.group(1), match.group(2).lower(), z.read(name)))
    return found


def find_in_dir(root):
    found = []
    for dirpath, _dirs, files in os.walk(root):
        for filename in files:
            full = os.path.join(dirpath, filename)
            match = SNAPSHOT_RE.search(full.replace("\\", "/"))
            if match:
                with open(full, "rb") as handle:
                    found.append((match.group(1), match.group(2).lower(), handle.read()))
    return found


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Google Takeout Play Games export into Balatro .jkr save files."
    )
    parser.add_argument("source", help="The Takeout .zip, or an already-extracted folder")
    parser.add_argument(
        "-o", "--out", default="balatro-save-import",
        help="Output folder (default: balatro-save-import)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.source):
        sys.exit(f"error: '{args.source}' does not exist")

    if os.path.isdir(args.source):
        found = find_in_dir(args.source)
    elif zipfile.is_zipfile(args.source):
        found = find_in_zip(args.source)
    else:
        sys.exit(f"error: '{args.source}' is not a folder or a .zip")

    if not found:
        sys.exit(
            "No Balatro Play Games snapshots found.\n"
            'Make sure you exported "Google Play Game Services" in Takeout and that\n'
            "the archive contains paths like .../Saved Games/1-meta.jkr/Data.bin"
        )

    slots = {}
    for slot, kind, data in found:
        slot_dir = os.path.join(args.out, "game", slot)
        os.makedirs(slot_dir, exist_ok=True)
        with open(os.path.join(slot_dir, f"{kind}.jkr"), "wb") as handle:
            handle.write(data)
        slots.setdefault(slot, []).append(f"{kind}.jkr")

    print("Recovered save files:")
    for slot in sorted(slots):
        print(f"  profile {slot}: " + ", ".join(sorted(slots[slot])))

    out_game = os.path.abspath(os.path.join(args.out, "game"))
    print()
    print(f"Written to: {out_game}")
    print("Next, copy the game/<slot>/ folder into the portrait app's save at")
    print("  game/<slot>/   (see docs/SAVE_TRANSFER.md for no-root / root / ADB paths)")


if __name__ == "__main__":
    main()
