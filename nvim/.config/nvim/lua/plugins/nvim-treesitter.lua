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
      vim.api.nvim_create_autocmd("FileType", {
        callback = function(ev)
          local lang = vim.treesitter.language.get_lang(ev.match)
          local available_langs = require("nvim-treesitter").get_available()
          local is_available = vim.tbl_contains(available_langs, lang)
          if is_available then
            local installed_langs = require("nvim-treesitter").get_installed()
            local installed = vim.tbl_contains(installed_langs, lang)
            if not installed then
              require("nvim-treesitter").install(lang):await(function ()
                vim.notify("Installed " .. lang .. " parser", vim.log.levels.INFO, { title = "nvim-treesitter" })
                vim.treesitter.start()
                require("nvim-treesitter").indentexpr()
              end)
            else
              vim.treesitter.start()
              require("nvim-treesitter").indentexpr()
            end
          end
        end,
      })
    end,
  },
}
