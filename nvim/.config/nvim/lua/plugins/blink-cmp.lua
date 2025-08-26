return {
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
  {
    "saghen/blink.cmp",
    dependencies = {
      {
        "giuxtaposition/blink-cmp-copilot",
      },
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
        ["<C-Space>"] = { "snippet_forward" },
        ["<C-S-Space>"] = { "snippet_backward" },
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
