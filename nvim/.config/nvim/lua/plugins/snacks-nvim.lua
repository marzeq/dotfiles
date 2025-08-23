return {
  "folke/snacks.nvim",
  priority = 1000,
  lazy = false,
  opts = {
    bigfile = {
      enabled = true,
      max_size = 2 * 1024 * 1024, -- 2MB
    },
    input = {
      win = {
        relative = "cursor",
        row = 1,
        col = 0,
      }
    }
  }
}
