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
        },
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
  config = function (_, opts)
    require("snacks").setup(opts)

    local function setqflist(items)
      local qf = {}
      for _, item in ipairs(items) do
        qf[#qf + 1] = {
          filename = Snacks.picker.util.path(item),
          bufnr = item.buf,
          lnum = item.pos and item.pos[1] or 1,
          col = item.pos and item.pos[2] + 1 or 1,
          end_lnum = item.end_pos and item.end_pos[1] or nil,
          end_col = item.end_pos and item.end_pos[2] + 1 or nil,
          text = item.line or item.comment or item.label or item.name or item.detail or item.text,
          pattern = item.search,
          valid = true,
        }
      end
      vim.fn.setqflist(qf)
    end

    Snacks.picker.actions.qflist = function (picker)
      picker:close()
      local sel = picker:selected()
      local items = #sel > 0 and sel or picker:items()
      setqflist(items)
    end

    Snacks.picker.actions.qflist_all = function (picker)
      picker:close()
      setqflist(picker:items())
    end
  end,
  keys = {
    { "<leader>ff", function () Snacks.picker.files() end, desc = "Find files" },
    { "<leader>fi", function () Snacks.picker.files({ ignored = true }) end, desc = "Find ignored files" },
    { "<leader>fg", function () Snacks.picker.grep() end, desc = "Grep" },

    { "<leader>qf", function () Snacks.picker.qflist() end, desc = "Quickfix list" },

    { "<leader>bd", function () Snacks.bufdelete() end, desc = "Buffer delete" },
  }
}
