#!/usr/bin/env python3
"""
Rebuild Game.love from src folder
This script creates a fresh Game.love file from the modified source files in src/
"""

import os
import sys
import zipfile
import re

CRT_PATCH_ORIGINAL = 'if (not G.recording_mode or G.video_control) and true then'
CRT_PATCH_MODIFIED = 'if (not G.recording_mode or G.video_control) and true and not G.F_PORTRAIT then'


def ask_crt_patch():
    """Ask user if they want to apply CRT disable patch"""
    print()
    print("=" * 60)
    print("CRT SHADER PATCH")
    print("=" * 60)
    print()
    print("Some devices show a BLACK ELLIPSE covering part of the screen.")
    print("This is caused by the CRT shader not working correctly in")
    print("portrait mode on certain Android devices.")
    print()
    print("If you experience this issue, enable the CRT patch.")
    print("If your game works fine, you can skip this patch to keep")
    print("the CRT visual effects.")
    print()
    
    while True:
        response = input("Apply CRT disable patch? (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'y' or 'n'")


def apply_crt_patch(src_dir, apply=True):
    """Apply or revert CRT patch to game.lua"""
    game_lua = os.path.join(src_dir, "game.lua")
    
    if not os.path.exists(game_lua):
        print(f"Warning: {game_lua} not found, skipping CRT patch")
        return False
    
    with open(game_lua, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if apply:
        if CRT_PATCH_MODIFIED in content:
            return True
        if CRT_PATCH_ORIGINAL not in content:
            print("Warning: Could not find CRT shader code to patch")
            return False
        content = content.replace(CRT_PATCH_ORIGINAL, CRT_PATCH_MODIFIED)
        print("CRT shader disabled for portrait mode")
    else:
        if CRT_PATCH_ORIGINAL in content:
            return True
        if CRT_PATCH_MODIFIED not in content:
            return True
        content = content.replace(CRT_PATCH_MODIFIED, CRT_PATCH_ORIGINAL)
    
    with open(game_lua, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def rebuild_game_love(apply_crt_patch_flag=False):
    """Rebuild Game.love from src folder"""

    src_dir = "src"
    output_file = "Game.love"

    if not os.path.exists(src_dir):
        print(f"Error: {src_dir} directory not found!")
        sys.exit(1)

    if apply_crt_patch_flag:
        apply_crt_patch(src_dir, apply=True)

    if os.path.exists(output_file):
        print(f"Removing old {output_file}...")
        os.remove(output_file)

    print(f"Building {output_file} from {src_dir}...")

    exclude_patterns = [
        "smali",
        ".pyc",
        "__pycache__",
        ".git",
        ".gitignore",
        "zip_game.py",
    ]

    def should_exclude(path):
        """Check if a path should be excluded"""
        for pattern in exclude_patterns:
            if pattern in path:
                return True
        return False

    file_count = 0

    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

            for file in files:
                if should_exclude(file):
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, src_dir)

                zipf.write(file_path, arcname)
                file_count += 1
                print(f"  Added: {arcname}")

    if apply_crt_patch_flag:
        apply_crt_patch(src_dir, apply=False)
        print("Source files restored to original state")

    file_size = os.path.getsize(output_file)
    print(f"\n✓ Successfully created {output_file}")
    print(f"  Files: {file_count}")
    print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"\nYou can now run: python build_apk.py")


if __name__ == "__main__":
    apply_patch = ask_crt_patch()
    rebuild_game_love(apply_crt_patch_flag=apply_patch)
