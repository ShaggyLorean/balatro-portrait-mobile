-- Luacheck config tuned for this repo: src/ is largely vanilla Balatro code
-- that we deliberately do not restyle (smaller diff against upstream), so
-- style/whitespace/shadowing/unused classes are off. What stays on is the
-- class that catches real bugs in new portrait code: undefined globals
-- (W111/112/113) plus undefined love fields (W143).
std = "luajit+love"
allow_defined = true
max_line_length = false

exclude_files = {
    "src/localization/**",  -- extracted from the game, not ours
    "src/resources/**",
    "desktop_test/**",
    "balatro-mobile-maker/**",
    "zygisk/deps/**",
}

ignore = {
    "131",  -- implicitly defined global unused in checked files (G.FUNCS-style dispatch)
    "2..",  -- unused variables/arguments (vanilla noise)
    "3..",  -- unused assignments (vanilla noise)
    "4..",  -- shadowing (vanilla noise)
    "5..",  -- control-flow style (vanilla noise)
    "6..",  -- whitespace (vanilla noise)
}

read_globals = {
    "SMODS",  -- defined by Steamodded when installed
}

files = {
    -- Nil-guarded reads that upstream game code does on purpose; keep the
    -- ignores narrow (per variable, per file) so new typos still get caught.
    ["src/engine/animatedsprite.lua"] = {ignore = {"113/k"}},
    ["src/engine/ui.lua"] = {ignore = {"113/dt"}},
    ["src/functions/UI_definitions.lua"] = {ignore = {
        "113/maxw", "113/badges", "113/disabled", "113/target", "113/show_win_cta",
    }},
    -- The mobile LOVE fork adds APIs luacheck's love standard doesn't know
    -- (window.setHint, handlers table access, graphics.isCreated).
    ["src/main.lua"] = {ignore = {"143"}},
    ["src/functions/misc_functions.lua"] = {ignore = {"143"}},
}
