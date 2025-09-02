local function key_for_command_numer(num)
  return { "<leader>r" .. num, function () require("command-runner").run_command(num) end, desc = "Run command #" .. num }
end

return {
  {
    "marzeq/command-runner.nvim",
    opts = {},
    keys = {
      { "<leader>rx", function () require("command-runner").set_commands() end, desc = "Open command setter window" },
      { "<leader>rr", function () require("command-runner").run_all_commands() end, desc = "Run all commands" },
      { "<leader>rs", function () require("command-runner").run_command_select_ui() end, desc = "Select and run command" },

      key_for_command_numer(1),
      key_for_command_numer(2),
      key_for_command_numer(3),
      key_for_command_numer(4),
      key_for_command_numer(5),
      key_for_command_numer(6),
      key_for_command_numer(7),
      key_for_command_numer(8),
      key_for_command_numer(9),
    }
  }
}
