#!/usr/bin/env python3
"""
Balatro Portrait Mobile - Unified Build Script

Handles everything: resource extraction, Game.love creation, and APK packaging.
Runs on Windows, macOS, Linux, and Termux on Android. On Termux, use
`bash termux-build.sh` for a PC-free build from the installed Play Store app;
an ARM aapt2 is downloaded automatically, or a native apktool already in PATH
is used as-is.

Usage:
    python build.py [options]

Options:
    --crt                 Apply the CRT-disabling portrait patch
    --no-crt              Keep the source CRT shader path unchanged (default)
    --readabletro         Apply Readabletro font and high-res texture patch (default)
    --no-readabletro      Skip Readabletro patch
    --ios                 Also build an iOS .ipa for sideloading (EXPERIMENTAL)
    --no-ios              Skip the iOS build (default)
    --balatro PATH        Path to Balatro game file (skips the interactive prompt)
    --skip-setup          Skip resource extraction (if src/resources already exists)
    --skip-apk            Only build Game.love, skip APK packaging
    --force               Force Game.love rebuild even if sources are unchanged
"""

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MOD_VERSION = "2.6.3"

CONFIG_FILE = ".buildconfig.json"
CACHE_FILE  = ".build_cache.json"
OFFICIAL_ANDROID_PACKAGE = "com.playstack.balatro.android"
DEFAULT_BUILD_CONFIG = {
    "crt": False,
    "readabletro": True,
    "ios": False,
}

WORKDIR  = os.path.abspath("balatro-mobile-maker")
JDK_DIR  = os.path.join(WORKDIR, "jdk")
JAVA_BIN = os.path.join(JDK_DIR, "bin", "java")  # resolved after JDK extraction

# Termux (building directly on an Android phone): the downloaded desktop JDK
# and the aapt binaries bundled inside the apktool jar are x86-64 only and
# cannot run on ARM64 Android. Use Termux-native Java and an ARM64-compatible
# apktool/aapt2 instead. Some Termux setups do not ship apktool in the official
# repos; the build script validates the tools and prints actionable errors.
#   pkg install python openjdk-17
IS_TERMUX = bool(os.environ.get("TERMUX_VERSION")) or os.path.isdir("/data/data/com.termux/files/usr")

if os.name == "nt":
    JDK_URL    = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-windows-x64.zip"
    JDK_SHA256 = "d1c5a1c674bf472838c4d63c46c2e23a8efd399362e40abebd4eee4988bc2130"
elif platform.system() == "Darwin":
    if platform.machine() == "arm64":
        JDK_URL    = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-aarch64.tar.gz"
        JDK_SHA256 = "489c96c8a4d3592811d1907346c05b75c12642729f83576982b9f62d0aafc672"
    else:
        JDK_URL    = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-x64.tar.gz"
        JDK_SHA256 = "cf7d2c967088ac71b29cf28ad791a071bbf2c1dab333dd73dc0e791cb974c1f6"
else:
    JDK_URL    = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-linux-x64.tar.gz"
    JDK_SHA256 = "b535a58db80aeb5cc0d5e85ae6cb3f621d7f269ca1b36832f1aed3842cede4f4"

APKTOOL_URL    = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
SIGNER_URL     = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
PATCH_URL      = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/Balatro-APK-Patch.zip"
# The LMM base APK is rebuilt upstream without version-pinned URLs, so it cannot
# be hash-pinned here. All version-pinned downloads above are SHA-256 verified.
LOVELY_APK_URL = "https://lmm.shorty.systems/base.apk"

# ReVanced's prebuilt native aapt2 binaries. The apktool jar only ships an
# x86-64 aapt2, which cannot run on ARM Android, so when building on Termux we
# point apktool at one of these via --use-aapt2. https://github.com/ReVanced/aapt2
REVANCED_AAPT2_BASE = "https://github.com/ReVanced/aapt2/releases/download/v1.1.0/"

# iOS (experimental): prebuilt unsigned LOVE iOS app shell from balatro-apk-maker.
# Game.love is inserted into the .app, Info.plist is locked to portrait, and the
# result is sideloaded with Sideloadly/AltStore which re-sign it with the user's
# Apple ID — no Xcode or macOS needed.
IOS_BASE_URL = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/balatro-base.ipa"

TOOL_SHA256 = {
    JDK_URL:      JDK_SHA256,
    APKTOOL_URL:  "7956eb04194300ce0d0a84ad18771eebc94b89fb8d1ddcce8ea4c056818646f4",
    SIGNER_URL:   "e1299fd6fcf4da527dd53735b56127e8ea922a321128123b9c32d619bba1d835",
    PATCH_URL:    "efa47e113b15b2963a193ff6b988544f58e0dab26a75b439943d55dba0f5b489",
    IOS_BASE_URL: "1b7a060dc06f7d3ea54fd24f04ff9fcedde7a0e3539c96bfee175499b723f661",
}

# These strings must match exactly what's in src/game.lua
CRT_PATCH_ORIGINAL = 'if (not G.recording_mode or G.video_control) and true then'
CRT_PATCH_MODIFIED = 'if (not G.recording_mode or G.video_control) and true and not G.F_PORTRAIT then'
CRT_MASK_ORIGINAL = '''    //smoothly transition the edge to black
    //buffer for the outer edge, this gets wonky if there is no buffer
    MY_HIGHP_OR_MEDIUMP number mask = (1.0 - smoothstep(1.0-feather_fac,1.0,abs(tc.x) - BUFF))
                * (1.0 - smoothstep(1.0-feather_fac,1.0,abs(tc.y) - BUFF));'''
CRT_MASK_MODIFIED = CRT_MASK_ORIGINAL + '''
    mask = 1.0 - (1.0 - mask) * clamp(crt_intensity/(0.16*0.3), 0.0, 1.0);'''
