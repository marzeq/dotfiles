return {
  {
    "norcalli/nvim-colorizer.lua",
    event = { "BufReadPre", "BufNewFile" },
    init = function()
      vim.o.termguicolors = true

      require("colorizer").setup({
        css = { css = true, css_fn = true },
        hyprlang = { css = true, css_fn = true, names = false },
        scss = { css = true, css_fn = true },
        html = { names = false },
        astro = { names = false },
        javascriptreact = { names = false },
        json = { names = false },
        jsonc = { names = false },
        mconf = { names = false },
        conf = { names = false },
      }, {
        RRGGBBAA = true,
      })
    end,
  },
}
