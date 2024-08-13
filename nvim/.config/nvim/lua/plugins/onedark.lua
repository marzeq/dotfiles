return {
  {
    "navarasu/onedark.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      style = "cool",
      transparent = true,
    },
    config = function(_, opts)
      if vim.fn.empty(vim.env.TMUX) == 1 then
        if vim.fn.has("nvim") == 1 then
          vim.env.NVIM_TUI_ENABLE_TRUE_COLOR = 1
        end

        if vim.fn.has("termguicolors") == 1 then
          vim.o.termguicolors = true
        end
      end

      require("onedark").setup(opts)
      require("onedark").load()
    end,
  },
}
