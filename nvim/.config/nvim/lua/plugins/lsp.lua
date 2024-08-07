return {
  -- lsp
  {
    "neovim/nvim-lspconfig",
    lazy = false,
    dependencies = {},
    init = function() end,
  },

  -- neovim types for lua
  {
    "folke/lazydev.nvim",
    ft = "lua",
    opts = {},
  },
}
