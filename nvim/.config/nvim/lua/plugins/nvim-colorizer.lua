return {
  {
    "norcalli/nvim-colorizer.lua",
    init = function()
      vim.o.termguicolors = true

      require("colorizer").setup({
        css = { css = true, css_fn = true },
        scss = { css = true, css_fn = true },
        html = { names = false },
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
