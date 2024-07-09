return {
	{
		"github/copilot.vim",
	},
	{
		"CopilotC-Nvim/CopilotChat.nvim",
		branch = "canary",
		dependencies = {
			{ "nvim-lua/plenary.nvim" }, -- for curl, log wrapper
		},
		opts = {},
	},
}
