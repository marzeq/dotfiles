local qk_plugin = {}

-- check if ~/code/qk exists
if vim.fn.isdirectory(vim.fn.expand("~/code/qk")) == 1 then
  qk_plugin = {
    dir = "~/code/qk",
    name = "qk",
    lazy = false,
    init = function(plugin)
      vim.opt.rtp:append(plugin.dir .. "/editor_support/vim")

      vim.filetype.add({
        extension = {
          qk = "qk",
          qks = "qk",
        },
      })
    end,
  }
end

return {
  qk_plugin,
}
