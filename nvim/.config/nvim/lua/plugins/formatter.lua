return {
  {
    "mhartington/formatter.nvim",
    opts = {
      formatOnSave = true,
    },
    config = function(_, opts)
      local filetype = {}
      local betterFiletypes = {
        [{ "typescript", "javascript", "typescriptreact", "javascriptreact", "json", "jsonc", "yaml", "html", "css" }] = require(
          "formatter.defaults.prettierd"
        ),
        rust = require("formatter.filetypes.rust").rustfmt,
        [{ "lua", "luau" }] = require("formatter.filetypes.lua").stylua,
        [{ "c", "cpp" }] = require("formatter.defaults.clangformat"),
        go = require("formatter.filetypes.go").gofumpt,
        pyton = require("formatter.filetypes.python").black,
      }

      for fts, format in pairs(betterFiletypes) do
        if type(fts) == "table" then
          for _, ft in ipairs(fts) do
            if type(ft) ~= "string" then
              error("One of the formatter indexes " .. fts .. " is not a string. Formatter will not work!")
            end

            filetype[ft] = format
          end
        elseif type(fts) == "string" then
          filetype[fts] = format
        else
          error("Formatter index " .. fts .. " is not a string or table of strings. Formatter will not work!")
        end
      end

      opts.filetype = filetype

      require("formatter").setup(opts)

      if opts.formatOnSave then
        -- enable format on save
        local augroup = vim.api.nvim_create_augroup
        local autocmd = vim.api.nvim_create_autocmd
        augroup("__formatter__", { clear = true })

        autocmd("BufWritePost", {
          group = "__formatter__",
          command = ":FormatWrite",
        })
      end
    end,
  },
}
