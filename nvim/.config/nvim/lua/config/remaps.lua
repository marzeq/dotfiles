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

local function makeResizeRemap(type)
	return {
		name = type,

		s = {
			function()
				resizeToPercent(type, 25)
			end,
			"Resize smaller (25%)",
		},
		b = {
			function()
				resizeToPercent(type, 75)
			end,
			"Resize bigger (75%)",
		},
		["="] = {
			function()
				resizeToPercent(type, 50)
			end,
			"Resize equal",
		},
		c = {
			function()
				vim.ui.input({ prompt = "Value for custom resize: " }, function(result)
					local n = tonumber(result)

					resizeToPercent(type, n)
				end)
			end,
			"Resize custom",
		},
	}
end

local wk_remaps = {
	{
		mappings = {
			f = {
				name = "file",

				f = {
					"<cmd>lua require'telescope.builtin'.find_files({ find_command = {'rg', '--files', '--hidden', '-g', '!.git' }})<cr>",
					"Find file",
				},
				g = { "<cmd>Telescope live_grep<cr>", "Grep" },
				b = { "<cmd>Telescope file_browser path=%:p:h select_buffer=true<cr>", "File browser" },
				w = { "<cmd>Telescope buffers<cr>", "Buffers" },
			},
			l = {
				name = "lsp",

				m = { "<cmd>Mason<cr>", "Mason menu" },
				i = { "<cmd>LspInfo<cr>", "LSP info" },
			},
			p = {
				name = "plugins",

				m = { "<cmd>Lazy<cr>", "Lazy menu" },
				s = { "<cmd>Lazy sync<cr>", "Lazy sync" },
			},
			w = {
				name = "window",

				v = { "<cmd>vsplit<cr><C-w>l", "Vertical split" },
				h = { "<cmd>split<cr><C-w>j", "Horizontal split" },
				r = {
					name = "resize",

					v = makeResizeRemap("vertical"),
					h = makeResizeRemap("horizontal"),
				},
			},
			a = {
				name = "codeactions",

				h = { [[:%s/\<<C-r><C-w>\>/<C-r><C-w>/gI<Left><Left><Left>]], "Find and replace word" },
				e = { vim.diagnostic.open_float, "Inspect error(s)" },
				c = { vim.diagnostic.goto_next, "Cycle errors" },
				r = { vim.lsp.buf.rename, "Rename symbol" },
				-- a = { require("actions-preview").codeactions, "Code actions" }, -- configured in plugins/actions.lua
			},
			t = {
				name = "terminal",

				v = {
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
					"Vertical terminal",
				},
				h = {
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
					"Vertical terminal",
				},
			},
			g = { "<cmd>Format<cr>", "Format current file" },
		},
		options = { prefix = "<leader>", mode = "n" },
	},

	{
		mappings = {
			P = { '"_dP', "Paste and keep buffer" },
		},
		options = { prefix = "<leader>", mode = "x" },
	},

	{
		mappings = {
			["<c-k>"] = { "<cmd>WhichKey<cr>", "Which Keys" },
		},
		options = {
			mode = { "n", "x", "v" },
		},
	},

	{ mappings = { d = { vim.lsp.buf.definition, "Go to definition" } }, options = { prefix = "g", mode = "n" } },
}

local remap = function()
	local key = vim.keymap.set
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
