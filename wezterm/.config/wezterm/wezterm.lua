local wezterm = require("wezterm")

local c = wezterm.config_builder()

c.color_schemes = {
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
}

c.color_scheme = "OneDark"

c.default_cursor_style = "BlinkingBar"
c.animation_fps = 1
c.cursor_blink_ease_in = "Constant"
c.cursor_blink_ease_out = "Constant"

c.front_end = "OpenGL"

c.window_padding = {
	left = 1,
	right = 1,
	top = 1,
	bottom = 1,
}

c.window_background_opacity = 0.95
c.enable_tab_bar = false
c.window_close_confirmation = "NeverPrompt"

c.font = wezterm.font("Cascadia Code NF", {
	stretch = "ExtraCondensed",
})
c.font_size = 11.0

c.initial_rows = 50
c.initial_cols = 200

c.audible_bell = "Disabled"

local use_wsl = true

if string.find(wezterm.target_triple, "windows") and use_wsl then
	local wsl_domains = wezterm.default_wsl_domains()
	c.wsl_domains = wsl_domains

	if #wsl_domains > 0 then
		local default_distro_name = "arch"
		local found = false

		for _, domain in ipairs(wsl_domains) do
			if string.find(domain.name, default_distro_name) then
				c.default_domain = domain.name
				found = true
				break
			end
		end

		-- fallback to the first distro
		if not found then
			c.default_domain = wsl_domains[1].name
		end
	end
end

local act = wezterm.action
local mod = "ALT"

c.keys = {
	{ key = "v", mods = mod, action = act.SplitHorizontal({ domain = "CurrentPaneDomain" }) },
	{ key = "h", mods = mod, action = act.SplitVertical({ domain = "CurrentPaneDomain" }) },

	{ key = "d", mods = mod, action = act.ShowTabNavigator },
	{ key = "c", mods = mod, action = act.SpawnTab("CurrentPaneDomain") },

	{ key = "q", mods = mod, action = act.CloseCurrentPane({ confirm = false }) },
}

return c
