return {
	{
		"folke/which-key.nvim",
		event = "VeryLazy",
		init = function()
		end,
		opts = {},
    config = function ()
      vim.o.timeout = true
      vim.o.timeoutlen = 300

      local remaps = require("config.remaps")
      remaps.remap()
        
      local wk = require("which-key")

      wk.add(remaps.wk_remaps)
    end
	},
}
