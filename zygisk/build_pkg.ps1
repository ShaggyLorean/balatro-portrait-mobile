param(
    [string]$NdkDir = $env:ANDROID_NDK_HOME,
    [string]$AndroidPlatform = "android-26"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $root

if (-not $NdkDir) {
    throw "ANDROID_NDK_HOME is not set. Install Android NDK r27c or pass -NdkDir <path>."
}
if (-not (Test-Path (Join-Path $NdkDir "build\cmake\android.toolchain.cmake"))) {
    throw "Android NDK toolchain file was not found under: $NdkDir"
}

$ninja = (Get-Command ninja -ErrorAction Stop).Source
$python = (Get-Command python -ErrorAction Stop).Source

& (Join-Path $root "fetch_deps.ps1")

$distRoot = Join-Path $root "dist"
$moduleDir = Join-Path $distRoot "balatro_portrait"
$moduleZip = Join-Path $distRoot "balatro_portrait.zip"
if (Test-Path $moduleDir) { Remove-Item -Recurse -Force $moduleDir }
if (Test-Path $moduleZip) { Remove-Item -Force $moduleZip }

New-Item -ItemType Directory -Force -Path @(
    (Join-Path $moduleDir "zygisk"),
    (Join-Path $moduleDir "zygisk\variants"),
    (Join-Path $moduleDir "system\lib64")
) | Out-Null

Copy-Item (Join-Path $root "module\module.prop") $moduleDir -Force
Copy-Item (Join-Path $root "module\customize.sh") $moduleDir -Force

$variants = @(
    @{ Name = "readabletro-on_crt-off";  Readabletro = "on";  Ctr = "off" },
    @{ Name = "readabletro-on_crt-on";   Readabletro = "on";  Ctr = "on"  },
    @{ Name = "readabletro-off_crt-off"; Readabletro = "off"; Ctr = "off" },
    @{ Name = "readabletro-off_crt-on";  Readabletro = "off"; Ctr = "on"  }
)

foreach ($variant in $variants) {
    $name = $variant.Name
    Write-Host "=== Building $name ==="
    & $python (Join-Path $root "gen_assets.py") `
        --readabletro $variant.Readabletro `
        --crt-disable $variant.Ctr `
        --out (Join-Path $root "src\assets_gen.h")

    $buildDir = Join-Path $root "build\$name"
    if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
    cmake -G Ninja -S $root -B $buildDir `
        "-DCMAKE_TOOLCHAIN_FILE=$NdkDir\build\cmake\android.toolchain.cmake" `
        "-DANDROID_ABI=arm64-v8a" `
        "-DANDROID_PLATFORM=$AndroidPlatform" `
        "-DCMAKE_MAKE_PROGRAM=$ninja" `
        "-DCMAKE_BUILD_TYPE=Release"
    if ($LASTEXITCODE -ne 0) { throw "CMake configure failed for $name" }
    cmake --build $buildDir
    if ($LASTEXITCODE -ne 0) { throw "CMake build failed for $name" }

    Copy-Item (Join-Path $buildDir "libbalatro_portrait.so") `
        (Join-Path $moduleDir "zygisk\variants\$name.so") -Force
    Copy-Item (Join-Path $buildDir "libshadowhook_nothing.so") `
        (Join-Path $moduleDir "system\lib64\libshadowhook_nothing.so") -Force
}

$defaultVariant = Join-Path $moduleDir "zygisk\variants\readabletro-on_crt-off.so"
Copy-Item $defaultVariant (Join-Path $moduleDir "zygisk\arm64-v8a.so") -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($moduleDir, $moduleZip)

Write-Host "Packaged: $moduleZip"
Write-Host "Install this ZIP from KernelSU, Magisk, or APatch, then reboot."
