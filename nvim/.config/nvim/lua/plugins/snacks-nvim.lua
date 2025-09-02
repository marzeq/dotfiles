---@diagnostic disable: undefined-field, undefined-global
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

local function my_dir_handler(dir)
  Snacks.picker.files({
    cwd = dir
  })
end

vim.api.nvim_create_autocmd("BufEnter", {
  group = vim.api.nvim_create_augroup("MyDirHandler", { clear = true }),
  callback = function(args)
    local stat = vim.loop.fs_stat(args.file)
    if stat and stat.type == "directory" then
      my_dir_handler(args.file)
      vim.cmd("bd!")
    end
  end,
})


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

    { "<leader>bd", function () Snacks.bufdelete() end, desc = "Buffer delete" },
  }
}
