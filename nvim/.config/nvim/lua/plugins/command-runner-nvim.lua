return {
  {
    "marzeq/command-runner.nvim",
    opts = {},
    keys = {
      { "<leader>rx", function () require("command-runner").set_commands() end, desc = "Open command setter window" },
      { "<leader>rr", function () require("command-runner").run_all_commands() end, desc = "Run all commands" },
      { "<leader>rs", function () require("command-runner").run_command_select_ui() end, desc = "Select and run command" },
    }
  }
}
