local wezterm = require("wezterm")

local config = {
	color_schemes = {
		OneDark = {
			background = "#1e2127",
			foreground = "#abb2bf",

			cursor_fg = "#282c34",
      cursor_border = "#abb2bf",
      cursor_bg = "#abb2bf",

			selection_bg = "#3e4452",
			selection_fg = "#abb2bf",
			ansi = {
				"#282c34",
				"#e06c75",
				"#98c379",
				"#d19a66",
				"#61afef",
				"#c678dd",
				"#56b6c2",
				"#abb2bf",
			},
			brights = {
				"#5c6370",
				"#e06c75",
				"#98c379",
				"#d19a66",
				"#61afef",
				"#c678dd",
				"#56b6c2",
				"#abb2bf",
			},
		},
	},

	color_scheme = "OneDark",

	default_cursor_style = "BlinkingBar",
	animation_fps = 1,
	cursor_blink_ease_in = "Constant",
	cursor_blink_ease_out = "Constant",

	front_end = "OpenGL",

	window_padding = {
		left = 1,
		right = 1,
		top = 1,
		bottom = 1,
	},
	window_background_opacity = 0.95,
	enable_tab_bar = false,
	window_close_confirmation = "NeverPrompt",

	font = wezterm.font("Cascadia Code NF", {
		stretch = "ExtraCondensed",
	}),
	font_size = 11.0,

	initial_rows = 50,
	initial_cols = 200,
}

if string.find(wezterm.target_triple, "windows") then
	config.default_prog = { "wsl.exe", "~" }
end

return config
