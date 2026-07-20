---@diagnostic disable: missing-fields
return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    lazy = false,
    branch = "main",
    opts = {
      sync_install = false,
      auto_install = true,
    },
    init = function()
      vim.filetype.add({
        pattern = { [".*/hypr/.*%.conf"] = "hyprlang" },
      })

      vim.filetype.add({
        pattern = { [".*%.mconf"] = "mconf" },
      })

      vim.api.nvim_create_autocmd("User", { pattern = "TSUpdate",
      callback = function()
        require("nvim-treesitter.parsers").mconf = {
          install_info = {
            url = "https://github.com/marzeq/tree-sitter-mconf",
            revision = "f1422fe2c06c6e7f7b7ba3b48bb26364aef5fec7",
            queries = "queries/mconf",
          },
          tier = 2,
        }
      end})

      vim.api.nvim_create_autocmd("FileType", {
        pattern = "mconf",
        callback = function()
          vim.bo.commentstring = "# %s"
        end,
      })

      vim.api.nvim_create_autocmd("FileType", {
        callback = function(ev)
          local lang = vim.treesitter.language.get_lang(ev.match)
          local available_langs = require("nvim-treesitter").get_available()
          local is_available = vim.tbl_contains(available_langs, lang)
          if is_available then
            require("nvim-treesitter").install(lang):await(function ()
              vim.treesitter.start()
              vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
            end)
          end
        end,
      })
    end,
  },
  {
    "rluba/jai.vim"
  }
}
