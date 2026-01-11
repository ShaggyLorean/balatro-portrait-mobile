if (love.system.getOS() == 'OS X' ) and (jit.arch == 'arm64' or jit.arch == 'arm') then jit.off() end

-- Android: force orientation hints off at runtime (LOVE/SDL can override manifest via hints)
local function _force_android_portrait_hints()
    if not (love and love.system and love.system.getOS and love.system.getOS() == 'Android') then return end
    if not (love and love.window and love.window.setMode) then return end

    -- These are SDL/LÖVE orientation hints used by love-android.
    -- If they exist, setting them should prevent FULL_SENSOR being requested.
    pcall(function()
        if love.window.setHint then
            love.window.setHint("screenorientation", "portrait")
            love.window.setHint("screenorientation", "fixed") -- some builds treat "fixed" as no sensor
        end
    end)

    -- As a fallback, re-apply current mode to force SDL to re-evaluate flags without changing size.
    pcall(function()
        local w, h, flags = love.window.getMode()
        flags = flags or {}
        flags.resizable = false
        love.window.setMode(w, h, flags)
    end)
end

-- Debug logging helpers (prints + Android logcat via logcat fallback)
local function _logcat(tag, msg)
    tag = tag or "BALATRO"
    msg = tostring(msg or "")
    print(tag .. ": " .. msg)
    if love and love.system and love.system.getOS and love.system.getOS() == 'Android' then
        -- Try to write to logcat using io.popen; if unavailable, print above is still useful.
        pcall(function()
            local p = io.popen('log -t "'..tag..'" "'..msg:gsub('"', '\\"')..'"', 'w')
            if p then p:close() end
        end)
    end
end
require "engine/object"
require "bit"
require "engine/string_packer"
require "engine/controller"
require "back"
require "tag"
require "engine/event"
require "engine/node"
require "engine/moveable"
require "engine/sprite"
require "engine/animatedsprite"
require "functions/misc_functions"
require "game"
require "globals"
require "engine/ui"
require "functions/UI_definitions"
require "functions/state_events"
require "functions/common_events"
require "functions/button_callbacks"
require "functions/misc_functions"
require "functions/test_functions"
require "card"
require "cardarea"
require "blind"
require "card_character"
require "engine/particles"
require "engine/text"
require "challenges"

math.randomseed( G.SEED )

function love.run()
	if love.load then love.load(love.arg.parseGameArguments(arg), arg) end

	-- We don't want the first frame's dt to include time taken by love.load.
	if love.timer then love.timer.step() end

	local dt = 0
	local dt_smooth = 1/100
	local run_time = 0

	-- Main loop time.
	return function()
		run_time = love.timer.getTime()
		-- Process events.
		if love.event and G and G.CONTROLLER then
			love.event.pump()
			local _n,_a,_b,_c,_d,_e,_f,touched
			for name, a,b,c,d,e,f in love.event.poll() do
				if name == "quit" then
					if not love.quit or not love.quit() then
						return a or 0
					end
				end
				if name == 'touchpressed' then
					_n = 'mousepressed'
					-- touchpressed signature: (id, x, y, dx, dy, pressure)
					-- 'a' is the touch id (userdata). We want x/y.
					local tx, ty = b, c
					-- Some backends provide normalized touch coordinates (0..1). Convert to pixels if needed.
					if type(tx) == 'number' and type(ty) == 'number' and tx >= 0 and tx <= 1 and ty >= 0 and ty <= 1 then
						local w, h = love.graphics.getDimensions()
						tx, ty = tx * w, ty * h
					end
					_a, _b = tx, ty
					_c = 1
					touched = true
					_logcat("BALATRO_INPUT", string.format("TOUCH: raw=(%s,%s) final=(%s,%s)", tostring(b), tostring(c), tostring(_a), tostring(_b)))
				elseif name == 'mousepressed' then
					_n,_a,_b,_c,_d,_e,_f = name,a,b,c,d,e,f
				else
					love.handlers[name](a,b,c,d,e,f)
				end
			end
			if _n then
				love.handlers['mousepressed'](_a,_b,_c,touched)
			end
		end

		-- Update dt, as we'll be passing it to update
		if love.timer then dt = love.timer.step() end
		dt_smooth = math.min(0.8*dt_smooth + 0.2*dt, 0.1)
		-- Call update and draw
		if love.update then love.update(dt_smooth) end -- will pass 0 if love.timer is disabled

		if love.graphics and love.graphics.isActive() then
			if love.draw then love.draw() end
			love.graphics.present()
		end

		run_time = math.min(love.timer.getTime() - run_time, 0.1)
		G.FPS_CAP = G.FPS_CAP or 500
		if run_time < 1./G.FPS_CAP then love.timer.sleep(1./G.FPS_CAP - run_time) end
	end
