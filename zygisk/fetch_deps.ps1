$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$deps = Join-Path $root "deps"
$shadowhook = Join-Path $deps "shadowhook"
$zsample = Join-Path $deps "zsample"

$shadowhookRepo = "https://github.com/bytedance/android-inline-hook.git"
$shadowhookCommit = "0aa7a93dd3b4ceb8558dc0058873ab3b6289b51b"
$zsampleRepo = "https://github.com/topjohnwu/zygisk-module-sample.git"
$zsampleCommit = "26ae876a437f4c34c5d1ab21d6aeac736301d2d0"

New-Item -ItemType Directory -Force $deps | Out-Null

if (-not (Test-Path $shadowhook)) {
    git clone --depth 1 $shadowhookRepo $shadowhook
}
git -C $shadowhook fetch --depth 1 origin $shadowhookCommit
git -C $shadowhook checkout --detach $shadowhookCommit

if (-not (Test-Path $zsample)) {
    git clone --depth 1 $zsampleRepo $zsample
}
git -C $zsample fetch --depth 1 origin $zsampleCommit
git -C $zsample checkout --detach $zsampleCommit

$patch = Join-Path $root "patches\shadowhook-nothing-override.patch"
$alreadyPatched = git -C $shadowhook grep -n "sh_linker_nothing_override_path" -- shadowhook/src/main/cpp/sh_linker.c
if (-not $alreadyPatched) {
    git -C $shadowhook apply $patch
}

Write-Host "Dependencies ready:"
Write-Host "  shadowhook $shadowhookCommit"
Write-Host "  zygisk sample $zsampleCommit"
