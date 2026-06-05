return {
  {
    "Mofiqul/adwaita.nvim",
    commit = "93f3bed009f7fc4c57f8d710880b6cab9e0b0d15",
    priority = 1000,
    config = function()
      vim.g.adwaita_transparent = true
      vim.cmd("colorscheme adwaita")
    end,
  },
}