CRT_NOISE_COMMENTED_LINES = (
    ("//extern MY_HIGHP_OR_MEDIUMP number noise_fac;", "extern MY_HIGHP_OR_MEDIUMP number noise_fac;"),
    ("    //MY_HIGHP_OR_MEDIUMP number x = (tc.x - mod(tc.x, 0.002)) * (tc.y - mod(tc.y, 0.0013)) * time * 1000.0;",
     "    MY_HIGHP_OR_MEDIUMP number x = (tc.x - mod(tc.x, 0.002)) * (tc.y - mod(tc.y, 0.0013)) * time * 1000.0;"),
    ("\t//x = mod( x, 13.0 ) * mod( x, 123.0 );",
     "\tx = mod( x, 13.0 ) * mod( x, 123.0 );"),
    ("\t//MY_HIGHP_OR_MEDIUMP number dx = mod( x, 0.11 )/0.11;",
     "\tMY_HIGHP_OR_MEDIUMP number dx = mod( x, 0.11 )/0.11;"),
    ("\t//rgb_result = (1.0-clamp( noise_fac*artifact_amplifier, 0.0,1.0 ))*rgb_result + dx * clamp( noise_fac*artifact_amplifier, 0.0,1.0 ) * vec3(1.0,1.0,1.0);",
     "\trgb_result = (1.0-clamp( noise_fac*artifact_amplifier, 0.0,1.0 ))*rgb_result + dx * clamp( noise_fac*artifact_amplifier, 0.0,1.0 ) * vec3(1.0,1.0,1.0);"),
)

GAME_LOVE_EXCLUDE = {"smali", ".pyc", "__pycache__", ".git", ".gitignore", ".bak", ".build_cache.json"}

