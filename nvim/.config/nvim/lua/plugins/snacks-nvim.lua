---@diagnostic disable: undefined-global

return {
  "folke/snacks.nvim",
  priority = 1000,
  lazy = false,
  opts = {
    bigfile = {
      enabled = true,
      max_size = 2 * 1024 * 1024, -- 2MB
    },
    input = {
      win = {
        relative = "cursor",
        row = 1,
        col = 0,
      }
    },
    picker = {
      prompt = " > ",
      icons = {
        files = {
          file = ""
        },
        ui = {
          selected = "+ ",
          unselected = " ",
        }
      },
    },
    image = {},
    notifier = {},
    indent = {
      indent = {
        char = "▎",
        hl = "Whitespace",
      },
      scope = { enabled = false },
    },
  },
  keys = {
    { "<leader>ff", function () Snacks.picker.files() end, desc = "Find files" },
    { "<leader>fi", function () Snacks.picker.files({ ignored = true }) end, desc = "Find ignored files" },
    { "<leader>fg", function () Snacks.picker.grep() end, desc = "Grep" },

    { "<leader>qf", function () Snacks.picker.qflist() end, desc = "Quickfix list" },

    { "<leader>bd", function () Snacks.bufdelete() end, desc = "Buffer delete" },
  }
}
