_RELEASE_MODE = true
_DEMO = false

-- Mod loaders draw their own boot screen by replacing the global boot_timer,
-- and they lay it out for a desktop window: Steamodded centres a 300px bar with
-- the mod icon 264px to its left, so on a phone the icon falls off the left edge
-- and the status line runs past the right one (#44).
--
-- Rather than edit the loader (which would break on its next release), watch for
-- whoever takes over that global and scale what it draws to fit the window. Any
-- loader that keeps its screen inside a normal desktop width lands on screen,
-- whatever version it is. Only a taller-than-wide window is touched, so desktop
-- behaviour is unchanged.
local _boot_screen_design_w = 620
local _wrapped_boot_timers = setmetatable({}, {__mode = 'k'})

local function _fit_boot_screen(fn)
    if type(fn) ~= 'function' or _wrapped_boot_timers[fn] then return fn end
    local wrapper = function(...)
        local ok_mode, w, h = pcall(love.window.getMode)
        if not (ok_mode and w and h and h > w) then return fn(...) end

        local scale = math.min(1, (w - 12)/_boot_screen_design_w)
        if scale >= 1 then return fn(...) end

        love.graphics.push()
        love.graphics.translate(w/2, h/2)
        love.graphics.scale(scale, scale)
        love.graphics.translate(-w/2, -h/2)

        -- Scaling the layout is not enough on its own: the status line grows with
        -- whatever is being loaded, and a long one still ran past the edge. While
        -- the boot screen draws, text that would overflow is squeezed to fit the
        -- room it has. Restored the moment the call returns.
        local real_print = love.graphics.print
        local right_edge = w/2 + (w/2)/scale
        love.graphics.print = function(text, x, y, r, sx, sy, ...)
            if type(text) == 'string' and type(x) == 'number' then
                local font = love.graphics.getFont()
                if font then
                    local avail = right_edge - x - 8
                    local width = font:getWidth(text)*(sx or 1)
                    if avail > 0 and width > avail then
                        sx = (sx or 1)*(avail/width)
                        sy = sx
                    end
                end
            end
            return real_print(text, x, y, r, sx, sy, ...)
        end

        local ok, err = pcall(fn, ...)

        love.graphics.print = real_print
        love.graphics.pop()
        if not ok then error(err, 0) end
    end
    _wrapped_boot_timers[wrapper] = true
    return wrapper
end

-- boot_timer is kept out of _G itself so that every read and write goes through
-- here. The game defines it and the loader overwrites it afterwards; leaving the
-- real key in place would mean only the first of those is ever seen.
do
    local stored = rawget(_G, 'boot_timer')
    rawset(_G, 'boot_timer', nil)

    local mt = getmetatable(_G) or {}
    local previous_index, previous_newindex = mt.__index, mt.__newindex

    mt.__index = function(t, k)
        if k == 'boot_timer' then return stored end
        if type(previous_index) == 'function' then return previous_index(t, k) end
        if previous_index then return previous_index[k] end
        return nil
    end

    mt.__newindex = function(t, k, v)
        if k == 'boot_timer' then stored = _fit_boot_screen(v) return end
        if previous_newindex then return previous_newindex(t, k, v) end
        rawset(t, k, v)
    end

    setmetatable(_G, mt)
    stored = _fit_boot_screen(stored)
end

function love.conf(t)
	t.console = not _RELEASE_MODE
	t.title = 'Balatro'
	t.window.width = 0
    t.window.height = 0
	t.window.minwidth = 100
	t.window.minheight = 100

	-- Android lists the accelerometer as a three axis joystick by default, and
	-- gravity alone keeps an axis past the deadzone. The game reads that as a
	-- gamepad and switches to controller mode, which is what put Balatro's own
	-- on-screen keyboard behind the system keyboard while renaming a profile
	-- (#44). Nothing here uses tilt input, so the device is pure noise.
	t.accelerometerjoystick = false

	-- Force portrait orientation on mobile at engine level
	t.window.usedpiscale = true
	t.modules.window = true
end
