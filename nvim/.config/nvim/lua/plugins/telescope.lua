return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "BurntSushi/ripgrep",
    },
    opts = {
      extensions = {},
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
    },
    keys = {
      {
        "<leader>ff",
        require("telescope.builtin").find_files,
        desc = "Find file",
      },
      { "<leader>fg", require("telescope.builtin").live_grep, desc = "Grep" },
    }
  },
}
