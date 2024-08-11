return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim", "BurntSushi/ripgrep" },
    config = function()
      local fb_actions = require("telescope._extensions.file_browser.actions")

      require("telescope").setup({
        extensions = {
          file_browser = {
            hijack_netrw = true,
            initial_mode = "normal",
            mappings = {
              n = {
                ["n"] = fb_actions.create,
                ["r"] = fb_actions.rename,
                ["m"] = fb_actions.move,
                ["c"] = fb_actions.copy,
                ["d"] = fb_actions.remove,
                ["x"] = fb_actions.open,
                ["g"] = fb_actions.goto_parent_dir,
                ["`"] = fb_actions.goto_home_dir,
                ["-"] = fb_actions.goto_cwd,
                ["t"] = fb_actions.change_cwd,
                ["f"] = fb_actions.toggle_browser,
                ["h"] = fb_actions.toggle_hidden,
                ["s"] = fb_actions.toggle_all,
              },
            },
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
      })

      require("telescope").load_extension("file_browser")
      require("telescope").load_extension("ui-select")
    end,
  },

  {
    "nvim-telescope/telescope-ui-select.nvim",
  },

  {
    "nvim-telescope/telescope-file-browser.nvim",
  },
}
