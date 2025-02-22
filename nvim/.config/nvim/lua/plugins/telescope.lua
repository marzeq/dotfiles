-- CREDIT: https://github.com/3rd/image.nvim/issues/183#issuecomment-2284979815 @sand4rt
function telescope_image_preview()
  local supported_images = { "svg", "png", "jpg", "jpeg", "gif", "webp", "avif" }
  local from_entry = require("telescope.from_entry")
  local Path = require("plenary.path")
  local conf = require("telescope.config").values
  local Previewers = require("telescope.previewers")

  local previewers = require("telescope.previewers")
  local image_api = require("image")

  local is_image_preview = false
  local image = nil
  local last_file_path = ""

  local is_supported_image = function(filepath)
    local split_path = vim.split(filepath:lower(), ".", { plain = true })
    local extension = split_path[#split_path]
    return vim.tbl_contains(supported_images, extension)
  end

  local delete_image = function()
    if not image then
      return
    end

    image:clear()

    is_image_preview = false
  end

  local create_image = function(filepath, winid, bufnr)
    image = image_api.hijack_buffer(filepath, winid, bufnr)

    if not image then
      return
    end

    vim.schedule(function()
      image:render()
    end)

    is_image_preview = true
  end

  local function defaulter(f, default_opts)
    default_opts = default_opts or {}
    return {
      new = function(opts)
        if conf.preview == false and not opts.preview then
          return false
        end
        opts.preview = type(opts.preview) ~= "table" and {} or opts.preview
        if type(conf.preview) == "table" then
          for k, v in pairs(conf.preview) do
            opts.preview[k] = vim.F.if_nil(opts.preview[k], v)
          end
        end
        return f(opts)
      end,
      __call = function()
        local ok, err = pcall(f(default_opts))
        if not ok then
          error(debug.traceback(err))
        end
      end,
    }
  end

  -- NOTE: Add teardown to cat previewer to clear image when close Telescope
  local file_previewer = defaulter(function(opts)
    opts = opts or {}
    local cwd = opts.cwd or vim.loop.cwd()
    return Previewers.new_buffer_previewer({
      title = "File Preview",
      dyn_title = function(_, entry)
        return Path:new(from_entry.path(entry, true)):normalize(cwd)
      end,

      get_buffer_by_name = function(_, entry)
        return from_entry.path(entry, true)
      end,

      define_preview = function(self, entry, _)
        local p = from_entry.path(entry, true)
        if p == nil or p == "" then
          return
        end

        conf.buffer_previewer_maker(p, self.state.bufnr, {
          bufname = self.state.bufname,
          winid = self.state.winid,
          preview = opts.preview,
        })
      end,

      teardown = function(_)
        if is_image_preview then
          delete_image()
        end
      end,
    })
  end, {})

  local buffer_previewer_maker = function(filepath, bufnr, opts)
    -- NOTE: Clear image when preview other file
    if is_image_preview and last_file_path ~= filepath then
      delete_image()
    end

    last_file_path = filepath

    if is_supported_image(filepath) then
      create_image(filepath, opts.winid, bufnr)
    else
      previewers.buffer_previewer_maker(filepath, bufnr, opts)
    end
  end

  return { buffer_previewer_maker = buffer_previewer_maker, file_previewer = file_previewer.new }
end

return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "BurntSushi/ripgrep",
      {
        "3rd/image.nvim",
        dependencies = {
          {
            "vhyrro/luarocks.nvim",
            priority = 1000,
            config = true,
          },
        },
        opts = {},
      },
    },
    config = function()
      local fb_actions = require("telescope._extensions.file_browser.actions")
      local image_preview = telescope_image_preview()

      require("telescope").setup({
        extensions = {
          file_browser = {
            hijack_netrw = true,
            initial_mode = "normal",
            mappings = {
              n = {
                ["n"] = fb_actions.create,
                ["r"] = fb_actions.rename,
                ["m"] = fb_actions.move,
                ["c"] = fb_actions.copy,
                ["d"] = fb_actions.remove,
                ["x"] = fb_actions.open,
                ["g"] = fb_actions.goto_parent_dir,
                ["`"] = fb_actions.goto_home_dir,
                ["-"] = fb_actions.goto_cwd,
                ["t"] = fb_actions.change_cwd,
                ["f"] = fb_actions.toggle_browser,
                ["h"] = fb_actions.toggle_hidden,
                ["s"] = fb_actions.toggle_all,
              },
            },
          },
          ["ui-select"] = require("telescope.themes").get_dropdown({}),
        },
        defaults = {
          sorting_strategy = "ascending",
          layout_config = {
            horizontal = {
              prompt_position = "top",
              preview_width = 0.3,
            },
          },
          file_previewer = image_preview.file_previewer,
          buffer_previewer_maker = image_preview.buffer_previewer_maker,
        },
      })

      require("telescope").load_extension("file_browser")
      require("telescope").load_extension("ui-select")
    end,
  },

  {
    "nvim-telescope/telescope-ui-select.nvim",
  },

  {
    "nvim-telescope/telescope-file-browser.nvim",
  },
}
