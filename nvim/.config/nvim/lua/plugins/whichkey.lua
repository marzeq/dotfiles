return {
	{
		"folke/which-key.nvim",
		event = "VeryLazy",
		init = function()
			vim.o.timeout = true
			vim.o.timeoutlen = 300

			local wk = require("which-key")
			require("config.remaps").remap()
		end,
		opts = {},
    keys = require("config.remaps").wk_remaps
	},
}
