return {
  {
    "catgoose/nvim-colorizer.lua",
    event = { "BufReadPre", "BufNewFile" },
    init = function()
      vim.o.termguicolors = true

      require("colorizer").setup({
        filetypes = {
          "*",

          css = {
            parsers = {
              css = true,
              css_fn = true,
              css_var = { enable = true, parsers = { css = true } },
            },
          },

          scss = {
            parsers = {
              css = true,
              css_fn = true,
              sass = { enable = true },
              css_var = { enable = true, parsers = { css = true } },
            },
          },
        },

        options = {
          parsers = {
            names = { enable = false },

            hex = {
              default = true,
              aarrggbb = true,
            },
          },
        },
      })
    end,
  },
}
