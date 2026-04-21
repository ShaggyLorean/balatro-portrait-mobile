if (love.system.getOS() == 'OS X' ) and (jit.arch == 'arm64' or jit.arch == 'arm') then jit.off() end

local function _force_android_portrait_hints()
    if not (love and love.system and love.system.getOS and love.system.getOS() == 'Android') then return end
    if not (love and love.window and love.window.setMode) then return end

    pcall(function()
        if love.window.setHint then
            love.window.setHint("screenorientation", "portrait")
            love.window.setHint("screenorientation", "fixed")
        end
    end)

    pcall(function()
        local w, h, flags = love.window.getMode()
        flags = flags or {}
        flags.resizable = false
        love.window.setMode(w, h, flags)
    end)
end

local function _logcat(tag, msg)
    if _RELEASE_MODE then return end
    tag = tag or "BALATRO"
    msg = tostring(msg or "")
    print(tag .. ": " .. msg)
    if love and love.system and love.system.getOS and love.system.getOS() == 'Android' then
        pcall(function()
            local p = io.popen('log -t "'..tag..'" "'..msg:gsub('"', '\\"')..'"', 'w')
            if p then p:close() end
        end)
    end
end
require "engine/object"
require "bit"
require "engine/string_packer"
require "portrait_config"
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

	if love.timer then love.timer.step() end

	local dt = 0
	local dt_smooth = 1/100
	local run_time = 0

	return function()
		run_time = love.timer.getTime()
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
					local tx, ty = b, c
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

		if love.timer then dt = love.timer.step() end
		dt_smooth = math.min(0.8*dt_smooth + 0.2*dt, 0.1)
		if love.update then love.update(dt_smooth) end

		if love.graphics and love.graphics.isActive() then
			if love.draw then love.draw() end
			love.graphics.present()
		end

		run_time = math.min(love.timer.getTime() - run_time, 0.1)
		
		local os_name = (love and love.system and love.system.getOS) and love.system.getOS() or 'Windows'
		local is_mobile = (os_name == 'Android' or os_name == 'iOS')
		G.FPS_CAP = G.FPS_CAP or (is_mobile and (PORTRAIT_CONFIG and PORTRAIT_CONFIG.fps_cap or 60) or 500)
		
		if run_time < 1./G.FPS_CAP then love.timer.sleep(1./G.FPS_CAP - run_time) end
	end
end

function love.load()
	local w, h = love.graphics.getDimensions()
	G.F_PORTRAIT = (h > w)

	local os_name = love.system.getOS()
	if os_name == 'Android' or os_name == 'iOS' then
		love.graphics.setBackgroundColor(0.1, 0.2, 0.1, 1)
		G.F_PORTRAIT = true

		pcall(function()
			love.window.setFullscreen(true, 'desktop')
		end)

		pcall(function()
			if love.window.setDisplaySleepEnabled then
				love.window.setDisplaySleepEnabled(false)
			end
		end)
	end

	_force_android_portrait_hints()

	G:start_up()
	local os = love.system.getOS()
	if os == 'OS X' or os == 'Windows' then
		local st = nil
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
		G.STEAM = st
	else
	end

	love.mouse.setVisible(false)
end

function love.quit()
	if G.SOUND_MANAGER then G.SOUND_MANAGER.channel:push({type = 'stop'}) end
	if G.STEAM then G.STEAM:shutdown() end
end

G._needs_canvas_refresh = false

function love.visible(v)
    if not v and G and G.SAVE_MANAGER and G.STAGE == G.STAGES.RUN then
        pcall(function() G:save_progress() end)
    end
    if v then
        G._needs_canvas_refresh = true
    end
end

function love.update( dt )
    timer_checkpoint(nil, 'update', true)
    if G._needs_canvas_refresh then
        G._needs_canvas_refresh = false
        local os_name = love.system.getOS()
        if (os_name == 'Android' or os_name == 'iOS') and G and G.ROOM then
            local w, h = love.graphics.getDimensions()
            if w > 0 and h > 0 and G.TILESCALE and h > w then
                love.graphics.setScissor()
                love.graphics.origin()
                love.graphics.clear(0, 0, 0, 1)
                if G.CANVAS then
                    G.CANVAS:release()
                    G.CANVAS = nil
                end
                love.resize(w, h)
            end
        end
    end
    G:update(dt)
