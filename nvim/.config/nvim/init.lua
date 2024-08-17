local custom_opts = require("config.opts")

-- set leader before loading lazy
vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.keymap.set("", "<Space>", "<Nop>")

require("config.lazy")

if custom_opts.startup == "telescope" then
  vim.api.nvim_create_autocmd("VimEnter", {
    callback = function()
      if vim.fn.argc() == 0 or vim.fn.line2byte("$") ~= -1 and not vim.opt.insertmode then
        require("telescope.builtin").find_files({ find_command = { "rg", "--files", "--hidden", "-g", "!.git" } })
      end
    end,
  })
elseif custom_opts.startup == "none" then
  -- disable startup message
  vim.o.shortmess = "I"
else
end

local function augroup(name)
  return vim.api.nvim_create_augroup("lazyvim_" .. name, { clear = true })
end

vim.api.nvim_create_autocmd("VimEnter", {
  group = augroup("autoupdate"),
  callback = function()
    if require("lazy.status").has_updates then
      --- @diagnostic disable-next-line: different-requires
      require("lazy").update({ show = false })
    end
  end,
})
