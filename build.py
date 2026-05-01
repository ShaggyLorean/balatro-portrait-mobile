#!/usr/bin/env python3
"""
Balatro Portrait Mobile - Unified Build Script

Handles everything: resource extraction, Game.love creation, and APK packaging.

Usage:
    python build.py [options]

Options:
    --crt                 Disable CRT shader for all portrait modes
                          (Android disables it automatically; this also covers desktop)
    --no-crt              Keep CRT shader enabled
    --readabletro         Apply Readabletro font and high-res texture patch
    --no-readabletro      Skip Readabletro patch
    --with-lovely         Build with Lovely mod support embedded
    --no-lovely           Build vanilla (no mod support)
    --balatro PATH        Path to Balatro.exe (skips the interactive prompt)
    --skip-setup          Skip resource extraction (if src/resources already exists)
    --skip-apk            Only build Game.love, skip APK packaging
    --force               Force Game.love rebuild even if sources are unchanged
"""

import hashlib
import json
import os
import platform
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

CONFIG_FILE = ".buildconfig.json"
CACHE_FILE  = ".build_cache.json"

WORKDIR  = os.path.abspath("balatro-mobile-maker")
JDK_DIR  = os.path.join(WORKDIR, "jdk")
JAVA_BIN = os.path.join(JDK_DIR, "bin", "java")  # resolved after JDK extraction

if os.name == "nt":
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-windows-x64.zip"
elif platform.system() == "Darwin":
    JDK_URL = (
        "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-aarch64.tar.gz"
        if platform.machine() == "arm64"
        else "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-x64.tar.gz"
    )
else:
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-linux-x64.tar.gz"

APKTOOL_URL    = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
SIGNER_URL     = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
PATCH_URL      = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/Balatro-APK-Patch.zip"
LOVE_APK_URL   = "https://github.com/love2d/love-android/releases/download/11.5a/love-11.5-android-embed.apk"
LOVELY_APK_URL = "https://lmm.shorty.systems/base.apk"

