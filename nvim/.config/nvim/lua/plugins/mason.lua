return {
  {
    "williamboman/mason.nvim",
    opts = {},
  },

  {
    "williamboman/mason-lspconfig.nvim",
    opts = {
      ensure_installed = { "lua_ls", "rust_analyzer", "gopls" },
      handlers = {
        function(server_name)
          local capabilities =
            vim.tbl_deep_extend("force", vim.lsp.protocol.make_client_capabilities(), require("epo").register_cap())

          require("lspconfig")[server_name].setup({ capabilities = capabilities })
        end,
        ["lua_ls"] = function()
          local lspconfig = require("lspconfig")
          local capabilities =
            vim.tbl_deep_extend("force", vim.lsp.protocol.make_client_capabilities(), require("epo").register_cap())

          lspconfig.lua_ls.setup({
            settings = {
              Lua = {
                diagnostics = {
                  globals = { "vim" },
                },
              },
            },
            capabilities = capabilities,
          })
        end,
      },
    },
  },
}
