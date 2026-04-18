---@diagnostic disable: inject-field

vim.filetype.add({
  pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
})

return {
  {
    "marzeq/tree-sitter-mconf",
    config = function()
      require("nvim-treesitter.parsers").mconf = {
        install_info = {
          url = "https://github.com/marzeq/tree-sitter-mconf",
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
    end,
  },
}
