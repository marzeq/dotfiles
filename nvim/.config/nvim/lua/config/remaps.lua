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
	{ "<leader>ar", vim.lsp.buf.rename, desc = "Rename symbol" },
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
	{ "<leader>fb", "<cmd>Telescope file_browser path=%:p:help |select_buffer=true<cr>|", desc = "File browser" },
	{ "<leader>fw", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
	{ "<leader>fc", "<cmd>bd<cr>", desc = "Close current buffer" },

	{ "<leader>l", group = "lsp" },
	{ "<leader>lm", "<cmd>Mason<cr>", desc = "Mason menu" },
	{ "<leader>li", "<cmd>LspInfo<cr>", desc = "LSP info" },

	{ "<leader>p", group = "plugins" },
	{ "<leader>pm", "<cmd>Lazy<cr>", desc = "Lazy menu" },
	{ "<leader>ps", "<cmd>Lazy sync<cr>", desc = "Lazy sync" },

	{ "<leader>t", group = "terminal" },
	{
		"<leader>th",
		function()
			vim.api.nvim_exec(
				[[
          split
          wincmd j
          term
        ]],
				false
			)

			resizeToPercent("horizontal", 25)

			vim.api.nvim_feedkeys("a", "n", true)
		end,
		desc = "Horizontal terminal",
	},
	{
		"<leader>tv",
		function()
			vim.api.nvim_exec(
				[[
          vsplit
          wincmd l
          term
        ]],
				false
			)

			resizeToPercent("vertical", 25)

			vim.api.nvim_feedkeys("a", "n", true)
		end,
		desc = "Vertical terminal",
	},

	{ "<leader>w", group = "window" },
	{ "<leader>wh", "<cmd>split<cr><C-w>j", desc = "Horizontal split" },
	{ "<leader>wv", "<cmd>vsplit<cr><C-w>l", desc = "Vertical split" },
	{ "<leader>wr", group = "resize" },
	{ "<leader>wrh", group = "horizontal" },
	{
		"<leader>wrh=",
		function()
			resizeToPercent("horizontal", 50)
		end,
		desc = "Resize equal",
	},
	{
		"<leader>wrhb",
		function()
			resizeToPercent("horizontal", 75)
		end,
		desc = "Resize bigger (75%)",
	},
	{
		"<leader>wrhs",
		function()
			resizeToPercent("horizontal", 25)
		end,
		desc = "Resize smaller (25%)",
	},
	{
		"<leader>wrhc",
		function()
			vim.ui.input({ prompt = "Value for custom resize: " }, function(result)
				local n = tonumber(result)

				resizeToPercent("horizontal", n)
			end)
		end,
		desc = "Resize custom",
	},
	{ "<leader>wrv", group = "vertical" },
	{
		"<leader>wrv=",
		function()
			resizeToPercent("vertical", 50)
		end,
		desc = "Resize equal",
	},
	{
		"<leader>wrvb",
		function()
			resizeToPercent("vertical", 75)
		end,
		desc = "Resize bigger (75%)",
	},
	{
		"<leader>wrvs",
		function()
			resizeToPercent("vertical", 25)
		end,
		desc = "Resize smaller (25%)",
	},
	{
		"<leader>wrvc",
		function()
			vim.ui.input({ prompt = "Value for custom resize: " }, function(result)
				local n = tonumber(result)

				resizeToPercent("vertical", n)
			end)
		end,
		desc = "Resize custom",
	},

	{ "<S-Tab>", "<cmd>BufferPrevious<cr>", desc = "Cycle buffers in reverse" },
	{ "<Tab>", "<cmd>BufferNext<cr>", desc = "Cycle buffers" },

	{ "<leader>P", '"_dP', desc = "Paste and keep buffer", mode = "x" },

	{ "<c-k>", "<cmd>WhichKey<cr>", desc = "Which Keys", mode = { "n", "v", "x" } },

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
