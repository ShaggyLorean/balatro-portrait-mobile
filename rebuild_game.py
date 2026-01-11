#!/usr/bin/env python3
"""
Rebuild Game.love from src folder
This script creates a fresh Game.love file from the modified source files in src/
"""

import os
import sys
import zipfile


def rebuild_game_love():
    """Rebuild Game.love from src folder"""

    src_dir = "src"
    output_file = "Game.love"

    if not os.path.exists(src_dir):
        print(f"Error: {src_dir} directory not found!")
        sys.exit(1)

    # Remove old Game.love if exists
    if os.path.exists(output_file):
        print(f"Removing old {output_file}...")
        os.remove(output_file)

    print(f"Building {output_file} from {src_dir}...")

    # Files and directories to exclude from the build
    exclude_patterns = [
        "smali",  # Android-specific, handled separately
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
        # Walk through src directory
        for root, dirs, files in os.walk(src_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

            for file in files:
                if should_exclude(file):
                    continue

                file_path = os.path.join(root, file)

                # Calculate archive name (relative to src, not including 'src/')
                arcname = os.path.relpath(file_path, src_dir)

                zipf.write(file_path, arcname)
                file_count += 1
                print(f"  Added: {arcname}")

    file_size = os.path.getsize(output_file)
    print(f"\n✓ Successfully created {output_file}")
    print(f"  Files: {file_count}")
    print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"\nYou can now run: python3 build_apk.py")


if __name__ == "__main__":
    rebuild_game_love()