# These strings must match exactly what's in src/game.lua
CRT_PATCH_ORIGINAL = 'if (not G.recording_mode or G.video_control) and not G.F_NO_CRT then'
CRT_PATCH_MODIFIED = 'if (not G.recording_mode or G.video_control) and not G.F_NO_CRT and not G.F_PORTRAIT then'

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
    "main.lua": [
        (
            'local font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 20)',
            'local font = love.graphics.setNewFont("resources/fonts/TypoQuik-Bold.ttf", 20)',
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
        r = input(f"{prompt}{hint}: ").strip().lower()
        if not r and default is not None:
            return default
        if r in ("y", "yes"):
            return True
        if r in ("n", "no"):
            return False
        print("  Please enter y or n.")


def _download(url, dest):
    if os.path.exists(dest):
        print(f"  Already downloaded: {os.path.basename(dest)}")
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


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Resource extraction
# ─────────────────────────────────────────────────────────────────────────────

def setup_resources(balatro_path=None):
    """Extract resources and localization from Balatro.exe into src/."""
    script_dir      = os.path.dirname(os.path.abspath(__file__))
    game_files_dir  = os.path.join(script_dir, "game_original_files")
    src_dir         = os.path.join(script_dir, "src")

    if not balatro_path:
        print()
        print("  Path to Balatro.exe:")
        print("    Windows  D:\\Steam\\steamapps\\common\\Balatro\\Balatro.exe")
        print("    Linux    ~/.steam/steam/steamapps/common/Balatro/Balatro.exe")
        print("    macOS    ~/Library/Application Support/Steam/steamapps/common/Balatro/Balatro.exe")
        balatro_path = input("  > ").strip().strip('"').strip("'")

    if not os.path.exists(balatro_path):
        print(f"  ERROR: File not found: {balatro_path}")
        sys.exit(1)

    print(f"  Extracting {os.path.basename(balatro_path)} ...")
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
        src = os.path.join(game_files_dir, folder)
        dst = os.path.join(src_dir, folder)
        if not os.path.exists(src):
            print(f"  ERROR: '{folder}' not found inside Balatro.exe — wrong file?")
            sys.exit(1)
        print(f"  Copying {folder} ...")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    print("  Done — resources ready.")


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
            print("  Warning: CRT patch target not found in game.lua — skipping.")
            return
        content = content.replace(CRT_PATCH_ORIGINAL, CRT_PATCH_MODIFIED)
        print("  CRT shader disabled for all portrait modes.")
    else:
        if CRT_PATCH_ORIGINAL in content:
            return
        content = content.replace(CRT_PATCH_MODIFIED, CRT_PATCH_ORIGINAL)
    with open(game_lua, "w", encoding="utf-8") as f:
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


def build_game_love(apply_crt=False, apply_readabletro=False, force=False):
    """Package src/ into Game.love."""
    src_dir     = "src"
    output_file = "Game.love"

    if not os.path.exists(src_dir):
        print("  ERROR: src/ not found.")
        sys.exit(1)

    if apply_crt:
        _apply_crt_patch(src_dir, apply=True)
    if apply_readabletro:
        _apply_readabletro(src_dir, apply=True)

    changed, current_files = _sources_changed(src_dir, output_file)

    if not force and not changed:
        print("  No source changes — skipping rebuild.")
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

    count = 0
    with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not _skip(os.path.join(root, d))]
            for fn in files:
                if _skip(fn):
                    continue
                fp = os.path.join(root, fn)
                zf.write(fp, os.path.relpath(fp, src_dir))
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
                t.extractall(WORKDIR)
        for item in os.listdir(WORKDIR):
            if item.startswith("jdk-"):
                shutil.move(os.path.join(WORKDIR, item), JDK_DIR)
                break

    global JAVA_BIN
    java_exe = "java.exe" if os.name == "nt" else "java"
    for root, _, files in os.walk(JDK_DIR):
        if java_exe in files and "bin" in root:
            JAVA_BIN = os.path.join(root, java_exe)
            if os.name != "nt":
                os.chmod(JAVA_BIN, 0o755)
            break
    print(f"  Java: {JAVA_BIN}")


def _java(jar, args):
    result = subprocess.run([JAVA_BIN, "-jar", jar] + args, cwd=WORKDIR,
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR:\n{result.stderr}")
        sys.exit(1)


def build_apk(use_lovely=False, profiler=None):
    """Download tools, package, and sign the APK."""
    game_love_src = os.path.abspath("Game.love")
    if not os.path.exists(game_love_src):
        print("  ERROR: Game.love not found — run the build step first.")
        sys.exit(1)

    os.makedirs(WORKDIR, exist_ok=True)
    p = profiler or BuildProfiler()

    apk_fn  = "lovely-base.apk" if use_lovely else "love-11.5-android-embed.apk"
    apk_url = LOVELY_APK_URL    if use_lovely else LOVE_APK_URL

    apktool   = os.path.join(WORKDIR, "apktool.jar")
    signer    = os.path.join(WORKDIR, "uber-apk-signer.jar")
    patch_zip = os.path.join(WORKDIR, "Balatro-APK-Patch.zip")
    base_apk  = os.path.join(WORKDIR, apk_fn)

    with p.step("JDK setup"):
        _setup_jdk()

    with p.step("Download tools"):
        for url, dest in [(APKTOOL_URL, apktool), (SIGNER_URL, signer),
                          (PATCH_URL, patch_zip), (apk_url, base_apk)]:
            _download(url, dest)

    apk_out = os.path.join(WORKDIR, "balatro-apk")
    with p.step("Unpack APK"):
        if os.path.exists(apk_out):
            shutil.rmtree(apk_out)
        print("  Unpacking APK ...")
        _java(apktool, ["d", "-o", "balatro-apk", apk_fn])

    with p.step("Patch manifest"):
        patch_dir = os.path.join(WORKDIR, "Balatro-APK-Patch")
        if os.path.exists(patch_dir):
            shutil.rmtree(patch_dir)
        with zipfile.ZipFile(patch_zip) as z:
            z.extractall(WORKDIR)

        manifest_path = os.path.join(apk_out, "AndroidManifest.xml")

        if use_lovely:
            with open(manifest_path) as f:
                m = f.read()
            m = m.replace("systems.shorty.lmm", "com.unofficial.balatro")
            m = re.sub(r'android:label="[^"]+"',         'android:label="Balatro"',          m)
            m = re.sub(r'\sandroid:debuggable="[^"]+"',  "",                                  m)
            m = re.sub(r'android:screenOrientation="[^"]+"', 'android:screenOrientation="portrait"', m)
            m = re.sub(r'android:configChanges="[^"]+"',
                       'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|uiMode|keyboard|keyboardHidden|navigation"', m)
            with open(manifest_path, "w") as f:
                f.write(m)
            print("  [Lovely] Manifest patched.")
        else:
            shutil.copy(os.path.join(WORKDIR, "AndroidManifest.xml"), manifest_path)
            with open(manifest_path) as f:
                m = f.read()
            m = re.sub(r'android:versionCode="[^"]+"', f'android:versionCode="{int(time.time())}"', m)
            m = re.sub(r'android:versionName="[^"]+"', 'android:versionName="1.0.0n-FULL-p1"',      m)
            for orient in ["landscape","sensorLandscape","userLandscape","reverseLandscape",
                           "fullSensor","sensor","nosensor","unspecified"]:
                m = m.replace(f'screenOrientation="{orient}"', 'screenOrientation="portrait"')
            m = re.sub(r'android:configChanges="[^"]+"',
                       'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|uiMode|keyboard|keyboardHidden|navigation"', m)
            with open(manifest_path, "w") as f:
                f.write(m)
            print("  [Vanilla] Manifest patched — portrait locked.")

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

        # Smali patches (vanilla only — lovely has its own init)
        smali_src = os.path.join(os.getcwd(), "src", "smali")
        if not use_lovely and os.path.exists(smali_src):
            smali_dst = os.path.join(apk_out, "smali")
            for root, _, files in os.walk(smali_src):
                for fn in files:
                    if fn.endswith(".smali"):
                        src_f = os.path.join(root, fn)
                        dst_f = os.path.join(smali_dst, os.path.relpath(src_f, smali_src))
                        os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                        shutil.copy(src_f, dst_f)

    with p.step("Repack APK"):
        print("  Repacking APK ...")
        _java(apktool, ["b", "-o", "balatro.apk", "balatro-apk"])

    with p.step("Sign APK"):
        print("  Signing APK ...")
        _java(signer, ["-a", "balatro.apk"])

    p.report()
    label = "MODDED (Lovely)" if use_lovely else "VANILLA"
    print(f"\n{'=' * 60}")
    print(f"  Build complete — {label}")
    print(f"  APK: balatro-mobile-maker/balatro-aligned-debugSigned.apk")
    print(f"{'=' * 60}")

    if use_lovely:
        print()
        print("  Mod installation (requires root / Magisk):")
        print("  1. Install Material Files from Play Store")
        print("  2. Navigate to:")
        print("       /data/user/0/com.unofficial.balatro/files/save/ASET/Mods/")
        print("  3. Place mod folders there and restart the game")
        print("  See docs/MODDING.md for details.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI flag parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args():
    args = sys.argv[1:]
    flags = {}

    def _flag(pos, neg, key):
        if pos in args:
            flags[key] = True
        elif neg in args:
            flags[key] = False

    _flag("--crt",         "--no-crt",          "crt")
    _flag("--readabletro", "--no-readabletro",   "readabletro")
    _flag("--with-lovely", "--no-lovely",        "lovely")

    if "--balatro" in args:
        i = args.index("--balatro")
        if i + 1 < len(args):
            flags["balatro_path"] = args[i + 1]

    flags["force"]      = "--force"      in args
    flags["skip_setup"] = "--skip-setup" in args
    flags["skip_apk"]   = "--skip-apk"  in args
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  BALATRO PORTRAIT MOBILE - BUILD")
    print("=" * 60)

    cli = _parse_args()
    all_cli_set = all(k in cli for k in ("crt", "readabletro", "lovely"))

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
                print(f"    Lovely mod support:            {'yes' if config.get('lovely') else 'no'}")
                print()
                if not _ask("  Use these settings?", default=True):
                    config = {}
            except Exception:
                config = {}

        if not config:
            print()
            print("  ── Build options ──────────────────────────────────────")
            print()
            print("  1. CRT Shader Patch")
            print("     Android automatically disables CRT (fixes the bottom-edge")
            print("     artifact on tall phones). This option ALSO disables CRT")
            print("     when testing portrait mode on desktop.")
            print("     Skip unless you develop/test on PC.")
            config["crt"] = _ask("     Apply CRT patch?", default=False)
            print()
            print("  2. Readabletro")
            print("     Replaces the pixel font with TypoQuik-Bold and adds")
            print("     high-resolution card and UI textures.")
            config["readabletro"] = _ask("     Apply Readabletro?", default=False)
            print()
            print("  3. Lovely Mod Support")
            print("     Embeds the Lovely runtime so mods (e.g. Steamodded)")
            print("     can be loaded. Requires a rooted device to install mods.")
            config["lovely"] = _ask("     Enable Lovely?", default=True)
            print()
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            print("  Settings saved to .buildconfig.json")

    apply_crt         = cli.get("crt",          config.get("crt",         False))
    apply_readabletro = cli.get("readabletro",   config.get("readabletro", False))
    use_lovely        = cli.get("lovely",        config.get("lovely",      True))
    balatro_path      = cli.get("balatro_path",  None)
    force             = cli.get("force",         False)

    # ── Step 1 — Resources ──────────────────────────────────────────────────
    needs_setup = not os.path.exists(os.path.join("src", "resources"))
    print()
    if cli.get("skip_setup"):
        print("[1/3] Skipping resource setup (--skip-setup).")
    elif needs_setup:
        print("[1/3] Game resources not found — extracting from Balatro.exe ...")
        setup_resources(balatro_path)
    else:
        print("[1/3] Resources already present.")

    # ── Step 2 — Game.love ─────────────────────────────────────────────────
    print()
    print("[2/3] Building Game.love ...")
    build_game_love(apply_crt=apply_crt, apply_readabletro=apply_readabletro, force=force)

    # ── Step 3 — APK ───────────────────────────────────────────────────────
    if cli.get("skip_apk"):
        print()
        print("[3/3] Skipping APK build (--skip-apk).")
        return

    print()
    print("[3/3] Building APK ...")
    build_apk(use_lovely=use_lovely, profiler=BuildProfiler())

    print()
    print("  Install on device:")
    print("    adb install balatro-mobile-maker/balatro-aligned-debugSigned.apk")


if __name__ == "__main__":
    main()
