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
import concurrent.futures


class BuildProfiler:
    def __init__(self):
        self.steps = []
        self._start = time.time()

    def step(self, name):
        return _StepContext(self, name)

    def record(self, name, duration):
        self.steps.append({'name': name, 'duration': duration})

    def print_progress(self, current, total, label):
        bar_len = 40
        filled = int(bar_len * current / total)
        bar = '#' * filled + '-' * (bar_len - filled)
        pct = current / total * 100
        sys.stdout.write('\r  [%s] %.0f%% %s' % (bar, pct, label))
        sys.stdout.flush()

    def report(self):
        total = sum(s['duration'] for s in self.steps)
        wall = time.time() - self._start
        print(f"\n{'=' * 50}")
        print("BUILD TIME REPORT")
        print(f"{'=' * 50}")
        for s in self.steps:
            pct = s['duration'] / total * 100 if total > 0 else 0
            print(f"  {s['name']:<30s} {s['duration']:>6.1f}s  ({pct:>4.0f}%)")
        print(f"  {'TOTAL':<30s} {wall:>6.1f}s")
        print(f"{'=' * 50}")


class _StepContext:
    def __init__(self, profiler, name):
        self.profiler = profiler
        self.name = name

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.profiler.record(self.name, time.time() - self.start)


PROFILER = BuildProfiler()

# Constants
# Detect OS and architecture for appropriate JDK
if os.name == "nt":
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-windows-x64.zip"
elif platform.system() == "Darwin":  # macOS
    # Detect architecture: arm64 for Apple Silicon (M1/M2/M3), x64 for Intel
    if platform.machine() == "arm64":
        JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-aarch64.tar.gz"
    else:
        JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-macos-x64.tar.gz"
else:  # Linux
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-linux-x64.tar.gz"
APKTOOL_URL = (
    "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
)
SIGNER_URL = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
PATCH_URL = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/Balatro-APK-Patch.zip"
LOVE_APK_URL = "https://github.com/love2d/love-android/releases/download/11.5a/love-11.5-android-embed.apk"
LOVELY_APK_URL = "https://lmm.shorty.systems/base.apk"

WORKDIR = os.path.abspath("balatro-mobile-maker")
JDK_DIR = os.path.join(WORKDIR, "jdk")
JAVA_BIN = os.path.join(
    JDK_DIR, "bin", "java"
)  # Will need to find actual path after extraction


def download_file(url, dest):
    if os.path.exists(dest):
        print("File %s already exists. Skipping." % dest)
        return
    print("Downloading %s ..." % url)
    tmp_dest = dest + ".part"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=120)
        total_size = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        block_size = 8192
        with open(tmp_dest, 'wb') as f:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = min(downloaded / total_size * 100, 100)
                    bar_len = 30
                    filled = int(bar_len * pct / 100)
                    bar = '#' * filled + '-' * (bar_len - filled)
                    mb = downloaded / 1024 / 1024
                    total_mb = total_size / 1024 / 1024
                    sys.stdout.write('\r  [%s] %.0f%% (%.1f/%.1f MB)' % (bar, pct, mb, total_mb))
                    sys.stdout.flush()
        sys.stdout.write('\n')
        os.rename(tmp_dest, dest)
        print("Download complete: %s" % os.path.basename(dest))
    except Exception as e:
        if os.path.exists(tmp_dest):
            os.remove(tmp_dest)
        print("\nFailed to download %s: %s" % (url, e))
        exit(1)


def download_all_parallel(downloads):
    for url, dest in downloads:
        download_file(url, dest)


def setup_jdk():
    # Use appropriate archive format for the platform
    if os.name == "nt":
        jdk_archive = os.path.join(WORKDIR, "openjdk.zip")
    else:
        jdk_archive = os.path.join(WORKDIR, "openjdk.tar.gz")
    download_file(JDK_URL, jdk_archive)

    if not os.path.exists(JDK_DIR):
        print("Extracting JDK...")
        # Clean up any partial extraction
        for item in os.listdir(WORKDIR):
            if item.startswith("jdk-"):
                p = os.path.join(WORKDIR, item)
                if os.path.isdir(p):
                    shutil.rmtree(p)

        # Extract based on platform
        if os.name == "nt":
            # Windows: use zipfile
            with zipfile.ZipFile(jdk_archive, 'r') as zip_ref:
                zip_ref.extractall(WORKDIR)
        else:
            # Linux/Mac: use tarfile
            with tarfile.open(jdk_archive, 'r:gz') as tar_ref:
                tar_ref.extractall(WORKDIR)

        # Find the extracted folder (it usually has a versioned name)
        for item in os.listdir(WORKDIR):
            if item.startswith("jdk-"):
                shutil.move(os.path.join(WORKDIR, item), JDK_DIR)
                break

    # Locate java bin
    global JAVA_BIN
    java_name = "java.exe" if os.name == "nt" else "java"
    for root, dirs, files in os.walk(JDK_DIR):
        if java_name in files and "bin" in root:
            JAVA_BIN = os.path.join(root, java_name)
            # Ensure it is executable (only needed on Unix)
            if os.name != "nt":
                os.chmod(JAVA_BIN, 0o755)
            break
    print(f"Using Java at: {JAVA_BIN}")


