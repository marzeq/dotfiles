return {
	{
		"joshdick/onedark.vim",
		lazy = false,
		priority = 1000,
		config = function()
			if vim.fn.empty(vim.env.TMUX) == 1 then
				if vim.fn.has("nvim") == 1 then
					vim.env.NVIM_TUI_ENABLE_TRUE_COLOR = 1
				end

				if vim.fn.has("termguicolors") == 1 then
					vim.o.termguicolors = true
				end
			end

			local colors = vim.fn["onedark#GetColors"]()

			vim.cmd("syntax on")
			vim.cmd.colorscheme("onedark")
			vim.api.nvim_set_hl(0, "Normal", { bg = "none" })
			vim.api.nvim_set_hl(0, "NormalFloat", { bg = colors.background.gui })
		end,
	},
}
