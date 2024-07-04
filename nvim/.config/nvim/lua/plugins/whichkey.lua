return {
	{
		"folke/which-key.nvim",
		event = "VeryLazy",
		init = function()
			vim.o.timeout = true
			vim.o.timeoutlen = 300

			local wk = require("which-key")
			require("config.remaps").remap()
			local wk_remaps = require("config.remaps").wk_remaps

			for i = 1, #wk_remaps do
				wk.register(wk_remaps[i].mappings, wk_remaps[i].options)
			end
		end,
		opts = {},
	},
}
