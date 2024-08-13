local o = vim.opt
local g = vim.g

local indent_size = 2
o.tabstop = indent_size
o.softtabstop = indent_size
o.shiftwidth = indent_size
o.expandtab = true

o.relativenumber = true

o.clipboard:append("unnamedplus")

o.nu = true

o.wrap = false

o.hlsearch = false
o.incsearch = true

o.scrolloff = 8
o.updatetime = 50

o.mouse = "a"

o.undofile = true

o.title = true
