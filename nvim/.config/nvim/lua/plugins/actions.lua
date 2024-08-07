return {
  -- view errors in project
  {
    "folke/trouble.nvim",
    opts = {
      warn_no_results = false,
    },
    cmd = "Trouble",
  },

  -- better comments
  {
    "numToStr/Comment.nvim",
    opts = {
      mappings = {
        basic = true,
        extra = true,
      },
    },
  },
}