end

-- Error handler for debugging crashes
function love.errorhandler(msg)
	-- Log to file for debugging
	local err_msg = "ERROR: " .. tostring(msg) .. "\n" .. debug.traceback()

	-- Try to write to a file
	pcall(function()
		local file = love.filesystem.newFile("crash_log.txt")
		file:open("w")
		file:write(err_msg)
		file:close()
	end)

	-- Display error on screen
	return function()
		love.graphics.clear(0.2, 0, 0, 1)
		love.graphics.setColor(1, 1, 1, 1)
		love.graphics.printf("CRASH LOG:\n\n" .. err_msg, 10, 50, love.graphics.getWidth() - 20)
		love.graphics.present()

		-- Wait for touch to quit
		love.event.pump()
		for e, a in love.event.poll() do
			if e == "quit" or e == "touchpressed" or e == "keypressed" then
				return nil
			end
		end
		love.timer.sleep(0.1)
		return true
	end
end

function love.load()
	-- Early portrait detection for Android/mobile
	local w, h = love.graphics.getDimensions()
	G.F_PORTRAIT = (h > w)

	-- Force portrait orientation on Android at engine level
	local os_name = love.system.getOS()
	if os_name == 'Android' or os_name == 'iOS' then
		-- Set background to dark green (matches game background)
		love.graphics.setBackgroundColor(0.1, 0.2, 0.1, 1)
		G.F_PORTRAIT = true  -- Always portrait on mobile
	end

	-- Android: apply orientation hints ASAP (prevents SDL from requesting FULL_SENSOR later)
	_force_android_portrait_hints()

	G:start_up()
	--Steam integration
	local os = love.system.getOS()
	if os == 'OS X' or os == 'Windows' then
		local st = nil
		--To control when steam communication happens, make sure to send updates to steam as little as possible
		if os == 'OS X' then
			local dir = love.filesystem.getSourceBaseDirectory()
			local old_cpath = package.cpath
			package.cpath = package.cpath .. ';' .. dir .. '/?.so'
			st = require 'luasteam'
			package.cpath = old_cpath
		else
			st = require 'luasteam'
		end

		st.send_control = {
			last_sent_time = -200,
			last_sent_stage = -1,
			force = false,
		}
		if not (st.init and st:init()) then
			love.event.quit()
		end
		--Set up the render window and the stage for the splash screen, then enter the gameloop with :update
		G.STEAM = st
	else
	end

	--Set the mouse to invisible immediately, this visibility is handled in the G.CONTROLLER
	love.mouse.setVisible(false)
end

function love.quit()
	--Steam integration
	if G.SOUND_MANAGER then G.SOUND_MANAGER.channel:push({type = 'stop'}) end
	if G.STEAM then G.STEAM:shutdown() end
end

function love.update( dt )
	--Perf monitoring checkpoint
    timer_checkpoint(nil, 'update', true)
    G:update(dt)
end

function love.draw()
	--Perf monitoring checkpoint
    timer_checkpoint(nil, 'draw', true)
	G:draw()
end

function love.keypressed(key)
	if not _RELEASE_MODE and G.keybind_mapping[key] then love.gamepadpressed(G.CONTROLLER.keyboard_controller, G.keybind_mapping[key])
	else
		G.CONTROLLER:set_HID_flags('mouse')
		G.CONTROLLER:key_press(key)
	end
end

