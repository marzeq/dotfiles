require("config.opts")

-- set leader before loading lazy
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"
vim.keymap.set("", "<Space>", "<Nop>")

require("config.lazy")

vim.api.nvim_create_autocmd("VimEnter", {
	callback = function()
		if vim.fn.argc() == 0 or vim.fn.line2byte("$") ~= -1 and not vim.opt.insertmode then
			vim.cmd("Telescope find_files")
		end
	end,
})
