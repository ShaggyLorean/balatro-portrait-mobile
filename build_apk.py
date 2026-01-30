import os
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request
import zipfile

# Constants
# Use Windows JDK for Windows, Linux JDK for Linux
if os.name == "nt":
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-windows-x64.zip"
else:
    JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-linux-x64.tar.gz"
APKTOOL_URL = (
    "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
)
SIGNER_URL = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
PATCH_URL = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/Balatro-APK-Patch.zip"
LOVE_APK_URL = "https://github.com/love2d/love-android/releases/download/11.5a/love-11.5-android-embed.apk"

WORKDIR = os.path.abspath("balatro-mobile-maker")
JDK_DIR = os.path.join(WORKDIR, "jdk")
JAVA_BIN = os.path.join(
    JDK_DIR, "bin", "java"
)  # Will need to find actual path after extraction


def download_file(url, dest):
    if os.path.exists(dest):
        print(f"File {dest} already exists. Skipping.")
        return
    print(f"Downloading {url} to {dest}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        exit(1)


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


def main():
    if not os.path.exists(WORKDIR):
        os.makedirs(WORKDIR)

    setup_jdk()

    # Download Tools
    apktool = os.path.join(WORKDIR, "apktool.jar")
    signer = os.path.join(WORKDIR, "uber-apk-signer.jar")
    patch_zip = os.path.join(WORKDIR, "Balatro-APK-Patch.zip")
    base_apk = os.path.join(WORKDIR, "love-11.5-android-embed.apk")

    download_file(APKTOOL_URL, apktool)
    download_file(SIGNER_URL, signer)
    download_file(PATCH_URL, patch_zip)
    download_file(LOVE_APK_URL, base_apk)

    # 1. Unpack Love2D APK
    apk_out = os.path.join(WORKDIR, "balatro-apk")
    if os.path.exists(apk_out):
        shutil.rmtree(apk_out)

    print("Unpacking APK...")
    run_java_command(apktool, ["d", "-o", "balatro-apk", "love-11.5-android-embed.apk"])

    # 2. Extract Patch
    print("Extracting Patch...")
    patch_dir = os.path.join(WORKDIR, "Balatro-APK-Patch")
    if os.path.exists(patch_dir):
        shutil.rmtree(patch_dir)
    with zipfile.ZipFile(patch_zip, "r") as zip_ref:
        zip_ref.extractall(
            WORKDIR
        )  # Extracts into Balatro-APK-Patch folder normally or creates it

    # 3. Apply Patch
    print("Applying Patch...")
    # Copy AndroidManifest.xml
    # Zip extracted to WORKDIR
    shutil.copy(
        os.path.join(WORKDIR, "AndroidManifest.xml"),
        os.path.join(apk_out, "AndroidManifest.xml"),
    )

    # Modify AndroidManifest: bump version for install-as-update + hard-lock PORTRAIT orientation
    manifest_path = os.path.join(apk_out, "AndroidManifest.xml")
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
    manifest_content = manifest_content.replace(
        'screenOrientation="landscape"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="sensorLandscape"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="userLandscape"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="reverseLandscape"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="fullSensor"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="sensor"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="nosensor"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="unspecified"', 'screenOrientation="portrait"'
    )
    manifest_content = manifest_content.replace(
        'screenOrientation="portrait"', 'screenOrientation="portrait"'
    )
    with open(manifest_path, "w") as f:
        f.write(manifest_content)
    print("Set screen orientation to PORTRAIT (hard-locked, ignores auto-rotate)")

    # Force orientation into configChanges to PREVENT activity restart on rotation
    # If the activity restarts (which happens if orientation is NOT in configChanges),
    # Love2D crashes with "filesystem already initialized".
    with open(manifest_path, "r") as f:
        manifest_content = f.read()

    # Replace existing configChanges with a comprehensive list that prevents restarts
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
    game_love_src = os.path.join(os.getcwd(), "Game.love")
    game_love_dst = os.path.join(apk_out, "assets", "game.love")
    os.makedirs(os.path.dirname(game_love_dst), exist_ok=True)
    shutil.copy(game_love_src, game_love_dst)

    # 4.5. Copy custom smali files (orientation fixes, etc.)
    print("Copying custom smali patches...")
    smali_src = os.path.join(os.getcwd(), "src", "smali")
    if os.path.exists(smali_src):
        smali_dst = os.path.join(apk_out, "smali")
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
        print("Custom smali patches applied")
    else:
        print("No custom smali patches found (src/smali doesn't exist)")

    # 5. Repack APK
    print("Repacking APK...")
    run_java_command(apktool, ["b", "-o", "balatro.apk", "balatro-apk"])

    # 6. Sign APK
    print("Signing APK...")
    # java -jar uber-apk-signer.jar -a balatro.apk
    run_java_command(signer, ["-a", "balatro.apk"])

    print("Build Complete! Check balatro-mobile-maker/balatro-aligned-debugSigned.apk")


if __name__ == "__main__":
    main()
