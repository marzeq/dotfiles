require("config.opts")

-- set leader before loading lazy
vim.g.mapleader = " "
vim.g.maplocalleader = " "
vim.keymap.set("", "<Space>", "<Nop>")

require("config.lazy")

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