function love.keyreleased(key)
	if not _RELEASE_MODE and G.keybind_mapping[key] then love.gamepadreleased(G.CONTROLLER.keyboard_controller, G.keybind_mapping[key])
	else
		G.CONTROLLER:set_HID_flags('mouse')
		G.CONTROLLER:key_release(key)
	end
end

function love.gamepadpressed(joystick, button)
	button = G.button_mapping[button] or button
	G.CONTROLLER:set_gamepad(joystick)
    G.CONTROLLER:set_HID_flags('button', button)
    G.CONTROLLER:button_press(button)
end

function love.gamepadreleased(joystick, button)
	button = G.button_mapping[button] or button
    G.CONTROLLER:set_gamepad(joystick)
    G.CONTROLLER:set_HID_flags('button', button)
    G.CONTROLLER:button_release(button)
end

function love.mousepressed(x, y, button, touch)
    _logcat("BALATRO_INPUT", string.format("MOUSEPRESSED: x=%s y=%s button=%s touch=%s", tostring(x), tostring(y), tostring(button), tostring(touch)))
    if not (G and G.CONTROLLER) then return end

    -- On Android touch, the controller's cursor position can lag behind the touch.
    -- Force cursor to the tap position so UI hit-testing uses the correct coordinates.
    if touch and G.CONTROLLER.cursor_position then
        G.CONTROLLER.cursor_position.x = x
        G.CONTROLLER.cursor_position.y = y
        if G.CURSOR and G.CURSOR.T then
            G.CURSOR.T.x = x/(G.TILESCALE*G.TILESIZE) - (G.ROOM and G.ROOM.T and G.ROOM.T.x or 0)
            G.CURSOR.T.y = y/(G.TILESCALE*G.TILESIZE) - (G.ROOM and G.ROOM.T and G.ROOM.T.y or 0)
        end
    end

    if G and G.CONTROLLER and G.CONTROLLER.cursor_position then
        _logcat("BALATRO_INPUT", string.format("  CONTROLLER cursor_pos=(%s,%s)", tostring(G.CONTROLLER.cursor_position.x), tostring(G.CONTROLLER.cursor_position.y)))
    end

    G.CONTROLLER:set_HID_flags(touch and 'touch' or 'mouse')
    if button == 1 then
		G.CONTROLLER:queue_L_cursor_press(x, y)
	end
	if button == 2 then
		G.CONTROLLER:queue_R_cursor_press(x, y)
	end
end


function love.mousereleased(x, y, button)
    if button == 1 then G.CONTROLLER:L_cursor_release(x, y) end
end

function love.mousemoved(x, y, dx, dy, istouch)
	G.CONTROLLER.last_touch_time = G.CONTROLLER.last_touch_time or -1
	if next(love.touch.getTouches()) ~= nil then
		G.CONTROLLER.last_touch_time = G.TIMERS.UPTIME
	end
    G.CONTROLLER:set_HID_flags(G.CONTROLLER.last_touch_time > G.TIMERS.UPTIME - 0.2 and 'touch' or 'mouse')
end

function love.joystickaxis( joystick, axis, value )
    if math.abs(value) > 0.2 and joystick:isGamepad() then
		G.CONTROLLER:set_gamepad(joystick)
        G.CONTROLLER:set_HID_flags('axis')
    end
end

