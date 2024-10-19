return {
  {
    "marzeq/tree-sitter-mconf",
    config = function()
      local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
      parser_config.mconf = {
        install_info = {
          url = "~/.local/share/nvim/lazy/tree-sitter-mconf", -- adjust according to your plugin manager install path
          files = { "src/parser.c" },
        },
      }

      vim.filetype.add({
        pattern = { [".*%.mconf"] = "mconf" },
      })
    end,
  },
}
