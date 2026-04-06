import os
import sys
import json
import subprocess

CONFIG_FILE = ".buildconfig.json"

def ask_yes_no(prompt, default=None):
    if default is not None:
        prompt += f" (y/n) [default: {'y' if default else 'n'}]: "
    else:
        prompt += " (y/n): "
        
    while True:
        response = input(prompt).strip().lower()
        if not response and default is not None:
            return default
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'")

def main():
    print("=========================================")
    print(" BALATRO PORTRAIT MOBILE - AUTO BUILDER  ")
    print("=========================================")
    print()

    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            print("Found previous build configuration:")
            print(f"  CRT Patch:      {'Enabled' if config.get('crt') else 'Disabled'}")
            print(f"  Readabletro:    {'Enabled' if config.get('readabletro') else 'Disabled'}")
            print(f"  Lovely Mod:     {'Enabled' if config.get('lovely') else 'Disabled'}")
            print()
            
            use_last = ask_yes_no("Use these settings?", default=True)
            if not use_last:
                config = {}
        except Exception as e:
            print(f"Got error loading config: {e}. Starting fresh.")
    
    if not config:
        print("\n--- Configuration Setup ---")
        config['crt'] = ask_yes_no("Apply CRT disable patch (fixes black ellipse bug)?", default=False)
        config['readabletro'] = ask_yes_no("Apply Readabletro patch (better font and textures)?", default=True)
        config['lovely'] = ask_yes_no("Enable Lovely mod support? (Requires rooted device to add mods)", default=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print("Saved configuration for next time.")
        
    print("\n[1/3] Checking source files...")
    if not os.path.exists("src"):
        print("Error: 'src' folder not found.")
        print("Please run setup.py first to extract the game files:")
        print("  python setup.py \"C:\\path\\to\\Balatro.exe\"")
        sys.exit(1)
        
    print("\n[2/3] Rebuilding Game.love...")
    rebuild_args = [sys.executable, "rebuild_game.py"]
    rebuild_args.append("--crt" if config.get('crt') else "--no-crt")
    rebuild_args.append("--readabletro" if config.get('readabletro') else "--no-readabletro")
    
    res = subprocess.run(rebuild_args)
    if res.returncode != 0:
        print("\nERROR: rebuild_game.py failed.")
        sys.exit(1)
        
        
    print("\n[3/3] Building APK...")
    build_args = [sys.executable, "build_apk.py"]
    build_args.append("--with-lovely" if config.get('lovely') else "--no-lovely")
    
    res = subprocess.run(build_args)
    if res.returncode != 0:
        print("\nERROR: build_apk.py failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
