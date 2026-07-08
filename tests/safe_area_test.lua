-- Fixture test for the mobile safe-area math in src/portrait_config.lua.
-- Run from the repo root: luajit tests/safe_area_test.lua
--
-- The design invariant under test: on iOS the room bottom must sit exactly
-- safe_area_y tiles below the SAFE-AREA bottom edge — the same overshoot the
-- Android layout was tuned with relative to the physical bottom — so every
-- bottom-anchored offset (main-menu buttons, corner buttons, the hand) lands
-- with its dialed-in spacing on any iPhone. Device numbers come from
-- tests/ios_inset_fixtures.txt, which the ios-simulator workflow validates
-- against real simulators.

local failures = 0
local function check(cond, msg)
    if cond then
        print("ok - " .. msg)
    else
        failures = failures + 1
        print("FAIL - " .. msg)
    end
end
local function near(a, b) return math.abs(a - b) < 1e-9 end

-- Minimal LOVE mock: exactly the surface the safe-area functions touch.
local current = {}
love = {
    system = { getOS = function() return current.os end },
    window = {},
    graphics = { getHeight = function() return current.h end },
}

dofile("src/portrait_config.lua")

local TILESIZE = 20
local TILE_W = 20

-- Mirrors main.lua: TILESCALE = w / (TILE_W * scale_factor * TILESIZE);
-- one room tile is w / (TILE_W * scale_factor) device units.
local function set_device(os_name, w, h, safe)
    current.os, current.h = os_name, h
    local tile = w / (TILE_W * PORTRAIT_CONFIG.scale_factor)
    G = { TILESCALE = tile / TILESIZE, TILESIZE = TILESIZE }
    if safe then
        love.window.getSafeArea = function() return safe.x, safe.y, safe.w, safe.h end
    else
        love.window.getSafeArea = nil
    end
    return tile
end

local floor_inset = PORTRAIT_CONFIG.safe_area_y

-- iOS devices from the fixture file.
local fixture_count = 0
for line in io.lines("tests/ios_inset_fixtures.txt") do
    if not line:match("^%s*#") and line:match("%S") then
        local name, w, h, top_pt, bottom_pt = line:match("^(.-)|(%d+)|(%d+)|(%d+)|(%d+)%s*$")
        assert(name, "bad fixture line: " .. line)
        w, h, top_pt, bottom_pt = tonumber(w), tonumber(h), tonumber(top_pt), tonumber(bottom_pt)
        fixture_count = fixture_count + 1

        local tile = set_device("iOS", w, h, {x = 0, y = top_pt, w = w, h = h - top_pt - bottom_pt})
        local top = get_mobile_safe_area_top("iOS")
        local trim = get_mobile_room_bottom_trim("iOS", top)

        check(near(top, math.max(top_pt / tile, floor_inset)),
            name .. ": top inset is measured value with the tuned floor")

        local room_bottom = top + (h / tile - trim)
        local safe_bottom = (h - bottom_pt) / tile
        check(near(room_bottom, safe_bottom + floor_inset),
            name .. ": room bottom overshoots the SAFE bottom by exactly the tuned floor")
        check(trim >= 0, name .. ": trim never negative")
    end
end
check(fixture_count >= 3, "fixture file parsed (" .. fixture_count .. " devices)")

-- Android: static tuned value, full-height room, regardless of getSafeArea.
set_device("Android", 1080, 2400, {x = 0, y = 90, w = 1080, h = 2250})
check(near(get_mobile_safe_area_top("Android"), floor_inset),
    "Android: top is the static tuned inset, not the measured one")
check(near(get_mobile_room_bottom_trim("Android", floor_inset), 0),
    "Android: room height untouched")

-- Desktop: no insets at all.
set_device("Windows", 1920, 1080, nil)
check(near(get_mobile_safe_area_top("Windows"), 0), "Desktop: no top inset")
check(near(get_mobile_room_bottom_trim("Windows", 0), 0), "Desktop: no bottom trim")

-- iOS with the safe-area API missing: degrade to the old behaviour.
set_device("iOS", 393, 852, nil)
check(near(get_mobile_safe_area_top("iOS"), floor_inset),
    "iOS w/o getSafeArea: falls back to the static floor")
check(near(get_mobile_room_bottom_trim("iOS", floor_inset), 0),
    "iOS w/o getSafeArea: no trim (old behaviour)")

-- Tester knobs shift the results one-for-one.
local tile = set_device("iOS", 393, 852, {x = 0, y = 59, w = 393, h = 759})
local base_top = get_mobile_safe_area_top("iOS")
local base_trim = get_mobile_room_bottom_trim("iOS", base_top)
PORTRAIT_CONFIG.safe_area_extra_ios = 0.5
PORTRAIT_CONFIG.safe_area_bottom_extra_ios = 0.3
local knob_top = get_mobile_safe_area_top("iOS")
check(near(knob_top, base_top + 0.5), "safe_area_extra_ios adds to the top inset")
check(near(get_mobile_room_bottom_trim("iOS", knob_top), base_trim + 0.5 + 0.3),
    "safe_area_bottom_extra_ios adds to the trim (plus the extra top overshoot)")
PORTRAIT_CONFIG.safe_area_extra_ios = 0.0
PORTRAIT_CONFIG.safe_area_bottom_extra_ios = 0.0

print(failures == 0 and "ALL PASSED" or (failures .. " FAILURES"))
os.exit(failures == 0 and 0 or 1)