end

function love.draw()
    timer_checkpoint(nil, 'draw', true)
    local os_name = love.system.getOS()
    if (os_name == 'Android' or os_name == 'iOS') and G and G.CANVAS then
        local screen_w = love.graphics.getWidth()
        local screen_h = love.graphics.getHeight()
        local canvas_w = G.CANVAS:getWidth() / (G.CANV_SCALE or 1)
        local canvas_h = G.CANVAS:getHeight() / (G.CANV_SCALE or 1)
        if math.abs(screen_w - canvas_w) > 2 or math.abs(screen_h - canvas_h) > 2 then
            love.resize(screen_w, screen_h)
        end
    end
	G:draw()
end

function love.keypressed(key)
	local os_name = (love and love.system and love.system.getOS) and love.system.getOS() or nil
	if G and G.CONTROLLER and G.CONTROLLER.text_input_hook and (os_name == 'Android' or os_name == 'iOS') then
		local allow_key = key == 'backspace' or key == 'delete' or key == 'left' or key == 'right' or key == 'return' or key == 'enter' or key == 'escape'
		if not allow_key then
			return
		end
	end

	if key == 'back' or (key == 'escape' and love.system.getOS() == 'Android') then
		if G.OVERLAY_MENU then
			G.FUNCS.exit_overlay_menu()
		elseif G.STAGE == G.STAGES.RUN and G.STATE ~= G.STATES.GAME_OVER then
			G.FUNCS.options()
		end
		return
	end
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

