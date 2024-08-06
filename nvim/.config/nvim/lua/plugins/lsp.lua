return {
  {
    "nvim-treesitter/nvim-treesitter", -- better highlighting
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

      local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
      parser_config.mconf = {
        install_info = {
          url = "https://github.com/marzeq/tree-sitter-mconf",
          files = { "src/parser.c" },
          branch = "dev",
        },
      }

      vim.filetype.add({
        -- *.mconf files
        pattern = { [".*%.mconf"] = "mconf" },
      })

      vim.filetype.add({
        pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
      })
    end,
  },

	-- lsp
	{
		"neovim/nvim-lspconfig",
		lazy = false,
		dependencies = {},
		init = function() end,
	},

  -- neovim types for lua
  {
    "folke/lazydev.nvim",
    ft = "lua",
    opts = {},
  },

	-- autocomplete
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
}
