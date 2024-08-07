return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim", "BurntSushi/ripgrep", "nvim-telescope/telescope-file-browser.nvim" },
    opts = {
      extensions = {
        file_browser = {
          hijack_netrw = true,
        },
        ["ui-select"] = require("telescope.themes").get_dropdown({}),
      },
      defaults = {
        sorting_strategy = "ascending",
        layout_config = {
          horizontal = {
            prompt_position = "top",
            preview_width = 0.3,
          },
        },
      },
    },
    config = function(_, opts)
      require("telescope").setup(opts)
      require("telescope").load_extension("file_browser")
      require("telescope").load_extension("ui-select")
    end,
  },

  {
    "nvim-telescope/telescope-ui-select.nvim",
  },
}
