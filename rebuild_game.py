#!/usr/bin/env python3
"""
Rebuild Game.love from src folder
This script creates a fresh Game.love file from the modified source files in src/
"""

import os
import sys
import zipfile
import re
import shutil

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


def ask_readabletro_patch():
    """Ask user if they want to apply Readabletro mod"""
    print()
    print("=" * 60)
    print("READABLETRO MOD")
    print("=" * 60)
    print()
    print("This applies the 'Readabletro' font and high-contrast")
    print("shaders to make the game much easier to read.")
    print("Original pixel font is replaced with TypoQuik-Bold.")
    print()
    
    while True:
        response = input("Apply Readabletro mod? (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'y' or 'n'")


def apply_readabletro_patch(src_dir, apply=True):
    """Apply or revert Readabletro mod to game files"""
    replacements = {
        "game.lua": [
            ('{file = "resources/fonts/m6x11plus.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
             '{file = "resources/fonts/TypoQuik-Bold.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}'),
            ('{file = "resources/fonts/m6x11plus.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.9, TEXT_OFFSET = {x=10,y=15}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
             '{file = "resources/fonts/TypoQuik-Bold.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}')
        ],
        "main.lua": [
            ('local font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 20)',
             'local font = love.graphics.setNewFont("resources/fonts/TypoQuik-Bold.ttf", 20)')
        ],
        "functions/misc_functions.lua": [
            ('font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 20),',
             'font = love.graphics.setNewFont("resources/fonts/TypoQuik-Bold.ttf", 20),')
        ]
    }
    
    font_src = os.path.join("patches", "readabletro", "fonts", "TypoQuik-Bold.ttf")
    font_dst = os.path.join(src_dir, "resources", "fonts", "TypoQuik-Bold.ttf")
    
    shaders = ["background.fs", "splash.fs"]
    shader_dir_src = os.path.join("patches", "readabletro", "shaders")
    shader_dir_dst = os.path.join(src_dir, "resources", "shaders")
    
    texture_dir_src = os.path.join("patches", "readabletro", "textures", "2x")
    texture_dir_dst = os.path.join(src_dir, "resources", "textures", "2x")
    
    if apply:
        # -- Lua file patches --
        for rel_path, reps in replacements.items():
            filepath = os.path.join(src_dir, rel_path)
            if not os.path.exists(filepath): continue
            
            bak_path = filepath + ".bak"
            if not os.path.exists(bak_path):
                shutil.copy2(filepath, bak_path)
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            for orig, mod in reps:
                content = content.replace(orig, mod)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # -- Font --
        if os.path.exists(font_src):
            shutil.copy2(font_src, font_dst)
            
        # -- Shaders --
        for shader in shaders:
            s_src = os.path.join(shader_dir_src, shader)
            s_dst = os.path.join(shader_dir_dst, shader)
            s_bak = s_dst + ".bak"
            if os.path.exists(s_dst) and not os.path.exists(s_bak):
                shutil.copy2(s_dst, s_bak)
            if os.path.exists(s_src):
                shutil.copy2(s_src, s_dst)
        
        # -- Textures --
        tex_count = 0
        if os.path.isdir(texture_dir_src):
            for tex_file in os.listdir(texture_dir_src):
                if not tex_file.endswith(".png"):
                    continue
                t_src = os.path.join(texture_dir_src, tex_file)
                t_dst = os.path.join(texture_dir_dst, tex_file)
                t_bak = t_dst + ".bak"
                if os.path.exists(t_dst) and not os.path.exists(t_bak):
                    shutil.copy2(t_dst, t_bak)
                shutil.copy2(t_src, t_dst)
                tex_count += 1
            print(f"  Replaced {tex_count} textures")
                
        print("Readabletro mod enabled")
    else:
        # -- Revert Lua files --
        for rel_path, reps in replacements.items():
            filepath = os.path.join(src_dir, rel_path)
            bak_path = filepath + ".bak"
            if os.path.exists(bak_path):
                shutil.copy2(bak_path, filepath)
                os.remove(bak_path)
                
        # -- Revert font --
        if os.path.exists(font_dst):
            os.remove(font_dst)
            
        # -- Revert shaders --
        for shader in shaders:
            s_dst = os.path.join(shader_dir_dst, shader)
            s_bak = s_dst + ".bak"
            if os.path.exists(s_bak):
                shutil.copy2(s_bak, s_dst)
                os.remove(s_bak)
        
        # -- Revert textures --
        if os.path.isdir(texture_dir_dst):
            for tex_file in os.listdir(texture_dir_dst):
                t_bak = os.path.join(texture_dir_dst, tex_file)
                if t_bak.endswith(".bak"):
                    original = t_bak[:-4]
                    shutil.copy2(t_bak, original)
                    os.remove(t_bak)


def rebuild_game_love(apply_crt_patch_flag=False, apply_readabletro_flag=False):
    """Rebuild Game.love from src folder"""

    src_dir = "src"
    output_file = "Game.love"

    if not os.path.exists(src_dir):
        print(f"Error: {src_dir} directory not found!")
        sys.exit(1)

    if apply_crt_patch_flag:
        apply_crt_patch(src_dir, apply=True)
        
    if apply_readabletro_flag:
        apply_readabletro_patch(src_dir, apply=True)

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
        ".bak",
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
        
    if apply_readabletro_flag:
        apply_readabletro_patch(src_dir, apply=False)
        
    print("Source files restored to original state")

    file_size = os.path.getsize(output_file)
    print(f"\n[OK] Successfully created {output_file}")
    print(f"  Files: {file_count}")
    print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"\nYou can now run: python build_apk.py")


if __name__ == "__main__":
    if '--crt' in sys.argv:
        apply_crt = True
    elif '--no-crt' in sys.argv:
        apply_crt = False
    else:
        apply_crt = ask_crt_patch()
        
    if '--readabletro' in sys.argv:
        apply_readabletro = True
    elif '--no-readabletro' in sys.argv:
        apply_readabletro = False
    else:
        apply_readabletro = ask_readabletro_patch()
        
    rebuild_game_love(apply_crt_patch_flag=apply_crt, apply_readabletro_flag=apply_readabletro)
