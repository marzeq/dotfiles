return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "BurntSushi/ripgrep",
    },
    config = function()
      require("telescope").setup({
        extensions = {
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
        pickers = {
          live_grep = {
            additional_args = {
              "-i" -- case insensitive
            }
          }
        }
      })

      require("telescope").load_extension("ui-select")
    end,
  },

  {
    "nvim-telescope/telescope-ui-select.nvim",
  },
}
