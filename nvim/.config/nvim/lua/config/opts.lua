local o = vim.opt
local g = vim.g

g.have_nerd_font = true

local indent_size = 2
o.tabstop = indent_size
o.softtabstop = indent_size
o.shiftwidth = indent_size
o.expandtab = true

vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.tabstop = indent_size
    vim.opt_local.softtabstop = indent_size
    vim.opt_local.shiftwidth = indent_size
  end,
})
vim.api.nvim_create_autocmd("FileType", {
  pattern = "go",
  callback = function()
    vim.opt_local.expandtab = false
  end,
})
vim.api.nvim_create_autocmd("FileType", {
  pattern = "json",
  callback = function()
    vim.opt_local.filetype = "jsonc"
  end,
})
vim.api.nvim_command("au BufNewFile,BufRead *.rasi set filetype=css")

o.relativenumber = true

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

vim.cmd('let @t="yypwv$hr─i└─\\<Esc>$a─┘\\<Esc>yyka │\\<Esc>^wi│ \\<Esc>Pwxi┌\\<Esc>$xa┐\\<Esc>j^ww"') -- neat macro for making a title header comment

return {
  ---@type "telescope" | "builtin" | "none"
  startup = "none",
}
