PORTRAIT_CONFIG = {
    scale_factor = 0.63,
    hud_top_space = 13,
    bottom_margin = 0.35,
    splash_scale_mult = 10 / 13,
    card_scale = 0.8,
    button = {
        width = 4,
        height = 2,
        text_scale = 0.8,
        width_landscape = 3.2,
        height_landscape = 1.3,
        text_scale_landscape = 0.45,
    },
    blind = {
        scale = 0.34,
        dim = 1.0,
        scale_landscape = 0.4,
        dim_landscape = 1.5,
    },
    row_sizes = {3, 4, 4},
    row_sizes_landscape = {5, 6},
    tab_breakpoints = {
        rows_5_6 = 3,
        rows_7_plus = 4,
    },
    challenge_page_size = 5,
    challenge_page_size_landscape = 10,
    jokers_y = 11,
    anti_jitter_threshold = 3.5,
    fps_cap = 60,
    safe_area_y = 0.85,
    tooltip_screen_padding = 0.12,
    tooltip_touch_gap = 1.6,
    main_menu = {
        x_offset_base = 0.1,
        x_offset_plus = 0.2,
        y_offset_base = -1.55,
        corner_y_offset = -2.15,
    },
    view_deck_scale = 0.8,
    game_over_scale = 1.2,
    game_over_scale_landscape = 1.5,
    tag_align = {
        first_x_left = -0.2,
        first_x_right = 0.2,
    },
    usable_w_factor = 0.96,
    hand_screen_padding = 0.28,
    hand_base_offset = 3.1,
    discard_x_offset = 0.3,
    mobile_ui = {
        hud_scale_tall = 0.39,
        hud_scale_normal = 0.42,
        hud_scale_short = 0.46,
        hud_panel_minw = 8.4,
        hud_top_right_minw = 4.22,
        hud_score_minw = 4.1,
        hud_chip_box_minw = 2.95,
        hud_chip_label_minw = 1.18,
        hud_current_hand_minw = 4.1,
        hud_hand_meter_minw = 1.88,
        hud_money_minw = 3.05,
        hud_spacing = 0.07,
        hud_stat_pad = 0.035,
        hud_stat_minw = 1.16,
        hud_stat_label_scale = 0.68,
        hud_stat_count_scale = 1.72,
        hud_stats_gap = 0.1,
        hud_blind_minw = 3.62,
        hud_blind_minh = 3.12,
        hud_blind_body_minh = 1.92,
        hud_blind_dim = 0.82,
        hud_blind_name_h = 0.46,
        hud_blind_name_minw = 2.38,
        hud_blind_name_scale = 1.42,
        hud_blind_body_pad = 0.018,
        hud_blind_body_maxw = 3.12,
        hud_blind_lower_pad = 0.02,
        hud_blind_score_minw = 2.15,
        hud_blind_score_maxw = 2.05,
        hud_blind_score_label_scale = 0.29,
        hud_blind_reward_scale = 0.29,
        hud_blind_dollar_scale = 0.4,
        hud_blind_line_h = 0.24,
        hud_blind_debuff_scale = 0.88,
        hud_blind_chip_row_h = 0.48,
        hud_blind_reward_h = 0.34,
        hud_button_minw = 2.0,
        hud_button_minh = 0.82,
        run_setup_back_desc_scale = 0.72,
        run_setup_back_min_dims = 0.76,
        run_setup_back_desc_h = 1.9,
        blind_choice = {
            prompt_pad = 0.05,
            prompt_scale_1 = 0.72,
            prompt_scale_2 = 0.8,
            choice_pad = 0.02,
            wrapper_pad = 0.012,
            wrapper_inner_pad = 0.018,
            panel_pad = 0.018,
            inner_pad = 0.026,
            button_pad = 0.018,
            button_scale = 0.62,
            name_scale = 0.62,
            desc_scale = 0.46,
            score_label_scale = 0.42,
            reward_scale = 0.46,
            chip_size = 1.6,
            score_minw = 2.95,
            text_maxw = 2.75,
            tag_pad = 0.012,
            tag_button_pad = 0.018,
            tag_skip_scale = 0.6,
            tag_reward_scale = 0.5,
        },
        shop_sign = {
            w = 2.85,
            h = 1.43,
            panel_w = 3.18,
            panel_h = 1.95,
            text_scale = 0.34,
        },
    },
}

function get_portrait_scale(w, h)
    local aspect = h / w
    if aspect > 2.2 then
        return 0.58
    elseif aspect > 1.8 then
        return 0.63
    elseif aspect > 1.5 then
        return 0.70
    else
        return 0.80
    end
