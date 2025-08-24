return {
  {
    "folke/trouble.nvim",
    opts = {
      warn_no_results = false,
    },
    cmd = "Trouble",
    keys = {
      {
        "gen",
        function()
          vim.diagnostic.jump({ count = 1, float = true })
        end,
        desc = "Cycle errors",
      },
      {
        "gep",
        function()
          require("trouble").toggle("diagnostics")
        end,
        desc = "Project diagnostics",
      },
      {
        "gef",
        function()
          ---@diagnostic disable-next-line: missing-fields
          require("trouble").toggle({
            mode = "diagnostics",
            filter = {
              buf = 0,
            },
          })
        end,
        desc = "File diagnostics",
      },
      { "gE", vim.diagnostic.open_float, desc = "Inspect errors" },
    }
  },
}
