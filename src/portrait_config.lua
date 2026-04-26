PORTRAIT_CONFIG = {
    scale_factor = 0.63,
    hud_top_space = 13,
    bottom_margin = 0.5,
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
        scale = 0.3,
        dim = 1.1,
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
    safe_area_y = 0.5,
    main_menu = {
        x_offset_base = 0.7,
        x_offset_plus = 0.2,
        y_offset_base = -1.2,
    },
    view_deck_scale = 0.8,
    game_over_scale = 1.2,
    game_over_scale_landscape = 1.5,
    tag_align = {
        first_x_left = -0.2,
        first_x_right = 0.2,
    },
    usable_w_factor = 0.96,
    hand_base_offset = 3.5,
    discard_x_offset = 0.3,
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