end

function apply_portrait_tooltip_fit(config)
    if config and G and G.F_PORTRAIT then
        if config.can_collide == nil then config.can_collide = false end
        if config.can_drag == nil then config.can_drag = false end
        if config.fit_to_room == nil then config.fit_to_room = true end
        if config.fit_to_room then
            config.lr_clamp = false
        elseif config.lr_clamp == nil then
            config.lr_clamp = true
        end
        if config.touch_above_cursor == nil then config.touch_above_cursor = true end
        if config.snap_to_fit == nil then config.snap_to_fit = true end
    end

    return config
end

function prepare_portrait_popup_fit(box)
    if not (G and G.F_PORTRAIT and box) then return end

    if box.config then
        apply_portrait_tooltip_fit(box.config)
    end
    if box.states then
        if box.states.collide then box.states.collide.can = false end
        if box.states.drag then box.states.drag.can = false end
    end

    if box.align_to_major then box:align_to_major() end
    if box.fit_to_room then box:fit_to_room() end
    if box.hard_set_VT then box:hard_set_VT() end
    if box.UIRoot and box.UIRoot.initialize_VT then
        box.UIRoot:initialize_VT(true)
    end
end

function get_portrait_room_fit_delta(box, opts)
    opts = opts or {}

    if not (G and G.F_PORTRAIT and G.ROOM and G.ROOM.T and box and box.T) then
        return 0, 0
    end

    local room_w = G.ROOM.T.w or 0
    local room_h = G.ROOM.T.h or 0
    if room_w <= 0 or room_h <= 0 then return 0, 0 end

    local padding = opts.screen_padding or (PORTRAIT_CONFIG and PORTRAIT_CONFIG.tooltip_screen_padding) or 0.12
    local left = padding
    local top = padding
    local right = math.max(left, room_w - padding)
    local bottom = math.max(top, room_h - padding)
    local min_x = box.T.x
    local min_y = box.T.y
    local max_x = box.T.x + box.T.w
    local max_y = box.T.y + box.T.h
    local dx = 0
    local dy = 0

    if opts.touch_above_cursor and G.CONTROLLER and G.CONTROLLER.HID and G.CONTROLLER.HID.touch and G.CONTROLLER.cursor_position and G.TILESCALE and G.TILESIZE then
        local touch_gap = opts.touch_gap or (PORTRAIT_CONFIG and PORTRAIT_CONFIG.tooltip_touch_gap) or 1.25
        local cursor_y = G.CONTROLLER.cursor_position.y / (G.TILESCALE * G.TILESIZE) - (G.ROOM.T.y or 0)
        local desired_bottom = cursor_y - touch_gap
        if max_y + dy > desired_bottom then
            dy = desired_bottom - max_y
        end
    end

    if box.T.w >= (right - left) then
        dx = left - min_x
    else
        if min_x + dx < left then dx = left - min_x end
        if max_x + dx > right then dx = right - max_x end
    end

    if box.T.h >= (bottom - top) then
        dy = top - min_y
    else
        if min_y + dy < top then dy = top - min_y end
        if max_y + dy > bottom then dy = bottom - max_y end
    end

    return dx, dy
end

function fit_portrait_side_tooltip(box, parent)
    if not (G and G.F_PORTRAIT and G.ROOM and G.ROOM.T and box and box.T and parent) then return end

    local padding = (PORTRAIT_CONFIG and PORTRAIT_CONFIG.tooltip_screen_padding) or 0.12
    if box.T.x < padding then
        box:set_alignment({
            major = parent,
            type = 'cr',
            bond = 'Strong',
            offset = {x = 0.03, y = 0},
            lr_clamp = false
        })
        box:align_to_major()
    end

    box.config.fit_to_room = true
    box.config.lr_clamp = false
    box.config.touch_above_cursor = false
    box.config.screen_padding = padding
    if box.fit_to_room then box:fit_to_room() end
    if prepare_portrait_popup_fit then
        prepare_portrait_popup_fit(box)
    elseif box.UIRoot and box.UIRoot.initialize_VT then
        box.UIRoot:initialize_VT()
    end
end

function get_portrait_side_tooltip_config(parent)
    local align = 'cl'
    local offset = {x = -0.03, y = 0}
    if G and G.F_PORTRAIT and G.ROOM and G.ROOM.T and parent and parent.T then
        local parent_cx = parent.T.x + parent.T.w/2
        if parent_cx < G.ROOM.T.w/2 then
            align = 'cr'
            offset = {x = 0.03, y = 0}
        end
    end
    return align, offset
end
