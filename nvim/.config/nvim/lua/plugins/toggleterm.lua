return {
  "akinsho/nvim-toggleterm.lua",
  config = function()
    local toggleterm = require("toggleterm")

    toggleterm.setup({
      hide_number = true,
      start_in_insert = true,
    })
  end,
}
