---@diagnostic disable: missing-fields
return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    lazy = false,
    branch = "master",
    config = function()
      require("nvim-treesitter.configs").setup({
        sync_install = false,
        auto_install = true,

        highlight = {
          enable = true,
        },
        indent = {
          enable = true,
        },
      })
    end,
  },
}