function love.errhand(msg)
	if G.F_NO_ERROR_HAND then return end
	msg = tostring(msg)

	if G.SETTINGS.crashreports and _RELEASE_MODE and G.F_CRASH_REPORTS then
		local http_thread = love.thread.newThread([[
			local https = require('https')
			CHANNEL = love.thread.getChannel("http_channel")

			while true do
				--Monitor the channel for any new requests
				local request = CHANNEL:demand()
				if request then
					https.request(request)
				end
			end
		]])
		local http_channel = love.thread.getChannel('http_channel')
		http_thread:start()
		local httpencode = function(str)
			local char_to_hex = function(c)
				return string.format("%%%02X", string.byte(c))
			end
			str = str:gsub("\n", "\r\n"):gsub("([^%w _%%%-%.~])", char_to_hex):gsub(" ", "+")
			return str
		end


		local error = msg
		local file = string.sub(msg, 0,  string.find(msg, ':'))
		local function_line = string.sub(msg, string.len(file)+1)
		function_line = string.sub(function_line, 0, string.find(function_line, ':')-1)
		file = string.sub(file, 0, string.len(file)-1)
		local trace = debug.traceback()
		local boot_found, func_found = false, false
		for l in string.gmatch(trace, "(.-)\n") do
			if string.match(l, "boot.lua") then
				boot_found = true
			elseif boot_found and not func_found then
				func_found = true
				trace = ''
				function_line = string.sub(l, string.find(l, 'in function')+12)..' line:'..function_line
			end

			if boot_found and func_found then
				trace = trace..l..'\n'
			end
		end

		http_channel:push('https://958ha8ong3.execute-api.us-east-2.amazonaws.com/?error='..httpencode(error)..'&file='..httpencode(file)..'&function_line='..httpencode(function_line)..'&trace='..httpencode(trace)..'&version='..(G.VERSION))
	end

	if not love.window or not love.graphics or not love.event then
		return
	end

	if not love.graphics.isCreated() or not love.window.isOpen() then
		local success, status = pcall(love.window.setMode, 800, 600)
		if not success or not status then
			return
		end
	end

	-- Reset state.
	if love.mouse then
		love.mouse.setVisible(true)
		love.mouse.setGrabbed(false)
		love.mouse.setRelativeMode(false)
	end
	if love.joystick then
		-- Stop all joystick vibrations.
		for i,v in ipairs(love.joystick.getJoysticks()) do
			v:setVibration()
		end
	end
	if love.audio then love.audio.stop() end
	love.graphics.reset()
	local font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 20)

	love.graphics.clear(G.C.BLACK)
	love.graphics.origin()


	local p = 'Oops! Something went wrong:\n'..msg..'\n\n'..(not _RELEASE_MODE and debug.traceback() or G.SETTINGS.crashreports and
		'Since you are opted in to sending crash reports, LocalThunk HQ was sent some useful info about what happened.\nDon\'t worry! There is no identifying or personal information. If you would like\nto opt out, change the \'Crash Report\' setting to Off' or
		'Crash Reports are set to Off. If you would like to send crash reports, please opt in in the Game settings.\nThese crash reports help us avoid issues like this in the future')

	local function draw()
		local pos = love.window.toPixels(70)
		love.graphics.push()
		love.graphics.clear(G.C.BLACK)
		love.graphics.setColor(1., 1., 1., 1.)
		love.graphics.printf(p, font, pos, pos, love.graphics.getWidth() - pos)
		love.graphics.pop()
		love.graphics.present()

	end

	while true do
		love.event.pump()

		for e, a, b, c in love.event.poll() do
			if e == "quit" then
				return
			elseif e == "keypressed" and a == "escape" then
				return
			elseif e == "touchpressed" then
				local name = love.window.getTitle()
				if #name == 0 or name == "Untitled" then name = "Game" end
				local buttons = {"OK", "Cancel"}
				local pressed = love.window.showMessageBox("Quit "..name.."?", "", buttons)
				if pressed == 1 then
					return
				end
			end
		end

		draw()

		if love.timer then
			love.timer.sleep(0.1)
		end
	end

end

