return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    lazy = false,
    config = function()
      local configs = require("nvim-treesitter.configs")

      configs.setup({
        ensure_installed = { "c", "lua", "vim", "rust", "vimdoc", "typescript", "javascript", "html" },
        sync_install = false,
        auto_install = true,

        highlight = {
          enable = true,
        },
        indent = {
          enable = true,
        },
      })

      local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
      parser_config.mconf = {
        install_info = {
          url = "https://github.com/marzeq/tree-sitter-mconf",
          files = { "src/parser.c" },
          branch = "dev",
        },
      }

      vim.filetype.add({
        -- *.mconf files
        pattern = { [".*%.mconf"] = "mconf" },
      })

      vim.filetype.add({
        pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
      })
    end,
  },
}
