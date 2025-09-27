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
        { "<leader>s", ":%s/\\<<C-r><C-w>\\>//g<left><left>", desc = "Substitute word under cursor", mode = "n" },

        { "gy", '"+y', desc = "Yank to system clipboard", mode = { "n", "v", "x" } },
        { "gp", '"+p', desc = "Paste from system clipboard", mode = { "n", "v", "x" } },
      })
    end,
  },
}
