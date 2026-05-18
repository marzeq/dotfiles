return {
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    init = function() end,
    opts = {},
    config = function()
      vim.o.timeout = true
      vim.o.timeoutlen = 300

      local wk = require("which-key")
      wk.add({
        { "<S-Tab>", "<cmd>BufferPrevious<cr>", desc = "Cycle buffers in reverse" },
        { "<Tab>", "<cmd>BufferNext<cr>", desc = "Cycle buffers" },

        { "<leader>p", '"_dP', desc = "Paste and keep buffer", mode = { "v", "x" } },

        { "=", "=gv", desc = "Reindent line", mode = "x" },
        { "<", "<gv", desc = "Reindent line left", mode = "x" },
        { ">", ">gv", desc = "Reindent line right", mode = "x" },

        { "J", ":m '>+1<CR>gv=gv", desc = "Move line down", mode = "v" },
        { "K", ":m '<-2<CR>gv=gv", desc = "Move line up", mode = "v" },

        { "J", "mzJ`z", desc = "Join line below", mode = "n" },

        { "<Esc>", [[<C-\><C-n>]], desc = "Exit terminal mode", mode = "t" },
        {
          "<leader>s",
          function()
            local word = vim.fn.expand("<cword>")

            vim.ui.input({
              prompt = "Rename: ",
              default = word,
            }, function(input)
              if not input or input == "" or input == word then
                return
              end

              local pattern = ([[\V\<%s\>]]):format(vim.fn.escape(word, [[\]]))
              local replacement = vim.fn.escape(input, [[\/]])

              vim.cmd(("%%s/%s/%s/g"):format(pattern, replacement))
            end)
          end,
          desc = "Substitute word under cursor",
          mode = "n",
        },

        { "gy", '"+y', desc = "Yank to system clipboard", mode = { "n", "v", "x" } },
        { "gp", '"+p', desc = "Paste from system clipboard", mode = { "n", "v", "x" } },
        { "gX", '"+d', desc = "Cut to system clipboard", mode = { "n", "v", "x" } } ,
      })
    end,
  },
}
