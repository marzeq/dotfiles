return {
  {
    "neovim/nvim-lspconfig",
    lazy = false,
    dependencies = {
      { "folke/lazydev.nvim", ft="lua", opts = {} },
    },
    ---@alias LspOpts (string[] | table<string, any>)
    ---@type LspOpts
    opts = {
      "lua_ls",
      "gopls",
      "pyright",
    },
    ---@param opts LspOpts
    config = function(_, opts)
      local to_enable = {}
      local options = {}
      for k, v in pairs(opts) do
        if type(k) == "string" then
          table.insert(to_enable, k)
          options[k] = v
        else
          table.insert(to_enable, v)
        end
      end

      vim.lsp.enable(to_enable)
      for server, config in pairs(options) do
        if config then
          vim.lsp.config(server, config)
        end
      end
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
