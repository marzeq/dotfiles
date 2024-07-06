return {
	{
		"nvim-treesitter/nvim-treesitter",
		build = ":TSUpdate",
		config = function()
			local configs = require("nvim-treesitter.configs")

			configs.setup({
				ensure_installed = { "c", "lua", "vim", "rust", "vimdoc", "typescript", "javascript", "html" },
				sync_install = false,
				auto_install = true,

				highlight = {
					enable = true,
				},
				indent = {
					enable = true,
				},
			})
		end,
	},

	{
		"neovim/nvim-lspconfig",
		lazy = false,
		dependencies = {},
		init = function() end,
	},

	{
		"nvimdev/epo.nvim",
		dependencies = { { "onsails/lspkind.nvim", lazy = false } },
		opts = {
			kind_format = function(k)
				local icons = {
					Text = "󰉿",
					Method = "󰆧",
					Function = "󰊕",
					Constructor = "",
					Field = "󰜢",
					Variable = "󰀫",
					Class = "󰠱",
					Interface = "",
					Module = "",
					Property = "󰜢",
					Unit = "󰑭",
					Value = "󰎠",
					Enum = "",
					Keyword = "󰌋",
					Snippet = "",
					Color = "󰏘",
					File = "󰈙",
					Reference = "󰈇",
					Folder = "󰉋",
					EnumMember = "",
					Constant = "󰏿",
					Struct = "󰙅",
					Event = "",
					Operator = "󰆕",
					TypeParameter = "",
				}

				return icons[k]
			end,
		},
	},

	{
		"williamboman/mason.nvim",
		opts = {},
	},

	{
		"williamboman/mason-lspconfig.nvim",
		opts = {
			ensure_installed = { "lua_ls", "rust_analyzer", "tsserver" },
			handlers = {
				function(server_name)
					local capabilities = vim.tbl_deep_extend(
						"force",
						vim.lsp.protocol.make_client_capabilities(),
						require("epo").register_cap()
					)

					require("lspconfig")[server_name].setup({ capabilities = capabilities })
				end,
				["lua_ls"] = function()
					local lspconfig = require("lspconfig")
					local capabilities = vim.tbl_deep_extend(
						"force",
						vim.lsp.protocol.make_client_capabilities(),
						require("epo").register_cap()
					)

					lspconfig.lua_ls.setup({
						settings = {
							Lua = {
								diagnostics = {
									globals = { "vim" },
								},
							},
						},
						capabilities = capabilities,
					})
				end,
			},
		},
	},

	{
		"numToStr/Comment.nvim",
		opts = {
			mappings = {
				basic = true,
				extra = true,
			},
		},
	},
}
