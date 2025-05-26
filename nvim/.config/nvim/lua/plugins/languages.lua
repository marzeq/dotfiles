---@diagnostic disable: inject-field
return {
  {
    "marzeq/tree-sitter-mconf",
    config = function()
      local parser_config = require("nvim-treesitter.parsers").get_parser_configs()

      parser_config.mconf = {
        install_info = {
          url = vim.fn.stdpath("data") .. "/lazy/tree-sitter-mconf",
          files = { "src/parser.c" },
        },
      }

      vim.filetype.add({
        pattern = { [".*%.mconf"] = "mconf" },
      })

      vim.api.nvim_create_autocmd("FileType", {
        pattern = "mconf",
        callback = function()
          vim.bo.commentstring = "# %s"
        end,
      })

      vim.filetype.add({
        pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
      })
    end,
  },
}