function love.resize(w, h)
	-- Safety check: Don't process resize if game isn't initialized yet
	if not G or not G.ROOM then
		return
	end

	-- Android: re-apply portrait hints on any resize/config change
	_force_android_portrait_hints()

	-- On mobile: Completely ignore landscape resize events to prevent crash
	local os_name = love.system.getOS()
	if (os_name == 'Android' or os_name == 'iOS') then
		if w > h then
			-- Landscape detected on mobile - ignore this resize completely
			-- Do not process any resize logic for landscape orientation
			return
		end
		-- Force portrait flag
		G.F_PORTRAIT = true
	else
		-- Desktop: detect based on dimensions
		G.F_PORTRAIT = (h > w)
	end

	-- Additional safety check for window_prev
	if not G.window_prev then
		return
	end

	if G.F_PORTRAIT then
		-- PORTRAIT MODE
		-- Use 63% of original width as visible area
		local portrait_scale_factor = 0.63
		G.TILESCALE = w / (G.TILE_W * portrait_scale_factor * G.TILESIZE)

		if G.ROOM then
			-- Room dimensions based on visible area
			G.ROOM.T.w = w / (G.TILESCALE * G.TILESIZE)
			G.ROOM.T.h = h / (G.TILESCALE * G.TILESIZE)
			G.ROOM.T.x = 0
			G.ROOM.T.y = 0

			G.ROOM_ATTACH.T.w = G.ROOM.T.w
			G.ROOM_ATTACH.T.h = G.ROOM.T.h
			G.ROOM_ATTACH.T.x = G.ROOM.T.x
			G.ROOM_ATTACH.T.y = G.ROOM.T.y

			G.ROOM_ORIG = {
				x = G.ROOM.T.x,
				y = G.ROOM.T.y,
				r = G.ROOM.T.r
			}

			if G.buttons then G.buttons:recalculate() end
			if G.HUD then G.HUD:recalculate() end

			-- Update game element positions for portrait mode
			set_screen_positions()
		end
	else
		-- LANDSCAPE MODE (original logic)
		if w/h < 1 then
			h = w/1
		end

		if w/h < G.window_prev.orig_ratio then
			G.TILESCALE = G.window_prev.orig_scale*w/G.window_prev.w
		else
			G.TILESCALE = G.window_prev.orig_scale*h/G.window_prev.h
		end

		if G.ROOM then
			G.ROOM.T.w = G.TILE_W
			G.ROOM.T.h = G.TILE_H
			G.ROOM_ATTACH.T.w = G.TILE_W
			G.ROOM_ATTACH.T.h = G.TILE_H

			if w/h < G.window_prev.orig_ratio then
				G.ROOM.T.x = G.ROOM_PADDING_W
				G.ROOM.T.y = (h/(G.TILESIZE*G.TILESCALE) - (G.ROOM.T.h+G.ROOM_PADDING_H))/2 + G.ROOM_PADDING_H/2
			else
				G.ROOM.T.y = G.ROOM_PADDING_H
				G.ROOM.T.x = (w/(G.TILESIZE*G.TILESCALE) - (G.ROOM.T.w+G.ROOM_PADDING_W))/2 + G.ROOM_PADDING_W/2
			end

			G.ROOM_ORIG = {
				x = G.ROOM.T.x,
				y = G.ROOM.T.y,
				r = G.ROOM.T.r
			}

			if G.buttons then G.buttons:recalculate() end
			if G.HUD then G.HUD:recalculate() end
		end
	end

	G.WINDOWTRANS = {
		x = 0, y = 0,
		w = G.TILE_W+2*G.ROOM_PADDING_W,
		h = G.TILE_H+2*G.ROOM_PADDING_H,
		real_window_w = w,
		real_window_h = h
	}

	G.CANV_SCALE = 1

	if love.system.getOS() == 'Windows' and false then --implement later if needed
		local render_w, render_h = love.window.getDesktopDimensions(G.SETTINGS.WINDOW.selcted_display)
		local unscaled_dims = love.window.getFullscreenModes(G.SETTINGS.WINDOW.selcted_display)[1]

		local DPI_scale = math.floor((0.5*unscaled_dims.width/render_w + 0.5*unscaled_dims.height/render_h)*500 + 0.5)/500

		if DPI_scale > 1.1 then
			G.CANV_SCALE = 1.5

			G.AA_CANVAS = love.graphics.newCanvas(G.WINDOWTRANS.real_window_w*G.CANV_SCALE, G.WINDOWTRANS.real_window_h*G.CANV_SCALE, {type = '2d', readable = true})
			G.AA_CANVAS:setFilter('linear', 'linear')
		else
			G.AA_CANVAS = nil
		end
	end

	G.CANVAS = love.graphics.newCanvas(w*G.CANV_SCALE, h*G.CANV_SCALE, {type = '2d', readable = true})
	G.CANVAS:setFilter('linear', 'linear')
end
