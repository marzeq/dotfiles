return {
	{
		"aznhe21/actions-preview.nvim",
		dependencies = { "nvim-telescope/telescope.nvim" },
		config = function()
			require("actions-preview").setup({
				backend = { "telescope" },
			})

      require("config.remaps").wk_remaps[1].mappings.a.a = { require("actions-preview").code_actions, "Code actions" }
   end,
	},
}
