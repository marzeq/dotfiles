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
    keys = {
      { "gd", vim.lsp.buf.definition, desc = "Go to definition" },
      { "gD", vim.lsp.buf.declaration, desc = "Go to declaration" },
      { "grf", vim.lsp.buf.format, desc = "Format file" },
      { "K", vim.lsp.buf.hover, desc = "Hover documentation" },
      { "Q", vim.lsp.buf.signature_help, desc = "Signature help" },
    }
  },
}
