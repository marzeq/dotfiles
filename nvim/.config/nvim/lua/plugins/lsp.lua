return {
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
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
