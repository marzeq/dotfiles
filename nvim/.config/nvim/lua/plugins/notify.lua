return {
  {
    "rcarriga/nvim-notify",
    event = "VeryLazy",
    opts = {
      background_colour = "#000000",
    },
    config = function(_, opts)
      require("notify").setup(opts)
      vim.notify = require("notify")
    end,
  },
}
