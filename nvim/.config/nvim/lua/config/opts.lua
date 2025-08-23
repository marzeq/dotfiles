local o = vim.opt
local g = vim.g

o.winborder = "rounded"
o.shortmess = "I"

g.have_nerd_font = true

local indent_size = 2
o.tabstop = indent_size
o.softtabstop = indent_size
o.shiftwidth = indent_size
o.expandtab = true

o.relativenumber = true

vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.tabstop = indent_size
    vim.opt_local.softtabstop = indent_size
    vim.opt_local.shiftwidth = indent_size
  end,
})
vim.api.nvim_create_autocmd("FileType", {
  pattern = "json",
  callback = function()
    vim.opt_local.filetype = "jsonc"
  end,
})

vim.schedule(function()
  o.clipboard:append("unnamedplus")
end)

o.nu = true

o.wrap = false

o.hlsearch = false
o.incsearch = true

o.scrolloff = 8
o.updatetime = 50

o.mouse = "a"

o.undofile = true

o.title = true

o.ignorecase = true
o.smartcase = true

o.foldmethod = "expr"
o.foldexpr = "v:lua.vim.treesitter.foldexpr()"
o.foldtext = "v:lua.vim.treesitter.foldtext()"
vim.api.nvim_command(
  "autocmd BufEnter * if !exists('b:entered_once') | let b:entered_once = 1 | set nofoldenable | endif"
)