READABLETRO_LUA_PATCHES = {
    "game.lua": [
        (
            '{file = "resources/fonts/m6x11plus.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
            '{file = "resources/fonts/TypoQuik-Bold.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
        ),
        (
            '{file = "resources/fonts/m6x11plus.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.9, TEXT_OFFSET = {x=10,y=15}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
            '{file = "resources/fonts/TypoQuik-Bold.ttf", render_scale = self.TILESIZE*10, TEXT_HEIGHT_SCALE = 0.83, TEXT_OFFSET = {x=10,y=-20}, FONTSCALE = 0.1, squish = 1, DESCSCALE = 1}',
        ),
    ],
    "functions/misc_functions.lua": [
        (
            'font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 20),',
            'font = love.graphics.setNewFont("resources/fonts/TypoQuik-Bold.ttf", 20),',
        ),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class BuildProfiler:
    def __init__(self):
        self.steps = []
        self._wall = time.time()

    def step(self, name):
        return _Step(self, name)

    def record(self, name, duration):
        self.steps.append((name, duration))

    def report(self):
        total = sum(d for _, d in self.steps)
        wall  = time.time() - self._wall
        sep = "-" * 50
        print(f"\n{sep}")
        print("Build time breakdown:")
        for name, d in self.steps:
            pct = d / total * 100 if total else 0
            print(f"  {name:<28}  {d:>5.1f}s  ({pct:.0f}%)")
        print(f"  {'Total':<28}  {wall:>5.1f}s")
        print(sep)


class _Step:
    def __init__(self, profiler, name):
        self.p    = profiler
        self.name = name

    def __enter__(self):
        self._t = time.time()
        return self

    def __exit__(self, *_):
        self.p.record(self.name, time.time() - self._t)


def _ask(prompt, default=None):
    hint = f" [{'y' if default else 'n'}]" if default is not None else ""
    while True:
        try:
            r = input(f"{prompt}{hint}: ").strip().lower()
        except EOFError:
            if default is not None:
                print(f"{prompt}{hint}: {'y' if default else 'n'}")
                return default
            raise
        if not r and default is not None:
            return default
        if r in ("y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("  Please enter y or n.")


def _sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_download(url, dest):
    expected = TOOL_SHA256.get(url)
    if not expected:
        return
    actual = _sha256_of(dest)
    if actual != expected:
        print(f"  ERROR: SHA-256 mismatch for {os.path.basename(dest)}")
        print(f"    expected: {expected}")
        print(f"    actual:   {actual}")
        print("  The download may be corrupted or tampered with.")
        print(f"  Delete the file and re-run: {dest}")
        os.remove(dest)
        sys.exit(1)


def _download(url, dest):
    if os.path.exists(dest):
        print(f"  Already downloaded: {os.path.basename(dest)}")
        _verify_download(url, dest)
        return
    print(f"  Downloading {os.path.basename(dest)} ...")
    tmp = dest + ".part"
    try:
        req  = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=120)
        total = int(resp.headers.get("Content-Length", 0))
        done  = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    pct    = min(done / total * 100, 100)
                    filled = int(30 * pct / 100)
                    bar    = "#" * filled + "-" * (30 - filled)
                    sys.stdout.write(f"\r    [{bar}] {pct:.0f}%  {done/1e6:.1f}/{total/1e6:.1f} MB")
                    sys.stdout.flush()
        sys.stdout.write("\n")
        os.rename(tmp, dest)
    except Exception as exc:
        if os.path.exists(tmp):
            os.remove(tmp)
        print(f"\n  ERROR: could not download {url}: {exc}")
        sys.exit(1)
    _verify_download(url, dest)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Resource extraction
# ─────────────────────────────────────────────────────────────────────────────

def _find_installed_android_balatro_apk():
    """Return the installed official Android base APK path when Termux can see it."""
    if not IS_TERMUX:
        return None

    pm = "/system/bin/pm"
    if not os.path.exists(pm):
        return None

    result = subprocess.run(
        [pm, "path", OFFICIAL_ANDROID_PACKAGE],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if line.startswith("package:") and line.endswith("/base.apk"):
            path = line[len("package:"):].strip()
            if os.path.exists(path):
                return path
    return None


def _find_extracted_source_folder(game_files_dir, folder):
    """Find a desktop/LÖVE or official Android APK resource folder."""
    source_options = (
        os.path.join(game_files_dir, folder),
        os.path.join(game_files_dir, "assets", folder),
    )
    for source in source_options:
        if os.path.exists(source):
            return source
    return None


def setup_resources(balatro_path=None):
    """Extract resources and localization from the Balatro game file into src/."""
    script_dir      = os.path.dirname(os.path.abspath(__file__))
    game_files_dir  = os.path.join(script_dir, "game_original_files")
    src_dir         = os.path.join(script_dir, "src")

    if not balatro_path:
        balatro_path = _find_installed_android_balatro_apk()
        if balatro_path:
            print()
            print("  Detected installed official Android Balatro - using its base APK.")

    if not balatro_path:
        print()
        print("  Path to Balatro game file:")
        print("    Windows  D:\\Steam\\steamapps\\common\\Balatro\\Balatro.exe")
        print("    Linux    ~/.steam/steam/steamapps/common/Balatro/Balatro.exe")
        print("    macOS    ~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.app/Contents/Resources/Balatro.love")
        print("             (you can also pass the .app bundle path - it will be found automatically)")
        print("    Android  official Balatro base.apk copied from the Play install")
        balatro_path = input("  > ").strip().strip('"').strip("'")

    balatro_path = os.path.expanduser(balatro_path)

    if os.path.isdir(balatro_path) and balatro_path.rstrip("/").endswith(".app"):
        love_path = os.path.join(balatro_path, "Contents", "Resources", "Balatro.love")
        if os.path.exists(love_path):
            print("  Detected macOS app bundle - using Balatro.love inside it.")
            balatro_path = love_path

    if not os.path.exists(balatro_path):
        print(f"  ERROR: File not found: {balatro_path}")
        sys.exit(1)

    print(f"  Extracting {os.path.basename(balatro_path)} ...")
    if os.path.exists(game_files_dir):
        shutil.rmtree(game_files_dir)
    os.makedirs(game_files_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(balatro_path, "r") as z:
            z.extractall(game_files_dir)
    except zipfile.BadZipFile:
        print("  ERROR: Not a valid ZIP/exe file.")
        sys.exit(1)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        sys.exit(1)

    for folder in ("resources", "localization"):
        src = _find_extracted_source_folder(game_files_dir, folder)
        dst = os.path.join(src_dir, folder)
        if not src:
            print(f"  ERROR: '{folder}' not found inside Balatro game file - wrong file?")
            sys.exit(1)
        print(f"  Copying {folder} ...")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    print("  Done - resources ready.")


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Game.love build
# ─────────────────────────────────────────────────────────────────────────────

def _file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sources_changed(src_dir, output_file):
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cache = json.load(f)
        except Exception:
            pass

    current = {}
    for root, _, files in os.walk(src_dir):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                current[fp] = _file_hash(fp)
            except Exception:
                current[fp] = str(os.path.getmtime(fp))

    unchanged = os.path.exists(output_file) and current == cache.get("files", {})
    return not unchanged, current


def _apply_crt_patch(src_dir, apply):
    game_lua = os.path.join(src_dir, "game.lua")
    if not os.path.exists(game_lua):
        return
    with open(game_lua, "r", encoding="utf-8") as f:
        content = f.read()
    if apply:
        if CRT_PATCH_MODIFIED in content:
            return
        if CRT_PATCH_ORIGINAL not in content:
            print("  Warning: CRT patch target not found in game.lua - skipping.")
            return
        content = content.replace(CRT_PATCH_ORIGINAL, CRT_PATCH_MODIFIED)
        print("  CRT shader disabled for all portrait modes.")
    else:
        if CRT_PATCH_ORIGINAL in content:
            return
        content = content.replace(CRT_PATCH_MODIFIED, CRT_PATCH_ORIGINAL)
    with open(game_lua, "w", encoding="utf-8") as f:
        f.write(content)


def _apply_crt_slider_mask_patch(src_dir):
    crt_shader = os.path.join(src_dir, "resources", "shaders", "CRT.fs")
    if not os.path.exists(crt_shader):
        return
    with open(crt_shader, "r", encoding="utf-8") as f:
        content = f.read()
    changed = False
    if CRT_MASK_MODIFIED not in content:
        if CRT_MASK_ORIGINAL not in content:
            print("  Warning: CRT slider mask patch target not found in CRT.fs - skipping.")
        else:
            content = content.replace(CRT_MASK_ORIGINAL, CRT_MASK_MODIFIED)
            changed = True
            print("  CRT edge mask now follows the CRT slider.")

    restored_noise = 0
    for original, replacement in CRT_NOISE_COMMENTED_LINES:
        if original in content:
            content = content.replace(original, replacement)
            restored_noise += 1

    if restored_noise:
        changed = True
        print("  Android CRT shader noise uniform restored.")

    if not changed:
        return

    if restored_noise and restored_noise != len(CRT_NOISE_COMMENTED_LINES):
        print("  Warning: Android CRT shader noise patch only partially applied.")

    with open(crt_shader, "w", encoding="utf-8") as f:
        f.write(content)


def _apply_readabletro(src_dir, apply):
    font_src        = os.path.join("patches", "readabletro", "fonts", "TypoQuik-Bold.ttf")
    font_dst        = os.path.join(src_dir, "resources", "fonts", "TypoQuik-Bold.ttf")
    shader_src_dir  = os.path.join("patches", "readabletro", "shaders")
    shader_dst_dir  = os.path.join(src_dir, "resources", "shaders")
    texture_src_dir = os.path.join("patches", "readabletro", "textures", "2x")
    texture_dst_dir = os.path.join(src_dir, "resources", "textures", "2x")

    if apply:
        for rel, pairs in READABLETRO_LUA_PATCHES.items():
            fp = os.path.join(src_dir, rel)
            if not os.path.exists(fp):
                continue
            shutil.copy2(fp, fp + ".bak")
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            for orig, mod in pairs:
                content = content.replace(orig, mod)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)

        if os.path.exists(font_src):
            os.makedirs(os.path.dirname(font_dst), exist_ok=True)
            shutil.copy2(font_src, font_dst)

        os.makedirs(shader_dst_dir, exist_ok=True)
        for shader in ("background.fs", "splash.fs"):
            s_src = os.path.join(shader_src_dir, shader)
            s_dst = os.path.join(shader_dst_dir, shader)
            if os.path.exists(s_dst):
                shutil.copy2(s_dst, s_dst + ".bak")
            if os.path.exists(s_src):
                shutil.copy2(s_src, s_dst)

        tex_count = 0
        if os.path.isdir(texture_src_dir):
            os.makedirs(texture_dst_dir, exist_ok=True)
            for fn in os.listdir(texture_src_dir):
                if not fn.endswith(".png"):
                    continue
                t_src = os.path.join(texture_src_dir, fn)
                t_dst = os.path.join(texture_dst_dir, fn)
                if os.path.exists(t_dst):
                    shutil.copy2(t_dst, t_dst + ".bak")
                shutil.copy2(t_src, t_dst)
                tex_count += 1
        print(f"  Readabletro applied ({tex_count} textures).")

    else:
        for rel in READABLETRO_LUA_PATCHES:
            fp  = os.path.join(src_dir, rel)
            bak = fp + ".bak"
            if os.path.exists(bak):
                shutil.copy2(bak, fp)
                os.remove(bak)
        if os.path.exists(font_dst):
            os.remove(font_dst)
        for shader in ("background.fs", "splash.fs"):
            s_dst = os.path.join(shader_dst_dir, shader)
            bak   = s_dst + ".bak"
            if os.path.exists(bak):
                shutil.copy2(bak, s_dst)
                os.remove(bak)
        if os.path.isdir(texture_dst_dir):
            for fn in os.listdir(texture_dst_dir):
                if fn.endswith(".bak"):
                    orig = os.path.join(texture_dst_dir, fn[:-4])
                    shutil.copy2(os.path.join(texture_dst_dir, fn), orig)
                    os.remove(os.path.join(texture_dst_dir, fn))


def build_game_love(apply_crt=False, apply_readabletro=False, force=False, import_saves=None):
    """Package src/ into Game.love."""
    src_dir     = "src"
    output_file = "Game.love"

    if not os.path.exists(src_dir):
        print("  ERROR: src/ not found.")
        sys.exit(1)

    if apply_crt:
        _apply_crt_patch(src_dir, apply=True)
    _apply_crt_slider_mask_patch(src_dir)
    if apply_readabletro:
        _apply_readabletro(src_dir, apply=True)

    changed, current_files = _sources_changed(src_dir, output_file)

    if not force and not changed:
        print("  No source changes - skipping rebuild.")
        if apply_crt:
            _apply_crt_patch(src_dir, apply=False)
        if apply_readabletro:
            _apply_readabletro(src_dir, apply=False)
        return

    with open(CACHE_FILE, "w") as f:
        json.dump({"files": current_files}, f, indent=2)

    if os.path.exists(output_file):
        os.remove(output_file)

    def _skip(path):
        return any(p in path for p in GAME_LOVE_EXCLUDE)

    # Lovely-injector regex patches anchor on '\n' newlines. If a Lua source has
    # CRLF (e.g. Windows autocrlf checkout), some SMODS regex patches fail to match
    # and leave behind dangling original code that creates Lua syntax errors at runtime
    # (observed: "ambiguous syntax (function call x new statement)" near the leftover
    # `(k==6 or k ==16 ...)` block in create_UIBox_your_collection_blinds).
    # Normalize all packaged Lua files to LF so patches apply correctly.
    count = 0
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not _skip(os.path.join(root, d))]
            for fn in files:
                if _skip(fn):
                    continue
                fp = os.path.join(root, fn)
                arc = os.path.relpath(fp, src_dir)
                if fn.endswith(".lua"):
                    with open(fp, "rb") as f:
                        data = f.read()
                    if b"\r\n" in data:
                        data = data.replace(b"\r\n", b"\n")
                    zf.writestr(arc.replace(os.sep, "/"), data)
                else:
                    zf.write(fp, arc)
                count += 1

        if import_saves:
            for slot, kinds in import_saves.items():
                for kind, data in kinds.items():
                    if kind == "save":
                        continue
                    zf.writestr(f"import_save/{slot}/{kind}.jkr", data)
                    count += 1

    if apply_crt:
        _apply_crt_patch(src_dir, apply=False)
    if apply_readabletro:
        _apply_readabletro(src_dir, apply=False)

    size_mb = os.path.getsize(output_file) / 1_048_576
    print(f"  Game.love built  ({count} files, {size_mb:.2f} MB)")


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — APK build
# ─────────────────────────────────────────────────────────────────────────────

def _setup_jdk():
    global JAVA_BIN
    if IS_TERMUX:
        java = shutil.which("java")
        if not java:
            print("  Java not found - installing Termux native OpenJDK 17 ...")
            _termux_install_packages(["openjdk-17"])
            java = shutil.which("java")
            if not java:
                print("  ERROR: openjdk-17 installed, but 'java' is still not in PATH.")
                sys.exit(1)
        JAVA_BIN = java
        print(f"  Java (Termux native): {JAVA_BIN}")
        return

    archive = os.path.join(WORKDIR, "openjdk.zip" if os.name == "nt" else "openjdk.tar.gz")
    _download(JDK_URL, archive)

    if not os.path.exists(JDK_DIR):
        print("  Extracting JDK ...")
        for item in os.listdir(WORKDIR):
            p = os.path.join(WORKDIR, item)
            if item.startswith("jdk-") and os.path.isdir(p):
                shutil.rmtree(p)
        if os.name == "nt":
            with zipfile.ZipFile(archive) as z:
                z.extractall(WORKDIR)
        else:
            with tarfile.open(archive, "r:gz") as t:
                if hasattr(tarfile, "data_filter"):
                    t.extractall(WORKDIR, filter="data")
                else:
                    t.extractall(WORKDIR)
        for item in os.listdir(WORKDIR):
            if item.startswith("jdk-"):
                shutil.move(os.path.join(WORKDIR, item), JDK_DIR)
                break

    java_exe = "java.exe" if os.name == "nt" else "java"
    for root, _, files in os.walk(JDK_DIR):
        if java_exe in files and "bin" in root:
            JAVA_BIN = os.path.join(root, java_exe)
            if os.name != "nt":
                os.chmod(JAVA_BIN, 0o755)
            break
    print(f"  Java: {JAVA_BIN}")


def _termux_install_packages(packages):
    pkg = shutil.which("pkg")
    if not pkg:
        print("  ERROR: Termux package manager 'pkg' was not found.")
        print("  Install these packages manually, then rerun build.py:")
        print(f"    pkg install {' '.join(packages)}")
        sys.exit(1)
    print(f"  Installing Termux packages: {' '.join(packages)}")
    result = subprocess.run([pkg, "install", "-y"] + packages)
    if result.returncode != 0:
        print("  ERROR: Termux package install failed.")
        print(f"    command: {pkg} install -y {' '.join(packages)}")
        sys.exit(1)


def _ensure_termux_command(command, package):
    tool = shutil.which(command)
    if tool:
        return tool
    _termux_install_packages([package])
    tool = shutil.which(command)
    if not tool:
        print(f"  ERROR: '{command}' was not found after installing '{package}'.")
        sys.exit(1)
    return tool


def _run_checked(command, cwd, label):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {label} failed.")
        print(f"    command: {' '.join(command)}")
        if result.stdout:
            print(f"  STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"  STDERR:\n{result.stderr}")
        sys.exit(1)


def _java(jar, args):
    result = subprocess.run([JAVA_BIN, "-jar", jar] + args, cwd=WORKDIR,
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR:\n{result.stderr}")
        sys.exit(1)


def _setup_termux_aapt2():
    """Download ReVanced's native ARM aapt2 and return its path. The apktool jar
    only ships an x86-64 aapt2, which can't run on Android, so on Termux we hand
    apktool a native aapt2 via --use-aapt2 -a. Only the build (`b`) step needs it."""
    machine = platform.machine().lower()
    asset = "aapt2-arm64-v8a" if machine in ("aarch64", "arm64") else "aapt2-armeabi-v7a"
    dest = os.path.join(WORKDIR, asset)
    _download(REVANCED_AAPT2_BASE + asset, dest)
    try:
        os.chmod(dest, 0o755)
    except OSError:
        pass
    return dest


def _ensure_debug_keystore():
    keystore = os.path.join(WORKDIR, "debug.keystore")
    if os.path.exists(keystore):
        return keystore
    keytool = shutil.which("keytool")
    if not keytool:
        print("  ERROR: keytool not found after Java setup.")
        sys.exit(1)
    _run_checked([
        keytool,
        "-genkeypair",
        "-keystore", "debug.keystore",
        "-storepass", "android",
        "-keypass", "android",
        "-alias", "androiddebugkey",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000",
        "-dname", "CN=Android Debug,O=Android,C=US",
        "-noprompt",
    ], WORKDIR, "debug keystore creation")
    return keystore


def _sign_apk(signer):
    if not IS_TERMUX:
        _java(signer, ["-a", "balatro.apk"])
        return

    apksigner = _ensure_termux_command("apksigner", "apksigner")
    _ensure_debug_keystore()

    aligned = os.path.join(WORKDIR, "balatro-aligned.apk")
    signed = os.path.join(WORKDIR, "balatro-aligned-debugSigned.apk")
    for path in (aligned, signed):
        if os.path.exists(path):
            os.remove(path)

    sign_input = "balatro.apk"
    zipalign = shutil.which("zipalign")
    if zipalign:
        _run_checked([
            zipalign,
            "-p",
            "-f",
            "4",
            "balatro.apk",
            "balatro-aligned.apk",
        ], WORKDIR, "zipalign")
        sign_input = "balatro-aligned.apk"
    else:
        print("  zipalign not found in Termux - signing APK without zipalign.")

    _run_checked([
        apksigner,
        "sign",
        "--ks", "debug.keystore",
        "--ks-pass", "pass:android",
        "--key-pass", "pass:android",
        "--out", "balatro-aligned-debugSigned.apk",
        sign_input,
    ], WORKDIR, "apksigner")


def _apktool(jar, args):
    """Run apktool. The apktool jar's bundled aapt binaries are x86-64 only, so
    on Termux/Android one of two known-good setups is used:

      A) a Termux-native apktool already in PATH (e.g. rendiix/termux-apktool),
         which ships its own ARM aapt — run as-is, no --use-aapt2 needed;
      B) otherwise the bundled ibotpeaches apktool jar driven by Termux's native
         Java, with ReVanced's ARM aapt2 (downloaded automatically) passed via
         --use-aapt2 -a. This needs no manual apktool install at all.
    """
    if IS_TERMUX:
        tool = shutil.which("apktool")
        if tool:
            # Setup A: native apktool brings its own ARM aapt; don't override it.
            result = subprocess.run([tool] + list(args), cwd=WORKDIR,
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print("  ERROR: apktool failed.")
                print(f"    command: {tool} {' '.join(args)}")
                if result.stdout:
                    print(f"  STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"  STDERR:\n{result.stderr}")
                sys.exit(1)
            return

        # Setup B: bundled apktool jar + downloaded ARM aapt2 (build step only).
        termux_args = list(args)
        if termux_args and termux_args[0] == "b":
            aapt2 = _setup_termux_aapt2()
            termux_args = ["b", "--use-aapt2", "-a", aapt2] + termux_args[1:]
        _java(jar, termux_args)
        return
    _java(jar, args)


def _patch_sdl_portrait_orientation(apk_out):
    smali_path = os.path.join(apk_out, "smali", "org", "libsdl", "app", "SDLActivity.smali")
    if not os.path.exists(smali_path):
        raise FileNotFoundError(f"SDLActivity.smali not found at {smali_path}")

    with open(smali_path, "r", encoding="utf-8") as f:
        smali = f.read()

    marker = "# Balatro Portrait: force portrait orientation"
    if marker in smali:
        return

    signature = ".method public setOrientationBis(IIZLjava/lang/String;)V"
    method_start = smali.find(signature)
    if method_start == -1:
        raise RuntimeError(f"{signature} not found in {smali_path}")

    method_end = smali.find(".end method", method_start)
    if method_end == -1:
        raise RuntimeError(f"{signature} has no .end method in {smali_path}")

    method_body = smali[method_start:method_end]
    header_match = re.search(r"(?m)^(\s+\.(?:locals|registers)\s+\d+\s*)$", method_body)
    if not header_match:
        raise RuntimeError(f"{signature} has no .locals/.registers header in {smali_path}")

    insert_at = method_start + header_match.end()
    injected = (
        "\n"
        f"    {marker}\n"
        "    const/4 p1, 0x1\n"
        "    invoke-virtual {p0, p1}, Landroid/app/Activity;->setRequestedOrientation(I)V\n"
        "    return-void\n"
    )
    smali = smali[:insert_at] + injected + smali[insert_at:]

    with open(smali_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(smali)


def build_apk(profiler=None):
    """Download tools, package, and sign the always-Lovely Android APK."""
    game_love_src = os.path.abspath("Game.love")
    if not os.path.exists(game_love_src):
        print("  ERROR: Game.love not found - run the build step first.")
        sys.exit(1)

    os.makedirs(WORKDIR, exist_ok=True)
    p = profiler or BuildProfiler()

    apk_fn  = "lovely-base.apk"
    apk_url = LOVELY_APK_URL

    apktool   = os.path.join(WORKDIR, "apktool.jar")
    signer    = os.path.join(WORKDIR, "uber-apk-signer.jar")
    patch_zip = os.path.join(WORKDIR, "Balatro-APK-Patch.zip")
    base_apk  = os.path.join(WORKDIR, apk_fn)

    with p.step("JDK setup"):
        _setup_jdk()

    with p.step("Download tools"):
        # apktool.jar is always fetched: on Termux it's the "setup B" fallback
        # (bundled jar + ReVanced aapt2) when no native apktool is in PATH, and
        # it's harmless if an in-PATH apktool ends up being used instead.
        downloads = [(APKTOOL_URL, apktool), (SIGNER_URL, signer),
                     (PATCH_URL, patch_zip), (apk_url, base_apk)]
        for url, dest in downloads:
            _download(url, dest)

    apk_out = os.path.join(WORKDIR, "balatro-apk")
    with p.step("Unpack APK"):
        if os.path.exists(apk_out):
            shutil.rmtree(apk_out)
        print("  Unpacking APK ...")
        _apktool(apktool, ["d", "-o", "balatro-apk", apk_fn])

    with p.step("Patch manifest"):
        patch_dir = os.path.join(WORKDIR, "Balatro-APK-Patch")
        if os.path.exists(patch_dir):
            shutil.rmtree(patch_dir)
        with zipfile.ZipFile(patch_zip) as z:
            z.extractall(WORKDIR)

        manifest_path = os.path.join(apk_out, "AndroidManifest.xml")

        with open(manifest_path) as f:
            m = f.read()
        m = m.replace("systems.shorty.lmm", "com.unofficial.balatro")
        m = re.sub(r'android:label="[^"]+"',         'android:label="Balatro"',          m)
        m = re.sub(r'android:versionCode="[^"]+"',   f'android:versionCode="{int(time.time())}"', m)
        m = re.sub(r'android:versionName="[^"]+"',   f'android:versionName="{MOD_VERSION}-lovely"', m)
        m = re.sub(r'\sandroid:debuggable="[^"]+"',  "",                                  m)
        m = re.sub(r'android:screenOrientation="[^"]+"', 'android:screenOrientation="portrait"', m)
        m = re.sub(r'android:configChanges="[^"]+"',
                   'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|uiMode|keyboard|keyboardHidden|navigation"', m)
        with open(manifest_path, "w") as f:
            f.write(m)
        print("  [Lovely] Manifest patched.")

        _patch_sdl_portrait_orientation(apk_out)
        print("  [Lovely] SDL orientation patched.")

        # Icons
        for density in ["hdpi","mdpi","xhdpi","xxhdpi","xxxhdpi"]:
            src = os.path.join(WORKDIR, "res", f"drawable-{density}", "love.png")
            dst = os.path.join(apk_out,  "res", f"drawable-{density}", "love.png")
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)

        # Game.love
        game_dst = os.path.join(apk_out, "assets", "game.love")
        os.makedirs(os.path.dirname(game_dst), exist_ok=True)
        shutil.copy(game_love_src, game_dst)

    with p.step("Repack APK"):
        print("  Repacking APK ...")
        _apktool(apktool, ["b", "-o", "balatro.apk", "balatro-apk"])

    with p.step("Sign APK"):
        print("  Signing APK ...")
        _sign_apk(signer)

    p.report()
    print(f"\n{'=' * 60}")
    print("  Build complete - MODDED (Lovely)")
    print(f"  APK: balatro-mobile-maker/balatro-aligned-debugSigned.apk")
    print(f"{'=' * 60}")

    print()
    print("  Mod installation:")
    print("  1. Launch the game once")
    print("  2. Put mod folders in ASET/Mods/")
    print("  3. Restart the game")
    print("  See docs/MODDING.md for no-root, root, and ADB paths.")


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — iOS IPA build (experimental)
# ─────────────────────────────────────────────────────────────────────────────

def build_ipa(profiler=None):
    """Package Game.love into an unsigned, portrait-locked iOS .ipa.

    The base is a prebuilt LOVE iOS app shell (no game data). We rewrite the
    archive instead of appending so Info.plist can be replaced: orientation is
    locked to portrait and the bundle version is set to MOD_VERSION. The IPA is
    unsigned by design — Sideloadly/AltStore re-sign it at install time.
    """
    game_love_src = os.path.abspath("Game.love")
    if not os.path.exists(game_love_src):
        print("  ERROR: Game.love not found - run the build step first.")
        sys.exit(1)

    os.makedirs(WORKDIR, exist_ok=True)
    p = profiler or BuildProfiler()

    base_ipa  = os.path.join(WORKDIR, "balatro-base.ipa")
    out_ipa   = "balatro-portrait.ipa"
    plist_arc = "Payload/Balatro.app/Info.plist"
    love_arc  = "Payload/Balatro.app/game.love"

    with p.step("Download iOS base"):
        _download(IOS_BASE_URL, base_ipa)

    with p.step("Pack IPA"):
        print("  Packing IPA (portrait-locked Info.plist + game.love) ...")
        if os.path.exists(out_ipa):
            os.remove(out_ipa)
        with zipfile.ZipFile(base_ipa, "r") as zin, \
             zipfile.ZipFile(out_ipa, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in (plist_arc, love_arc):
                    continue
                # passing the original ZipInfo preserves unix permissions on
                # the Balatro executable inside the .app bundle
                zout.writestr(item, zin.read(item.filename))

            plist = plistlib.loads(zin.read(plist_arc))
            plist["UISupportedInterfaceOrientations"] = ["UIInterfaceOrientationPortrait"]
            plist["UISupportedInterfaceOrientations~ipad"] = ["UIInterfaceOrientationPortrait"]
            plist["CFBundleShortVersionString"] = MOD_VERSION
            plist["CFBundleVersion"] = MOD_VERSION
            zout.writestr(plist_arc, plistlib.dumps(plist))

            zout.write(game_love_src, love_arc)

    p.report()
    size_mb = os.path.getsize(out_ipa) / 1_048_576
    print(f"\n{'=' * 60}")
    print("  iOS build complete - EXPERIMENTAL (untested by maintainer)")
    print(f"  IPA: {out_ipa}  ({size_mb:.2f} MB)")
    print(f"{'=' * 60}")
    print()
    print("  Sideload with Sideloadly or AltStore (signs with your Apple ID).")
    print("  Lovely mod support is Android-only; the IPA is always vanilla.")
    print("  See docs/IOS.md for instructions - and please report results!")


# ─────────────────────────────────────────────────────────────────────────────
# CLI flag parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args():
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Balatro Portrait Mobile - unified build script "
                    "(resource extraction, Game.love creation, APK packaging).",
    )
    crt = parser.add_mutually_exclusive_group()
    crt.add_argument("--crt",    dest="crt", action="store_true",  default=None,
                     help="apply the CRT-disabling portrait patch")
    crt.add_argument("--no-crt", dest="crt", action="store_false",
                     help="keep the CRT shader unchanged (default)")

    rdb = parser.add_mutually_exclusive_group()
    rdb.add_argument("--readabletro",    dest="readabletro", action="store_true", default=None,
                     help="apply Readabletro font and high-res texture patch (default)")
    rdb.add_argument("--no-readabletro", dest="readabletro", action="store_false",
                     help="skip Readabletro patch")

    ios = parser.add_mutually_exclusive_group()
    ios.add_argument("--ios",    dest="ios", action="store_true", default=None,
                     help="also build an iOS .ipa for sideloading (EXPERIMENTAL)")
    ios.add_argument("--no-ios", dest="ios", action="store_false",
                     help="skip the iOS build (default)")

    parser.add_argument("--balatro", dest="balatro_path", metavar="PATH",
                        help="path to the Balatro game file (skips the interactive prompt)")
    parser.add_argument("--skip-setup", action="store_true",
                        help="skip resource extraction (if src/resources already exists)")
    parser.add_argument("--skip-apk", action="store_true",
                        help="only build Game.love, skip APK packaging")
    parser.add_argument("--force", action="store_true",
                        help="force Game.love rebuild even if sources are unchanged")
    parser.add_argument("--import-save", dest="import_save", metavar="PATH",
                        help="bake a desktop Balatro save folder or Takeout zip into the APK")
    parser.add_argument("--version", action="version", version=f"%(prog)s {MOD_VERSION}")

    ns = parser.parse_args()
    flags = {k: v for k, v in vars(ns).items() if v is not None}
    return flags


def _load_collect_saves():
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "import_save.py")
    spec = importlib.util.spec_from_file_location("import_save", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.collect_saves


def _resolve_import_save(flag_path, interactive):
    """Return {slot: {kind: bytes}} of progression saves to bake in, or None."""
    path = flag_path
    if path is None and interactive:
        print()
        print("  Import an existing save (optional)")
        print("     Bring your unlocks and progression from desktop Balatro or the")
        print("     official Play Store app (via Google Takeout). Leave blank to skip.")
        guess = os.path.join(os.environ["APPDATA"], "Balatro") if os.environ.get("APPDATA") else None
        if guess and os.path.isdir(guess):
            print(f"     Detected desktop save: {guess}")
        try:
            path = input("     Save folder or Takeout zip (blank = skip): ").strip().strip('"')
        except EOFError:
            path = ""
    if not path:
        return None

    try:
        saves = _load_collect_saves()(path)
    except Exception as exc:
        print(f"  Save import skipped: {exc}")
        return None

    # Progression only (meta/profile/unlock_notify); an in-progress run is not
    # carried over, matching the documented transfer.
    cleaned = {}
    for slot, kinds in saves.items():
        keep = {k: v for k, v in kinds.items() if k != "save"}
        if keep:
            cleaned[slot] = keep
    if not cleaned:
        print("  Save import: no profile data found in that source.")
        return None
    print("  Save import: baking " + ", ".join(f"profile {s}" for s in sorted(cleaned)) + " into the build.")
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  BALATRO PORTRAIT MOBILE - BUILD")
    print("=" * 60)

    cli = _parse_args()
    all_cli_set = all(k in cli for k in ("crt", "readabletro", "ios"))

    # ── Load or collect config ──────────────────────────────────────────────
    config = {}
    if not all_cli_set:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    config = json.load(f)
                print()
                print("  Saved settings:")
                print(f"    CRT patch (desktop portrait):  {'yes' if config.get('crt') else 'no'}")
                print(f"    Readabletro:                   {'yes' if config.get('readabletro') else 'no'}")
                print("    Lovely mod support:            yes (always on for Android)")
                print(f"    iOS .ipa (experimental):       {'yes' if config.get('ios') else 'no'}")
                print()
                if not _ask("  Use these settings?", default=True):
                    config = {}
            except Exception:
                config = {}

        if not config:
            print()
            print("  -- Build options --------------------------------------")
            print()
            print("  1. CRT Shader Patch")
            print("     On some devices the CRT shader causes visual artifacts in")
            print("     portrait mode: a black ellipse or a thin colored sliver at")
            print("     the bottom of the screen. Enable this to disable CRT and")
            print("     fix those issues. If your game looks fine, skip it.")
            config["crt"] = _ask("     Apply CRT patch?", default=DEFAULT_BUILD_CONFIG["crt"])
            print()
            print("  2. Readabletro")
            print("     Replaces the pixel font with TypoQuik-Bold and adds")
            print("     high-resolution card and UI textures.")
            config["readabletro"] = _ask("     Apply Readabletro?", default=DEFAULT_BUILD_CONFIG["readabletro"])
            print()
            print("  3. iOS Build (EXPERIMENTAL)")
            print("     Also produces balatro-portrait.ipa for sideloading with")
            print("     Sideloadly or AltStore. Untested by the maintainer -")
            print("     feedback welcome. Lovely is not available on iOS.")
            config["ios"] = _ask("     Build iOS .ipa?", default=DEFAULT_BUILD_CONFIG["ios"])
            print()
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            print("  Settings saved to .buildconfig.json")

    apply_crt         = cli.get("crt",          config.get("crt",         DEFAULT_BUILD_CONFIG["crt"]))
    apply_readabletro = cli.get("readabletro",   config.get("readabletro", DEFAULT_BUILD_CONFIG["readabletro"]))
    build_ios         = cli.get("ios",           config.get("ios",         DEFAULT_BUILD_CONFIG["ios"]))
    balatro_path      = cli.get("balatro_path",  None)
    force             = cli.get("force",         False)
    import_saves      = _resolve_import_save(
        cli.get("import_save"),
        interactive=("import_save" not in cli and not all_cli_set),
    )

    total = 4 if build_ios else 3

    # ── Step 1 — Resources ──────────────────────────────────────────────────
    needs_setup = not os.path.exists(os.path.join("src", "resources"))
    print()
    if cli.get("skip_setup"):
        print(f"[1/{total}] Skipping resource setup (--skip-setup).")
    elif needs_setup:
        print(f"[1/{total}] Game resources not found - extracting from Balatro.exe ...")
        setup_resources(balatro_path)
    else:
        print(f"[1/{total}] Resources already present.")

    # ── Step 2 — Game.love ─────────────────────────────────────────────────
    print()
    print(f"[2/{total}] Building Game.love ...")
    build_game_love(apply_crt=apply_crt, apply_readabletro=apply_readabletro,
                    force=force or bool(import_saves), import_saves=import_saves)

    # ── Step 3 — APK ───────────────────────────────────────────────────────
    if cli.get("skip_apk"):
        print()
        print(f"[3/{total}] Skipping APK build (--skip-apk).")
    else:
        print()
        print(f"[3/{total}] Building APK ...")
        build_apk(profiler=BuildProfiler())

        print()
        print("  Install on device:")
        print("    adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk")

    # ── Step 4 — iOS IPA (experimental) ────────────────────────────────────
    if build_ios:
        print()
        print(f"[4/{total}] Building iOS IPA (experimental) ...")
        build_ipa(profiler=BuildProfiler())


if __name__ == "__main__":
    main()
