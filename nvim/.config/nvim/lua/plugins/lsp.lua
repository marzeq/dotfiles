return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        "lua_ls",
        "gopls"
      }
    },
    config = function(_, opts)
      for _, server in ipairs(opts.servers) do
        vim.lsp.enable(server)
      end
    end,
  },

  {
    "folke/lazydev.nvim",
    ft = "lua",
    opts = {},
  },
}
