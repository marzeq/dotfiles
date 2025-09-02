return {
  {
    "saghen/blink.cmp",
    dependencies = {
      {
        "zbirenbaum/copilot.lua",
        opts = {
          suggestion = { enabled = false },
          panel = { enabled = false },
          filetypes = {
            markdown = true,
            help = true,
          },
        },
      },
      { "giuxtaposition/blink-cmp-copilot", },
    },
    version = "1.*",
    event = "InsertEnter",
    ---@module "blink.cmp"
    ---@type blink.cmp.Config
    opts = {
      keymap = {
        preset = "default",
        ["<C-y>"] = false,
        ["<CR>"] = { "accept", "fallback" },
        ["<Tab>"] = false,
        ["<S-Tab>"] = false,
        ["<C-l>"] = { "snippet_forward" },
        ["<C-h>"] = { "snippet_backward" },
      },

      appearance = {
        nerd_font_variant = "normal"
      },

      sources = {
        default = {
          "lsp",
          "path",
          "buffer",
          "copilot"
        },
        providers = {
          copilot = {
            name = "copilot",
            module = "blink-cmp-copilot",
            score_offset = 100,
            async = true,
          },
        },
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
  },
}
