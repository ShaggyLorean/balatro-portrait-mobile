#!/usr/bin/env python3
"""Generate the embedded Zygisk Lua/resource payload.

The Zygisk module cannot rely on patching the official APK on disk, so the
portrait Lua and optional Readabletro resources are compiled into the native
module. The generator mirrors the safe build.py transforms without mutating
src/.
"""

import argparse
import base64
import hashlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
DEFAULT_OUT = Path(__file__).resolve().parent / "src" / "assets_gen.h"

sys.path.insert(0, str(REPO_ROOT))
import build as portrait_build  # noqa: E402


def _truth(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Embed Balatro portrait Lua and optional Zygisk resources."
    )
    parser.add_argument(
        "--readabletro",
        choices=("on", "off"),
        default="off" if os.environ.get("BALATRO_ZYGISK_READABLETRO", "").strip().lower() == "off" else "on",
        help="embed Readabletro Lua/resource overrides",
    )
    parser.add_argument(
        "--disable-crt", "--crt-disable",
        dest="crt_disable",
        choices=("on", "off"),
        default="on" if _truth(os.environ.get("BALATRO_ZYGISK_CRT_DISABLE")) else "off",
        help="disable the CRT shader in portrait, matching build.py --disable-crt"
             " (--crt-disable is a deprecated alias)",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="output assets_gen.h path",
    )
    args = parser.parse_args()
    return args


def _rel_of(path):
    return path.relative_to(SRC_DIR).as_posix()


def _read(path):
    return path.read_bytes()


def _normalize_lf(data):
    return data.replace(b"\r\n", b"\n")


def _replace_once(content, original, modified, label):
    if modified in content:
        return content
    if original not in content:
        raise RuntimeError(f"{label} patch target not found")
    return content.replace(original, modified, 1)


def _apply_readabletro_lua(rel, data):
    patches = portrait_build.READABLETRO_LUA_PATCHES.get(rel)
    if not patches:
        return data

    content = data.decode("utf-8")
    for original, modified in patches:
        content = _replace_once(content, original, modified, f"Readabletro {rel}")
    return content.encode("utf-8")


def _apply_lua_transforms(rel, data, readabletro, crt_disable):
    data = _normalize_lf(data)

    if readabletro:
        data = _apply_readabletro_lua(rel, data)

    if rel == "game.lua" and crt_disable:
        content = data.decode("utf-8")
        content = _replace_once(
            content,
            portrait_build.CRT_PATCH_ORIGINAL,
            portrait_build.CRT_PATCH_MODIFIED,
            "CRT disable game.lua",
        )
        data = content.encode("utf-8")

    return data


def _pick_bracket(data):
    level = 0
    while ("]" + "=" * level + "]").encode() in data or ("[" + "=" * level + "[").encode() in data:
        level += 1
    return ("[" + "=" * level + "[").encode(), ("]" + "=" * level + "]").encode()


def _lua_long_string(data):
    """Quote bytes as a Lua long-bracket string, preserving them exactly.

    The newline right after the opening bracket is stripped by Lua, so it
    protects data that itself starts with a newline; nothing is appended, so
    find/replace rules stay byte-exact.
    """
    open_bracket, close_bracket = _pick_bracket(data)
    return open_bracket + b"\n" + data + close_bracket


def _lua_shader_rules_module(name, replace, patches):
    parts = [f'package.preload["{name}"] = function(...)\nreturn {{\n'.encode()]

    parts.append(b"replace={\n")
    for key in sorted(replace):
        parts.append(b'["' + key.encode() + b'"]=' + _lua_long_string(replace[key]) + b",\n")
    parts.append(b"},\n")

    parts.append(b"patches={\n")
    for key in sorted(patches):
        parts.append(b'["' + key.encode() + b'"]={\n')
        for rule in patches[key]:
            parts.append(b"{find=" + _lua_long_string(rule["find"])
                         + b",replace=" + _lua_long_string(rule["replace"]))
            if "guard" in rule:
                parts.append(b",guard=" + _lua_long_string(rule["guard"]))
            parts.append(b"},\n")
        parts.append(b"},\n")
    parts.append(b"},\n")

    parts.append(b"}\nend\n")
    return b"".join(parts)


def _resource_magic(path, data):
    suffix = Path(path).suffix.lower()
    if suffix == ".png":
        magic = b"\x89PNG\r\n\x1a\n"
        if not data.startswith(magic):
            raise RuntimeError(f"PNG magic mismatch: {path}")
        return magic
    if suffix in {".ttf", ".otf", ".ttc"}:
        valid = (b"\x00\x01\x00\x00", b"OTTO", b"ttcf", b"true")
        if not data.startswith(valid):
            raise RuntimeError(f"Font magic mismatch: {path}")
        return data[:4]
    return b""