def run_java_command(jar, args):
    cmd = [JAVA_BIN, "-jar", jar] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=WORKDIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {result.stderr}")
        exit(1)
    print(result.stdout)


def ask_lovely_support():
    """Ask user if they want Lovely mod framework support."""
    print()
    print("=" * 60)
    print("LOVELY MOD SUPPORT")
    print("=" * 60)
    print()
    print("Lovely is a runtime Lua injector that allows loading mods")
    print("(such as Steamodded) into Balatro on Android.")
    print()
    print("If you enable this, the APK will be built with Lovely")
    print("embedded. After installing, you can add mods to:")
    print("  ASET/Mods  (accessible via Material Files on Android)")
    print()
    print("If you just want vanilla portrait Balatro, skip this.")
    print()

    while True:
        response = input("Enable Lovely mod support? (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Please enter 'y' or 'n'")


def main():
    # Parse CLI flags
    use_lovely = "--with-lovely" in sys.argv
    skip_lovely_prompt = "--no-lovely" in sys.argv

    # --- Pre-flight check: Game.love must exist before we do anything ---
    game_love_src = os.path.join(os.getcwd(), "Game.love")
    if not os.path.exists(game_love_src):
        print()
        print("ERROR: Game.love not found!")
        print()
        print("You must run rebuild_game.py first to generate Game.love:")
        print()
        print("  python rebuild_game.py")
        print()
        print("If you haven't set up the project yet, run setup.py first:")
        print()
        print("  python setup.py \"C:\\path\\to\\Balatro.exe\"")
        exit(1)

    if not os.path.exists(WORKDIR):
        os.makedirs(WORKDIR)

    # Determine Lovely support (CLI flag > interactive prompt)
    if not use_lovely and not skip_lovely_prompt:
        use_lovely = ask_lovely_support()

    if use_lovely:
        print()
        print("[*] Building WITH Lovely mod support")
        apk_url = LOVELY_APK_URL
        apk_filename = "lovely-base.apk"
    else:
        print()
        print("[*] Building WITHOUT Lovely (vanilla portrait mode)")
        apk_url = LOVE_APK_URL
        apk_filename = "love-11.5-android-embed.apk"

    with PROFILER.step("Setup JDK"):
        setup_jdk()

    # Download Tools (parallel)
    apktool = os.path.join(WORKDIR, "apktool.jar")
    signer = os.path.join(WORKDIR, "uber-apk-signer.jar")
    patch_zip = os.path.join(WORKDIR, "Balatro-APK-Patch.zip")
    base_apk = os.path.join(WORKDIR, apk_filename)

    all_downloads = [
        (APKTOOL_URL, apktool),
        (SIGNER_URL, signer),
        (PATCH_URL, patch_zip),
        (apk_url, base_apk),
    ]

    with PROFILER.step("Download tools"):
        download_all_parallel(all_downloads)

    # 1. Unpack Love2D APK
    with PROFILER.step("Unpack APK"):
        apk_out = os.path.join(WORKDIR, "balatro-apk")
        if os.path.exists(apk_out):
            shutil.rmtree(apk_out)
        print("Unpacking APK...")
        run_java_command(apktool, ["d", "-o", "balatro-apk", apk_filename])

    # 2. Extract Patch
    with PROFILER.step("Extract patch"):
        print("Extracting Patch...")
        patch_dir = os.path.join(WORKDIR, "Balatro-APK-Patch")
        if os.path.exists(patch_dir):
            shutil.rmtree(patch_dir)
        with zipfile.ZipFile(patch_zip, "r") as zip_ref:
            zip_ref.extractall(WORKDIR)

    # 3. Apply Patch
    with PROFILER.step("Apply manifest patch"):
        print("Applying Patch...")
    manifest_path = os.path.join(apk_out, "AndroidManifest.xml")

    if use_lovely:
        # Lovely mode: patch LMM's manifest in-place (preserves providers, AndroidX, liblovely)
        print("  [Lovely] Preserving LMM base manifest (patching in-place)")

        with open(manifest_path, "r") as f:
            manifest_content = f.read()

        # Replace LMM package name with standard Balatro package
        manifest_content = manifest_content.replace(
            "systems.shorty.lmm",
            "com.unofficial.balatro"
        )

        # Set app label to "Balatro" and make it debuggable
        manifest_content = re.sub(
            r'android:label="[^"]+"',
            'android:label="Balatro"',
            manifest_content,
        )
        # Add debuggable="true" if not present
        if 'android:debuggable="true"' not in manifest_content:
            manifest_content = manifest_content.replace(
                '<application ',
                '<application android:debuggable="true" '
            )

        # Set portrait orientation
        manifest_content = re.sub(
            r'android:screenOrientation="[^"]+"',
            'android:screenOrientation="portrait"',
            manifest_content,
        )

        # Ensure configChanges includes uiMode (LMM's may not have it)
        manifest_content = re.sub(
            r'android:configChanges="[^"]+"',
            'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|uiMode|keyboard|keyboardHidden|navigation"',
            manifest_content,
        )

        with open(manifest_path, "w") as f:
            f.write(manifest_content)
        print("  [Lovely] Patched: label=Balatro, orientation=portrait, configChanges=full")

    else:
        # ── VANILLA MODE ──
        # Copy the patch's AndroidManifest.xml (designed for vanilla Love2D APK)
        shutil.copy(
            os.path.join(WORKDIR, "AndroidManifest.xml"),
            os.path.join(apk_out, "AndroidManifest.xml"),
        )

        with open(manifest_path, "r") as f:
            manifest_content = f.read()

        # Bump versionCode/versionName so installs as an update without uninstalling (keeps saves)
        build_version_code = int(time.time())
        build_version_name = "1.0.0n-FULL-p1"
        manifest_content = re.sub(
            r'android:versionCode="[^"]+"',
            f'android:versionCode="{build_version_code}"',
            manifest_content,
        )
        manifest_content = re.sub(
            r'android:versionName="[^"]+"',
            f'android:versionName="{build_version_name}"',
            manifest_content,
        )

        # Replace all possible orientation values with portrait (prevents runtime rotation)
        for orient in [
            "landscape", "sensorLandscape", "userLandscape", "reverseLandscape",
            "fullSensor", "sensor", "nosensor", "unspecified",
        ]:
            manifest_content = manifest_content.replace(
                f'screenOrientation="{orient}"', 'screenOrientation="portrait"'
            )

        with open(manifest_path, "w") as f:
            f.write(manifest_content)
        print("Set screen orientation to PORTRAIT (hard-locked, ignores auto-rotate)")

        # Force configChanges to prevent activity restart on rotation
        with open(manifest_path, "r") as f:
            manifest_content = f.read()

        manifest_content = re.sub(
            r'android:configChanges="[^"]+"',
            r'android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout|uiMode|keyboard|keyboardHidden|navigation"',
            manifest_content,
        )

        with open(manifest_path, "w") as f:
            f.write(manifest_content)
        print("Forced configChanges to handle orientation/screenSize (prevents crash)")

    # Copy icons
    res_dirs = [
        "drawable-hdpi",
        "drawable-mdpi",
        "drawable-xhdpi",
        "drawable-xxhdpi",
        "drawable-xxxhdpi",
    ]
    for d in res_dirs:
        src = os.path.join(WORKDIR, "res", d, "love.png")
        dst = os.path.join(apk_out, "res", d, "love.png")
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)

    # 4. Copy Game.love
    print("Copying Game.love...")
    # game_love_src is validated at the top of main() — safe to use directly
    game_love_dst = os.path.join(apk_out, "assets", "game.love")
    os.makedirs(os.path.dirname(game_love_dst), exist_ok=True)
    shutil.copy(game_love_src, game_love_dst)

    # 4.5. Copy custom smali files (orientation fixes, etc.)
    smali_src = os.path.join(os.getcwd(), "src", "smali")
    if use_lovely:
        # LMM's SDLActivity.smali contains Lovely's native initialization.
        # Overwriting it with our vanilla version destroys Lovely's init code.
        # Portrait orientation is enforced via AndroidManifest instead.
        print("Skipping custom smali patches (Lovely mode)")
    elif os.path.exists(smali_src):
        print("Copying custom smali patches...")
        smali_dst = os.path.join(apk_out, "smali")
        applied = 0
        skipped = 0
        # Copy smali files recursively, overwriting existing files
        for root, dirs, files in os.walk(smali_src):
            for file in files:
                if file.endswith(".smali"):
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, smali_src)
                    dst_file = os.path.join(smali_dst, rel_path)
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy(src_file, dst_file)
                    print(f"  Patched: {rel_path}")
                    applied += 1
        print(f"Custom smali patches: {applied} applied")

    # 5. Repack APK
    with PROFILER.step("Repack APK"):
        print("Repacking APK...")
        run_java_command(apktool, ["b", "-o", "balatro.apk", "balatro-apk"])

    # 6. Sign APK
    with PROFILER.step("Sign APK"):
        print("Signing APK...")
        run_java_command(signer, ["-a", "balatro.apk"])

    build_type = "MODDED (Lovely)" if use_lovely else "VANILLA"
    PROFILER.report()
    print(f"\n{'=' * 60}")
    print(f"Build Complete! [{build_type}]")
    print(f"{'=' * 60}")
    print(f"APK: balatro-mobile-maker/balatro-aligned-debugSigned.apk")

    if use_lovely:
        print()
        print("MOD INSTALLATION (requires rooted device):")
        print("  1. Install Material Files from Play Store")
        print("  2. Open Material Files > navigate to:")
        print("     / > data > user > 0 > com.unofficial.balatro > files > save > ASET > Mods")
        print("  3. Place your mod folders there")
        print("  4. Restart the game")
        print()
        print("NOTE: Root access (e.g. Magisk) is required to access /data/user/0/")
        print("See docs/MODDING.md for detailed instructions.")


if __name__ == "__main__":
    main()
