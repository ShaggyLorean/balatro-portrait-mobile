import os
import urllib.request
import subprocess
import shutil
import zipfile
import tarfile

# Constants
JDK_URL = "https://aka.ms/download-jdk/microsoft-jdk-21.0.3-linux-x64.tar.gz"
APKTOOL_URL = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"
SIGNER_URL = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"
PATCH_URL = "https://github.com/blake502/balatro-apk-maker/releases/download/Additional-Tools-1.0/Balatro-APK-Patch.zip"
LOVE_APK_URL = "https://github.com/love2d/love-android/releases/download/11.5a/love-11.5-android-embed.apk"

WORKDIR = os.path.abspath("balatro-mobile-maker")
JDK_DIR = os.path.join(WORKDIR, "jdk")
JAVA_BIN = os.path.join(JDK_DIR, "bin", "java") # Will need to find actual path after extraction

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

        # Use system tar
        subprocess.run(["tar", "-xf", jdk_archive, "-C", WORKDIR], check=True)
        
        # Find the extracted folder (it usually has a versioned name)
        for item in os.listdir(WORKDIR):
            if item.startswith("jdk-"):
                shutil.move(os.path.join(WORKDIR, item), JDK_DIR)
                break
    
    # Locate java bin
    global JAVA_BIN
    for root, dirs, files in os.walk(JDK_DIR):
        if "java" in files and "bin" in root:
            JAVA_BIN = os.path.join(root, "java")
            # Ensure it is executable
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
    run_java_command(apktool, ["d", "-s", "-o", "balatro-apk", "love-11.5-android-embed.apk"])

    # 2. Extract Patch
    print("Extracting Patch...")
    patch_dir = os.path.join(WORKDIR, "Balatro-APK-Patch")
    if os.path.exists(patch_dir):
        shutil.rmtree(patch_dir)
    with zipfile.ZipFile(patch_zip, 'r') as zip_ref:
        zip_ref.extractall(WORKDIR) # Extracts into Balatro-APK-Patch folder normally or creates it

    # 3. Apply Patch
    print("Applying Patch...")
    # Copy AndroidManifest.xml
    # Zip extracted to WORKDIR
    shutil.copy(os.path.join(WORKDIR, "AndroidManifest.xml"), os.path.join(apk_out, "AndroidManifest.xml"))
    
    # Modify AndroidManifest for portrait orientation (force lock with nosensor)
    manifest_path = os.path.join(apk_out, "AndroidManifest.xml")
    with open(manifest_path, 'r') as f:
        manifest_content = f.read()
    # Replace all possible orientation values with nosensor (completely ignores sensor)
    manifest_content = manifest_content.replace('screenOrientation="landscape"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="sensorLandscape"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="userLandscape"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="reverseLandscape"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="fullSensor"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="sensor"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="unspecified"', 'screenOrientation="nosensor"')
    manifest_content = manifest_content.replace('screenOrientation="portrait"', 'screenOrientation="nosensor"')
    with open(manifest_path, 'w') as f:
        f.write(manifest_content)
    print("Set screen orientation to NOSENSOR (ignores all rotation)")
    
    # Also remove orientation from configChanges to prevent runtime rotation
    import re
    with open(manifest_path, 'r') as f:
        manifest_content = f.read()
    # Remove orientation from configChanges (can be anywhere in the list)
    manifest_content = re.sub(r'orientation\|', '', manifest_content)
    manifest_content = re.sub(r'\|orientation', '', manifest_content)
    manifest_content = re.sub(r'configChanges="orientation"', 'configChanges=""', manifest_content)
    with open(manifest_path, 'w') as f:
        f.write(manifest_content)
    print("Removed orientation from configChanges")
    
    # Copy icons
    res_dirs = ["drawable-hdpi", "drawable-mdpi", "drawable-xhdpi", "drawable-xxhdpi", "drawable-xxxhdpi"]
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
