local o = vim.opt
local g = vim.g

-- rounded window borders
o.winborder = "rounded"
-- start in empty buffer if no file is specified
o.shortmess = "I"

-- we have a nerd font
g.have_nerd_font = true

-- indent options
local indent_size = 2
o.tabstop = indent_size
o.softtabstop = indent_size
o.shiftwidth = indent_size
o.expandtab = true

-- relative line numbers
o.relativenumber = true

-- markdown force indent settings
vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.tabstop = indent_size
    vim.opt_local.softtabstop = indent_size
    vim.opt_local.shiftwidth = indent_size
  end,
})
-- make comments work in json files
vim.api.nvim_create_autocmd("FileType", {
  pattern = "json",
  callback = function()
    vim.opt_local.filetype = "jsonc"
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = "go",
  callback = function()
    vim.bo.makeprg = "go build ."
    vim.bo.errorformat = "%f:%l:%c: %m"
    vim.bo.expandtab = true
  end,
})

-- line numbers
o.number = true

-- disable line wrapping
o.wrap = false

-- disable highlighting after search
o.hlsearch = false
-- highlight while typing search
o.incsearch = true

-- number of lines to keep above and below cursor
o.scrolloff = 8

-- no swap files
o.swapfile = false

-- enable mouse support
o.mouse = "a"

-- persistent undo
o.undofile = true

-- window title shows file name
o.title = true

-- ignore case in search patterns
o.ignorecase = true
o.smartcase = true

-- honestly i don't remember what this does
o.foldmethod = "expr"
o.foldexpr = "v:lua.vim.treesitter.foldexpr()"
o.foldtext = "v:lua.vim.treesitter.foldtext()"
vim.api.nvim_command(
  "autocmd BufEnter * if !exists('b:entered_once') | let b:entered_once = 1 | set nofoldenable | endif"
)
