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

vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = { "*.mconf" },
  callback = function()
    local file = vim.fn.expand("%:t")
    local json_file = vim.fn.expand("%:t:r") .. ".json"

    local out = vim.fn.system("mconf -j " .. file)

    if vim.v.shell_error == 0 then
      local f = io.open(json_file, "w")
      if f == nil then
        vim.notify("Failed to open file: " .. json_file, vim.log.levels.ERROR)
        return
      end
      f:write(out)
      f:close()
    else
      vim.notify("mconf to json transpilation failed:\n" .. out, vim.log.levels.ERROR)
    end
  end,
})

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

return {
  ---@type "telescope" | "builtin" | "none"
  startup = "none",
}
