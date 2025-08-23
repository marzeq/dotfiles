---@diagnostic disable: missing-fields
local wk_remaps = {
  { "<leader>f", group = "file" },
  {
    "<leader>ff",
    require("telescope.builtin").find_files,
    desc = "Find file",
  },
  { "<leader>fg", require("telescope.builtin").live_grep, desc = "Grep" },

  { "<S-Tab>", "<cmd>BufferPrevious<cr>", desc = "Cycle buffers in reverse" },
  { "<Tab>", "<cmd>BufferNext<cr>", desc = "Cycle buffers" },

  { "<leader>p", '"_dP', desc = "Paste and keep buffer", mode = "x" },

  { "gd", vim.lsp.buf.definition, desc = "Go to definition" },
  { "gD", vim.lsp.buf.declaration, desc = "Go to declaration" },
  { "ge", group = "Errors" },
  {
    "gen",
    function()
      vim.diagnostic.jump({ count = 1, float = true })
    end,
    desc = "Cycle errors",
  },
  {
    "gep",
    function()
      require("trouble").toggle("diagnostics")
    end,
    desc = "Project diagnostics",
  },
  {
    "gef",
    function()
      require("trouble").toggle({
        mode = "diagnostics",
        filter = {
          buf = 0,
        },
      })
    end,
    desc = "File diagnostics",
  },
  { "gr", group = "Actions" },
  { "grf", vim.lsp.buf.format, desc = "Format file" },
  { "gE", vim.diagnostic.open_float, desc = "Inspect errors" },
  { "K", vim.lsp.buf.hover, desc = "Hover documentation" },
  { "Q", vim.lsp.buf.signature_help, desc = "Signature help" },

  { "=", "=gv", desc = "Reindent line", mode = "x" },
  { "<", "<gv", desc = "Reindent line left", mode = "x" },
  { ">", ">gv", desc = "Reindent line right", mode = "x" },

  { "J", ":m '>+1<CR>gv=gv", desc = "Move line down", mode = "v" },
  { "K", ":m '<-2<CR>gv=gv", desc = "Move line up", mode = "v" },

  { "J", "mzJ`z", desc = "Join line below", mode = "n" },

  { "<Esc>", [[<C-\><C-n>]], desc = "Exit terminal mode", mode = "t" },
}


return { wk_remaps = wk_remaps }
