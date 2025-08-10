---@diagnostic disable: missing-fields
local wk_remaps = {
  { "<leader>g", "<cmd>Format<cr>", desc = "Format current file" },

  { "<leader>a", group = "codeactions" },
  { "<leader>ah", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]], desc = "Find and replace word" },
  { "<leader>ae", vim.diagnostic.open_float, desc = "Inspect error(s)" },
  {
    "<leader>ac",
    function()
      vim.diagnostic.jump({ count = 1, float = true })
    end,
    desc = "Cycle errors",
  },
  { "<leader>ar", vim.lsp.buf.rename, desc = "Rename symbol" },
  {
    "<leader>ad",
    function()
      require("trouble").toggle("diagnostics")
    end,
    desc = "Project diagnostics",
  },
  {
    "<leader>aD",
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
  { "<leader>aa", vim.lsp.buf.code_action, desc = "Code action" },

  { "<leader>f", group = "file" },
  {
    "<leader>ff",
    require("telescope.builtin").find_files,
    desc = "Find file",
  },
  { "<leader>fg", require("telescope.builtin").live_grep, desc = "Grep" },

  { "<leader>l", group = "lsp" },
  { "<leader>lm", "<cmd>Mason<cr>", desc = "Mason menu" },

  { "<leader>p", group = "plugins" },
  { "<leader>pm", "<cmd>Lazy<cr>", desc = "Lazy menu" },
  { "<leader>ps", "<cmd>Lazy sync<cr>", desc = "Lazy sync" },

  { "<leader>r", group = "command-runner" },
  { "<leader>rs", require("command-runner").set_commands, desc = "Set commands" },
  {
    "<leader>rr",
    require("command-runner").run_all_commands,
    desc = "Run all commands",
  },
  {
    "<leader>rc",
    require("command-runner").run_command_select_ui,
    desc = "Run command",
  },
  {
    "<leader>ra",
    require("command-runner").run_arbitrary_ui,
    desc = "Run arbitrary command",
  },

  { "<leader>t", group = "terminal" },
  {
    "<leader>tt",
    ":ToggleTerm direction=horizontal<cr>",
    desc = "Terminal",
  },

  { "<leader>w", group = "window" },
  { "<leader>wh", "<cmd>split<cr><C-w>j", desc = "Horizontal split" },
  { "<leader>wv", "<cmd>vsplit<cr><C-w>l", desc = "Vertical split" },

  { "<S-Tab>", "<cmd>BufferPrevious<cr>", desc = "Cycle buffers in reverse" },
  { "<Tab>", "<cmd>BufferNext<cr>", desc = "Cycle buffers" },

  { "<leader>p", '"_dP', desc = "Paste and keep buffer", mode = "x" },

  {
    "<C-Space>",
    function()
      vim.snippet.jump(1)
    end,
    desc = "Go to next field or completion",
    mode = { "i", "s", "n" },
  },
  {
    "<C-S-Space>",
    function()
      vim.snippet.jump(-1)
    end,
    desc = "Go to previous field or completion",
    mode = { "i", "s", "n" },
  },

  {
    "<c-h>",
    "<c-w>h",
    desc = "Move to the window to the left",
  },
  {
    "<c-j>",
    "<c-w>j",
    desc = "Move to the window below",
  },
  {
    "<c-k>",
    "<c-w>k",
    desc = "Move to the window above",
  },
  {
    "<c-l>",
    "<c-w>l",
    desc = "Move to the window to the right",
  },

  { "<leader>q", "<cmd>bd<CR>", desc = "Close current buffer", mode = "n" },

  { "gd", vim.lsp.buf.definition, desc = "Go to definition" },
  { "gD", vim.lsp.buf.declaration, desc = "Go to declaration" },
  { "gi", vim.lsp.buf.implementation, desc = "Go to implementation" },
  { "gr", vim.lsp.buf.references, desc = "Go to references" },
  { "K", vim.lsp.buf.hover, desc = "Hover documentation" },
  { "<leader>k", vim.lsp.buf.signature_help, desc = "Signature help" },

  { "<leader>db", require("dap").toggle_breakpoint, desc = "Toggle breakpoint" },
  { "<leader>dB", function() require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: ")) end, desc = "Set conditional breakpoint" },
  { "<leader>dc", require("dap").continue, desc = "Continue" },
  { "<leader>di", require("dap").step_into, desc = "Step into" },
  { "<leader>do", require("dap").step_over, desc = "Step over" },
  { "<leader>du", require("dap").step_out, desc = "Step out" },
  { "<leader>ds", function()
    -- open sidebar
    local widget = require("dap.ui.widgets")
    local sidebar = widget.sidebar(widget.scopes)
    sidebar.open()
  end, desc = "Open scopes sidebar" },
  { "<leader>dr", require("dap").repl.open, desc = "Open REPL" },
  { "<leader>dt", require("dap").terminate, desc = "Terminate debug session" },
}

local remap = function()
  local key = vim.keymap.set
  ---@diagnostic disable-next-line: unused-local
  local g = vim.g

  -- key leader to space -- configured in init.lua
  -- g.mapleader = " "
  -- g.maplocalleader = "\\"
  -- key("", "<Space>", "<Nop>")

  -- dont exit visual when indenting
  key("x", "=", "=gv")
  key("x", "<", "<gv")
  key("x", ">", ">gv")

  -- move lines in visual mode
  key("v", "J", ":m '>+1<CR>gv=gv")
  key("v", "K", ":m '<-2<CR>gv=gv")

  -- shift-j keeps cursor in place
  key("n", "J", "mzJ`z")

  -- escape in terminal mode goes back to normal mode
  key("t", "<Esc>", [[<C-\><C-n>]])

  key("n", "Q", "<nop>")
end

return { wk_remaps = wk_remaps, remap = remap }
