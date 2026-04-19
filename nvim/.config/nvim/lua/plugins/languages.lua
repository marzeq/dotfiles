---@diagnostic disable: inject-field

vim.filetype.add({
  pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
})

return {
  {
    "marzeq/tree-sitter-mconf",
    config = function()
      
    end,
  },
}