function love.textinput(text)
    if not (G and G.CONTROLLER and G.CONTROLLER.text_input_hook and text and text ~= '') then
        return
    end

    if utf8 and utf8.codes and utf8.char then
        for _, codepoint in utf8.codes(text) do
            G.CONTROLLER:key_press_update(utf8.char(codepoint))
        end
    else
        for i = 1, #text do
            G.CONTROLLER:key_press_update(text:sub(i, i))
        end
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

	if istouch and math.abs(dx) < PORTRAIT_CONFIG.anti_jitter_threshold and math.abs(dy) < PORTRAIT_CONFIG.anti_jitter_threshold then
		return
	end

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

	local full_trace = debug.traceback()
	local crash_text = msg .. "\n\n" .. full_trace

	pcall(function()
		local file = love.filesystem.newFile("crash_log.txt")
		file:open("w")
		file:write("Balatro Portrait Mobile - Crash Log\n")
		file:write("Version: " .. tostring(G.VERSION or "unknown") .. "\n")
		file:write("OS: " .. love.system.getOS() .. "\n")
		file:write("Time: " .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
		file:write("\n" .. crash_text .. "\n")
		file:close()
	end)

	pcall(function()
		if love.system and love.system.setClipboardText then
			love.system.setClipboardText(crash_text)
		end
	end)

	if G.SETTINGS.crashreports and _RELEASE_MODE and G.F_CRASH_REPORTS then
		local http_thread = love.thread.newThread([[
			local https = require('https')
			CHANNEL = love.thread.getChannel("http_channel")

			while true do
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

	if love.mouse then
		love.mouse.setVisible(true)
		love.mouse.setGrabbed(false)
		love.mouse.setRelativeMode(false)
	end
	if love.joystick then
		for i,v in ipairs(love.joystick.getJoysticks()) do
			v:setVibration()
		end
	end
	if love.audio then love.audio.stop() end
	love.graphics.reset()

	local font = nil
	pcall(function()
		font = love.graphics.setNewFont("resources/fonts/TypoQuik-Bold.ttf", 18)
	end)
	if not font then
		pcall(function()
			font = love.graphics.setNewFont("resources/fonts/m6x11plus.ttf", 18)
		end)
	end
	if not font then
		font = love.graphics.newFont(18)
	end

	love.graphics.clear(0, 0, 0, 1)
	love.graphics.origin()

	local clipboard_ok = false
	pcall(function()
		clipboard_ok = love.system.getClipboardText() == crash_text
	end)

	local header = "=== CRASH ===\n"
	header = header .. "Log saved to crash_log.txt\n"
	if clipboard_ok then
		header = header .. "Log copied to clipboard!\n"
	end
	header = header .. "\nPress BACK button or ESC to exit.\n"
	header = header .. "Touch to scroll. Do NOT close app to read log.\n\n"

	local p = header .. msg .. '\n\n' .. (not _RELEASE_MODE and full_trace or '')

	local scroll_y = 0

	local function draw()
		local pos = love.window.toPixels(20)
		local w = love.graphics.getWidth()
		love.graphics.push()
		love.graphics.clear(0.15, 0, 0, 1)
		love.graphics.setColor(1, 1, 1, 1)
		love.graphics.printf(p, font, pos, pos + scroll_y, w - pos * 2)
		love.graphics.pop()
		love.graphics.present()
	end

	while true do
		love.event.pump()

		for e, a, b, c in love.event.poll() do
			if e == "quit" then
				return
			elseif e == "keypressed" and (a == "escape" or a == "back") then
				return
			elseif e == "touchpressed" then
				scroll_y = 0
			elseif e == "mousepressed" then
				scroll_y = 0
			elseif e == "wheelmoved" then
				scroll_y = scroll_y + (b or 0) * 30
				scroll_y = math.min(scroll_y, 0)
			end
		end

		draw()

		if love.timer then
			love.timer.sleep(0.1)
		end
	end

end

function love.resize(w, h)
	if not G or not G.ROOM then
		return
	end

	love.graphics.setScissor()
	love.graphics.origin()
	love.graphics.clear(0, 0, 0, 1)

	_force_android_portrait_hints()

	local os_name = love.system.getOS()
	if (os_name == 'Android' or os_name == 'iOS') then
		if w > h then
			if G.CANVAS then G.CANVAS:release() end
			G.CANVAS = love.graphics.newCanvas(w*G.CANV_SCALE, h*G.CANV_SCALE, {type = '2d', readable = true})
			if G.CANVAS then G.CANVAS:setFilter('linear', 'linear') end
			return
		end
		G.F_PORTRAIT = true
	else
		G.F_PORTRAIT = (h > w)
	end

	if not G.window_prev then
		return
	end

	if G.F_PORTRAIT then
		local portrait_scale_factor = get_portrait_scale(w, h)
		G.TILESCALE = w / (G.TILE_W * portrait_scale_factor * G.TILESIZE)

		if G.ROOM then
			G.ROOM.T.w = w / (G.TILESCALE * G.TILESIZE)
			G.ROOM.T.h = h / (G.TILESCALE * G.TILESIZE)
			G.ROOM.T.x = 0
			G.ROOM.T.y = (os_name == 'Android' or os_name == 'iOS') and (PORTRAIT_CONFIG.safe_area_y) or 0

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

			set_screen_positions()
		end
	else
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

	if love.system.getOS() == 'Windows' and false then
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

	if G.CANVAS then G.CANVAS:release() end
	G.CANVAS = love.graphics.newCanvas(w*G.CANV_SCALE, h*G.CANV_SCALE, {type = '2d', readable = true})
	G.CANVAS:setFilter('linear', 'linear')
	
	love.graphics.setScissor()
	love.graphics.origin()
	
	if G.OVERLAY_MENU then
		local menu_config = G.OVERLAY_MENU.config or {}
		local is_game_over = (G.STATE == G.STATES.GAME_OVER)
		
		G.OVERLAY_MENU:remove()
		G.OVERLAY_MENU = nil
		
		if is_game_over then
			G.FUNCS.overlay_menu{
				definition = create_UIBox_game_over(),
				config = {no_esc = true}
			}
		end
	end
end
