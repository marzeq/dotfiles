---@diagnostic disable: inject-field
return {
  {
    "marzeq/tree-sitter-mconf",
    config = function()
      local parser_config = require("nvim-treesitter.parsers").get_parser_configs()

      parser_config.mconf = {
        install_info = {
          url = "~/.local/share/nvim/lazy/tree-sitter-mconf",
          files = { "src/parser.c" },
        },
      }

      vim.filetype.add({
        pattern = { [".*%.mconf"] = "mconf" },
      })

      vim.api.nvim_create_autocmd("FileType", {
        pattern = "mconf",
        callback = function()
          vim.bo.commentstring = "# %s"
        end,
      })

      parser_config.c3 = {
        install_info = {
          url = "https://github.com/c3lang/tree-sitter-c3",
          files = { "src/parser.c", "src/scanner.c" },
          branch = "main",
        },
      }

      vim.filetype.add({
        extension = {
          c3 = "c3",
          c3i = "c3",
          c3t = "c3",
        },
      })

      local lspconfig = require("lspconfig")
      local util = require("lspconfig/util")
      local configs = require("lspconfig.configs")
      if not configs.c3_lsp then
        configs.c3_lsp = {
          default_config = {
            cmd = { "c3lsp" },
            filetypes = { "c3", "c3i" },
            root_dir = function(fname)
              local git_root = util.find_git_ancestor(fname)
              return git_root or util.path.dirname(fname)
            end,
            settings = {},
            name = "c3_lsp",
          },
        }
      end
      lspconfig.c3_lsp.setup({})
    end,
  },
}
