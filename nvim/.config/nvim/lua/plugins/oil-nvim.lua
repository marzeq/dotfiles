return {
  {
    "stevearc/oil.nvim",
    dependencies = {
      "nvim-tree/nvim-web-devicons",
    },
    lazy = false,
    opts = {
      default_file_explorer = true,
    },
    keys = {
      { "-", function () require("oil").open() end, desc = "Open parent directory", mode = "n" },
    },
  }
}
