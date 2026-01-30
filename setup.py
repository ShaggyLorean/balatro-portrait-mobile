#!/usr/bin/env python3
"""
Balatro Portrait Mobile - Setup Script
Cross-platform setup for Windows and Linux
"""

import os
import shutil
import subprocess
import sys
import zipfile


def find_7zip():
    """Find 7-Zip executable based on OS"""
    if os.name == "nt":  # Windows
        paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    else:  # Linux/Mac
        # Check if 7z is in PATH
        result = subprocess.run(["which", "7z"], capture_output=True, text=True)
        if result.returncode == 0:
            return "7z"
        # Try p7zip
        result = subprocess.run(["which", "7za"], capture_output=True, text=True)
        if result.returncode == 0:
            return "7za"
        return None


def extract_balatro(balatro_path, output_dir):
    """Extract Balatro.exe using 7-Zip"""
    seven_zip = find_7zip()
    
    if not seven_zip:
        print("ERROR: 7-Zip not found!")
        print("  Windows: Install from https://7-zip.org")
        print("  Linux: sudo apt install p7zip-full")
        return False
    
    print(f"Extracting {balatro_path}...")
    
    try:
        subprocess.run(
            [seven_zip, "x", balatro_path, f"-o{output_dir}", "-y"],
            check=True,
            capture_output=True
        )
        print("Extraction complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Extraction failed: {e}")
        return False


def copy_resources(game_files_dir, src_dir):
    """Copy resources and localization to src directory"""
    resources_src = os.path.join(game_files_dir, "resources")
    localization_src = os.path.join(game_files_dir, "localization")
    
    resources_dst = os.path.join(src_dir, "resources")
    localization_dst = os.path.join(src_dir, "localization")
    
    # Check if source directories exist
    if not os.path.exists(resources_src):
        print(f"ERROR: {resources_src} not found!")
        return False
    
    if not os.path.exists(localization_src):
        print(f"ERROR: {localization_src} not found!")
        return False
    
    # Copy resources
    print("Copying resources...")
    if os.path.exists(resources_dst):
        shutil.rmtree(resources_dst)
    shutil.copytree(resources_src, resources_dst)
    
    # Copy localization
    print("Copying localization...")
    if os.path.exists(localization_dst):
        shutil.rmtree(localization_dst)
    shutil.copytree(localization_src, localization_dst)
    
    print("Resources copied successfully!")
    return True


def main():
    print("=" * 50)
    print("Balatro Portrait Mobile - Setup")
    print("=" * 50)
    print()
    
    # Get Balatro path from user or command line
    if len(sys.argv) > 1:
        balatro_path = sys.argv[1]
    else:
        print("Enter the path to Balatro.exe:")
        print("  Windows example: D:\\Steam\\steamapps\\common\\Balatro\\Balatro.exe")
        print("  Linux example: ~/.steam/steam/steamapps/common/Balatro/Balatro.exe")
        print()
        balatro_path = input("Path: ").strip().strip('"').strip("'")
    
    if not os.path.exists(balatro_path):
        print(f"ERROR: File not found: {balatro_path}")
        sys.exit(1)
    
    # Directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_files_dir = os.path.join(script_dir, "game_original_files")
    src_dir = os.path.join(script_dir, "src")
    
    # Step 1: Extract Balatro.exe
    print()
    print("[1/2] Extracting game files...")
    if not extract_balatro(balatro_path, game_files_dir):
        sys.exit(1)
    
    # Step 2: Copy resources to src
    print()
    print("[2/2] Copying resources to src...")
    if not copy_resources(game_files_dir, src_dir):
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print()
    print("Next steps:")
    print("  1. python rebuild_game.py")
    print("  2. python build_apk.py")
    print()
    print("The APK will be at: balatro-mobile-maker/balatro-aligned-debugSigned.apk")


if __name__ == "__main__":
    main()
