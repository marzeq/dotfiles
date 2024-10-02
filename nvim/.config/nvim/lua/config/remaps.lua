local function resizeToPercent(type, n)
  if n < 0 or n > 100 or n == nil then
    error(n .. " is not a valid percentage")
  end

  if type ~= "vertical" and type ~= "horizontal" then
    error("type must be either `vertical` or `horizontal`")
  end

  local total_width = type == "vertical" and vim.o.columns or vim.o.lines

  local new_width = math.floor(total_width * n / 100)

  local prefix = type == "vertical" and "vertical " or ""

  vim.cmd(prefix .. "resize " .. new_width)
end

local wk_remaps = {
  { "<leader>g", "<cmd>Format<cr>", desc = "Format current file" },

  { "<leader>a", group = "codeactions" },
  { "<leader>ah", [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]], desc = "Find and replace word" },
  { "<leader>ae", vim.diagnostic.open_float, desc = "Inspect error(s)" },
  { "<leader>ac", vim.diagnostic.goto_next, desc = "Cycle errors" },
  {
    "<leader>ar",
    function()
      require("live-rename").rename({ insert = true })
    end,
    desc = "Rename symbol",
  },
  { "<leader>ad", "<cmd>Trouble diagnostics toggle<cr>", desc = "Project diagnostics" },
  { "<leader>aD", "<cmd>Trouble diagnostics toggle filter.buf=0<cr>", desc = "File diagnostics" },
  { "<leader>aa", vim.lsp.buf.code_action, desc = "Code action" },

  { "<leader>f", group = "file" },
  {
    "<leader>ff",
    "<cmd>lua require'telescope.builtin'.find_files({ find_command = {'rg', '--files', '--hidden', '-g', '!.git' }})<cr>",
    desc = "Find file",
  },
  { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Grep" },
  { "<leader>fb", "<cmd>Telescope file_browser path=%:p:help |select_buffer=true<cr>", desc = "File browser" },
  { "<leader>fw", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
  { "<leader>fc", "<cmd>bd<cr>", desc = "Close current buffer" },

  { "<leader>l", group = "lsp" },
  { "<leader>lm", "<cmd>Mason<cr>", desc = "Mason menu" },
  { "<leader>li", "<cmd>LspInfo<cr>", desc = "LSP info" },

  { "<leader>p", group = "plugins" },
  { "<leader>pm", "<cmd>Lazy<cr>", desc = "Lazy menu" },
  { "<leader>ps", "<cmd>Lazy sync<cr>", desc = "Lazy sync" },

  { "<leader>r", group = "command-runner" },
  { "<leader>rs", require("command-runner").set_commands, desc = "Set commands" },
  {
    "<leader>rr",
    function()
      require("command-runner").run_command(nil)
    end,
    desc = "Run all commands",
  },
  {
    "<leader>rc",
    function()
      local commands = require("command-runner").get_commands()

      if #commands == 0 then
        vim.notify("No commands set", vim.log.levels.ERROR)
        return
      end

      local indexes = {}

      for i, _ in ipairs(commands) do
        table.insert(indexes, tostring(i))
      end

      vim.ui.select(indexes, {
        prompt = "Select command to run: ",
        format_item = function(item)
          return item .. ": " .. commands[tonumber(item)]
        end,
      }, function(choice)
        if choice == nil then
          return
        end
        require("command-runner").run_command(tonumber(choice))
      end)
    end,
    desc = "Run command",
  },

  {
    "<leader>c",
    require("visual-commit").commit,
    desc = "Open git commit menu",
  },

  {
    mode = { "v" },
    { "<leader>s", group = "Screenshot" },
    {
      "<leader>sc",
      function()
        require("nvim-silicon").clip()
      end,
      desc = "Copy code screenshot to clipboard",
    },
    {
      "<leader>sf",
      function()
        require("nvim-silicon").file()
      end,
      desc = "Save code screenshot as file",
    },
    {
      "<leader>ss",
      function()
        require("nvim-silicon").shoot()
      end,
      desc = "Create code screenshot",
    },
  },

  { "<leader>t", group = "terminal" },
  {
    "<leader>th",
    ":ToggleTerm direction=horizontal<cr>",
    desc = "Horizontal terminal",
  },
  {
    "<leader>tv",
    ":ToggleTerm direction=vertical<cr>",
    desc = "Vertical terminal",
  },
  {
    "<leader>tt",
    ":ToggleTerm direction=float<cr>",
    desc = "Toggle terminal",
  },

  { "<leader>w", group = "window" },
  { "<leader>wh", "<cmd>split<cr><C-w>j", desc = "Horizontal split" },
  { "<leader>wv", "<cmd>vsplit<cr><C-w>l", desc = "Vertical split" },
  { "<leader>wr", group = "resize" },
  {
    "<leader>wrh",
    function()
      vim.ui.input({ prompt = "Value for horizontal resize: " }, function(result)
        local n = tonumber(result)

        resizeToPercent("horizontal", n)
      end)
    end,
    desc = "Resize horizontal",
  },
  {
    "<leader>wrv",
    function()
      vim.ui.input({ prompt = "Value for vertical resize: " }, function(result)
        local n = tonumber(result)

        resizeToPercent("vertical", n)
      end)
    end,
    desc = "Resize vertical",
  },

  { "<S-Tab>", "<cmd>BufferPrevious<cr>", desc = "Cycle buffers in reverse" },
  { "<Tab>", "<cmd>BufferNext<cr>", desc = "Cycle buffers" },

  { "<leader>p", '"_dP', desc = "Paste and keep buffer", mode = "x" },

  { "<c-k>", "<cmd>WhichKey<cr>", desc = "Which Keys", mode = { "n", "v", "x", "s" } },

  {
    "<C-Space>",
    "<cmd>lua vim.snippet.jump(1)<cr>",
    desc = "Go to next field or completion",
    mode = { "i", "s", "n" },
  },
  {
    "<C-S-Space>",
    "<cmd>lua vim.snippet.jump(-1)<cr>",
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

  {
    "<c-s>",
    "<cmd>w<cr>",
    desc = "Save file",
    mode = { "n", "v", "x", "s", "i" },
  },
  {
    "<C-S-s>",
    "<cmd>noa w<cr>",
    desc = "Save file without formatting",
    mode = { "n", "v", "x", "s", "i" },
  },

  { "<Esc>", "<cmd>nohlsearch<CR>", desc = "Clear highlights", mode = "n" },

  { "gd", vim.lsp.buf.definition, desc = "Go to definition" },
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

  -- START credit: ThePrimeagen

  -- move lines in visual mode
  key("v", "J", ":m '>+1<CR>gv=gv")
  key("v", "K", ":m '<-2<CR>gv=gv")

  -- shift-j keeps cursor in place
  key("n", "J", "mzJ`z")

  -- escape in terminal mode goes back to normal mode
  key("t", "<Esc>", [[<C-\><C-n>]])

  key("n", "Q", "<nop>")

  -- END credit: ThePrimeagen
end

return { wk_remaps = wk_remaps, remap = remap }