def _resource_version(entries):
    digest = hashlib.sha256()
    for key in sorted(entries):
        digest.update(key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(entries[key])
        digest.update(b"\0")
    return digest.hexdigest()


def _lua_resource_module(name, entries):
    parts = [f'package.preload["{name}"] = function(...)\nreturn {{\n'.encode()]
    for key in sorted(entries):
        data = entries[key]
        encoded = base64.b64encode(data)
        magic = base64.b64encode(_resource_magic(key, data))
        open_bracket, close_bracket = _pick_bracket(encoded)
        parts.append(
            b'["'
            + key.encode()
            + b'"]={size='
            + str(len(data)).encode()
            + b',magic="'
            + magic
            + b'",data='
            + open_bracket
            + b"\n"
        )
        parts.append(encoded)
        parts.append(b"\n" + close_bracket + b"},\n")
    parts.append(b"}\nend\n")
    return b"".join(parts)


def _lua_string(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _install_embedded_files_lua(resource_version, managed_paths):
    managed_table = ", ".join(_lua_string(path) for path in managed_paths)
    return f"""
local PORTRAIT_EMBEDDED_RESOURCE_VERSION = "{resource_version}"
local PORTRAIT_EMBEDDED_MANAGED_FILES = {{{managed_table}}}

local function decode_portrait_base64(data)
    local alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    local values = {{}}
    for i = 1, #alphabet do values[alphabet:sub(i, i)] = i - 1 end
    data = data:gsub("%s+", "")

    local chunks = {{}}
    local chunk = {{}}
    local chunk_len = 0

    local function emit(byte)
        chunk_len = chunk_len + 1
        chunk[chunk_len] = string.char(byte)
        if chunk_len >= 4096 then
            chunks[#chunks + 1] = table.concat(chunk)
            chunk = {{}}
            chunk_len = 0
        end
    end

    for i = 1, #data, 4 do
        local c1 = data:sub(i, i)
        local c2 = data:sub(i + 1, i + 1)
        local c3 = data:sub(i + 2, i + 2)
        local c4 = data:sub(i + 3, i + 3)
        local v1 = assert(values[c1], "invalid base64 byte 1")
        local v2 = assert(values[c2], "invalid base64 byte 2")
        local v3 = c3 == "=" and 0 or assert(values[c3], "invalid base64 byte 3")
        local v4 = c4 == "=" and 0 or assert(values[c4], "invalid base64 byte 4")
        local triple = v1 * 262144 + v2 * 4096 + v3 * 64 + v4
        emit(math.floor(triple / 65536) % 256)
        if c3 ~= "=" then emit(math.floor(triple / 256) % 256) end
        if c4 ~= "=" then emit(triple % 256) end
    end

    if chunk_len > 0 then chunks[#chunks + 1] = table.concat(chunk) end
    return table.concat(chunks)
end

local function assert_portrait_embedded_file(path, data, size, magic)
    assert(#data == size, "embedded file size mismatch: " .. path)
    if magic and #magic > 0 then
        assert(data:sub(1, #magic) == magic, "embedded file magic mismatch: " .. path)
    end
end

local function install_portrait_embedded_files()
    if not (love and love.filesystem and love.filesystem.write and love.filesystem.getInfo) then return end
    local ok, files = pcall(require, "portrait_embedded_files")
    if not ok or type(files) ~= "table" then return end
    local version_path = "portrait_embedded_files.version"
    local current_version = love.filesystem.read and love.filesystem.read(version_path)
    local force_install = current_version ~= PORTRAIT_EMBEDDED_RESOURCE_VERSION
    if force_install and love.filesystem.remove then
        for _, path in ipairs(PORTRAIT_EMBEDDED_MANAGED_FILES) do
            if not files[path] then love.filesystem.remove(path) end
        end
    end
    for path, item in pairs(files) do
        local info = love.filesystem.getInfo(path)
        if force_install or not info or info.size ~= item.size then
            local data = decode_portrait_base64(item.data)
            local magic = decode_portrait_base64(item.magic or "")
            assert_portrait_embedded_file(path, data, item.size, magic)
            local dir = path:match("^(.*)/[^/]+$")
            if dir then assert(love.filesystem.createDirectory(dir)) end
            assert(love.filesystem.write(path, data))
            local written = love.filesystem.read and love.filesystem.read(path)
            if written then assert_portrait_embedded_file(path, written, item.size, magic) end
        end
    end
    assert(love.filesystem.write(version_path, PORTRAIT_EMBEDDED_RESOURCE_VERSION))
end
install_portrait_embedded_files()
""".encode()


def _collect_lua_files(readabletro, crt_disable):
    files = {}
    for path in SRC_DIR.rglob("*.lua"):
        rel = _rel_of(path)
        if rel.startswith("localization/"):
            continue
        files[rel] = _apply_lua_transforms(rel, _read(path), readabletro, crt_disable)
    return files


def _collect_shader_module(readabletro):
    """Emit shader replacements and patch rules, never the game's shaders.

    The module runs inside the official app, so game.lua reads the original
    shader sources from the APK at runtime and applies these rules there.
    Only repo-owned Readabletro replacements are embedded whole; the CRT
    slider-mask fix ships as a find/replace pair mirroring _replace_once.
    This keeps the flashable ZIP free of game-derived content and removes
    the build-time dependency on an extracted src/resources tree.
    """
    replace = {}
    if readabletro:
        base = REPO_ROOT / "patches" / "readabletro" / "shaders"
        for name in ("background.fs", "splash.fs"):
            path = base / name
            if not path.exists():
                raise FileNotFoundError(f"Readabletro shader not found: {path}")
            replace[name] = _normalize_lf(_read(path))

    # Every CRT.fs transform build.py applies to the extracted tree, expressed
    # as rules. If a new shader patch lands in _apply_crt_slider_mask_patch
    # (or anywhere else in build.py), it must be wired in here too — the
    # runtime otherwise sees the pristine APK shader without it.
    crt_rules = [
        _shader_rule(portrait_build.CRT_MASK_ORIGINAL, portrait_build.CRT_MASK_MODIFIED),
    ]
    for original, replacement in portrait_build.CRT_NOISE_COMMENTED_LINES:
        crt_rules.append(_shader_rule(original, replacement))
    patches = {"CRT.fs": crt_rules}
    return _lua_shader_rules_module("portrait_shaders", replace, patches)


def _shader_rule(find, replace):
    """Build one runtime patch rule, choosing the idempotency guard by shape.

    Insertion-shaped rules (the mask patch: replacement still contains the
    target) need a 'skip if the replacement is already present' guard, or
    they would re-apply forever. Uncomment-shaped rules (the noise lines:
    the target contains the replacement) must NOT have that guard — the
    replacement text is a substring of the still-commented original, so the
    guard would always fire and the rule would never apply.
    """
    rule = {"find": find.encode("utf-8"), "replace": replace.encode("utf-8")}
    if find in replace:
        rule["guard"] = replace.encode("utf-8")
    return rule


def _collect_readabletro_files(readabletro):
    if not readabletro:
        return {}

    base = REPO_ROOT / "patches" / "readabletro"
    files = {}
    font = base / "fonts" / "TypoQuik-Bold.ttf"
    if not font.exists():
        raise FileNotFoundError(f"Readabletro font not found: {font}")
    files["resources/fonts/TypoQuik-Bold.ttf"] = _read(font)

    texture_dir = base / "textures" / "2x"
    if not texture_dir.is_dir():
        raise FileNotFoundError(f"Readabletro texture directory not found: {texture_dir}")
    for path in sorted(texture_dir.glob("*.png")):
        files[f"resources/textures/2x/{path.name}"] = _read(path)

    return files


def _fold_preloads(files, readabletro):
    portrait_config = files.pop("portrait_config.lua", None)
    if portrait_config is None:
        raise FileNotFoundError("portrait_config.lua not found in src/")
    if "conf.lua" not in files:
        raise FileNotFoundError("conf.lua not found in src/")

    managed_resource_files = _collect_readabletro_files(True)
    resource_files = managed_resource_files if readabletro else {}
    resource_version = _resource_version(resource_files)
    resource_module = _lua_resource_module("portrait_embedded_files", resource_files)
    shader_module = _collect_shader_module(readabletro)
    config_module = (
        b'package.preload["portrait_config"] = function(...)\n'
        + _install_embedded_files_lua(resource_version, sorted(managed_resource_files))
        + portrait_config
        + b"\nend\n"
    )
    files["conf.lua"] = resource_module + shader_module + config_module + files["conf.lua"]
    return len(resource_files)


def _write_header(files, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    names = sorted(files.keys())
    with out_path.open("w", encoding="utf-8") as out:
        out.write("// AUTO-GENERATED by zygisk/gen_assets.py. Do not edit.\n")
        out.write("#pragma once\n#include <stddef.h>\n\n")
        for index, rel in enumerate(names):
            data = files[rel]
            out.write(f"static const unsigned char asset_{index}[] = {{")
            out.write(",".join(str(byte) for byte in data))
            out.write("};\n")
        out.write("\nstruct LuaAsset { const char* name; const unsigned char* data; size_t len; };\n")
        out.write("static const LuaAsset kAssets[] = {\n")
        for index, rel in enumerate(names):
            out.write(f'  {{"{rel}", asset_{index}, {len(files[rel])}}},\n')
        out.write("};\n")
        out.write(f"static const int kAssetCount = {len(names)};\n")


def main():
    args = _parse_args()
    readabletro = args.readabletro == "on"
    crt_disable = args.crt_disable == "on"
    out_path = Path(args.out).resolve()

    files = _collect_lua_files(readabletro=readabletro, crt_disable=crt_disable)
    embedded_resource_count = _fold_preloads(files, readabletro=readabletro)
    _write_header(files, out_path)

    total = sum(len(data) for data in files.values())
    print(
        f"embedded {len(files)} Lua chunks, {embedded_resource_count} resource files, "
        f"{total} bytes -> {out_path}"
    )


if __name__ == "__main__":
    main()
