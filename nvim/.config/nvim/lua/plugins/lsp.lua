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
		dependencies = {
			{ "ms-jpq/coq_nvim", branch = "coq" },
		},
		init = function()
			vim.g.coq_settings = {
				auto_start = "shut-up",
				clients = {
					snippets = {
						warn = {},
					},
				},
			}
		end,
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
					local coq = require("coq")

					require("lspconfig")[server_name].setup(coq.lsp_ensure_capabilities({}))
				end,
				["lua_ls"] = function()
					local lspconfig = require("lspconfig")
					local coq = require("coq")

					lspconfig.lua_ls.setup(coq.lsp_ensure_capabilities({
						settings = {
							Lua = {
								diagnostics = {
									globals = { "vim" },
								},
							},
						},
					}))
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
