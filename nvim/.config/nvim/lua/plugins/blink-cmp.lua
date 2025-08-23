return {
  {
    "saghen/blink.cmp",
    version = "1.*",
    ---@module "blink.cmp"
    ---@type blink.cmp.Config
    opts = {
      keymap = {
        preset = "default",
        ["<C-y>"] = false,
        ["<CR>"] = { "accept", "fallback" },
        ["<Tab>"] = false,
        ["<S-Tab>"] = false,
        ["<C-Space>"] = { "snippet_forward" },
        ["<C-S-Space>"] = { "snippet_backward" },
      },

      appearance = {
        nerd_font_variant = "normal"
      },


      sources = {
        default = { "lsp", "path", "buffer" },
      },

      fuzzy = { implementation = "prefer_rust_with_warning" },

      signature = {
        enabled = true,
        trigger = {
          enabled = true,
        }
      }
    },
    opts_extend = { "sources.default" }
  }
}
