return {
  {
    "neovim/nvim-lspconfig",
    dependencies = {
      { "folke/lazydev.nvim", ft = "lua", opts = {} },
    },
    config = function()
      vim.lsp.enable({
        "lua_ls",
        "gopls",
      })
    end,
  },
}
