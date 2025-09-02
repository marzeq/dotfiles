return {
  {
    "stevearc/oil.nvim",
    lazy = false,
    opts = {
      default_file_explorer = true,
    },
    keys = {
      { "-", "<cmd>Oil<cr>", desc = "Open parent directory", mode = "n" },
    },
  }
}
