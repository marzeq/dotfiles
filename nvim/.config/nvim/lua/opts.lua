local o = vim.opt
local g = vim.g

-- rounded window borders
o.winborder = "rounded"
-- start in empty buffer if no file is specified
o.shortmess = "I"

-- we have a nerd font
g.have_nerd_font = true

-- indent options
local indent_size = 2
o.tabstop = indent_size
o.softtabstop = indent_size
o.shiftwidth = indent_size
o.expandtab = true

-- relative line numbers
o.relativenumber = true

-- markdown force indent settings
vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.tabstop = indent_size
    vim.opt_local.softtabstop = indent_size
    vim.opt_local.shiftwidth = indent_size
    vim.opt_local.wrap = true
    vim.opt_local.linebreak = true
  end,
})
-- make comments work in json files
vim.api.nvim_create_autocmd("FileType", {
  pattern = "json",
  callback = function()
    vim.opt_local.filetype = "jsonc"
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = "rust",
  callback = function()
    vim.opt_local.expandtab = true
    vim.opt_local.shiftwidth = indent_size
    vim.opt_local.tabstop = indent_size
    vim.opt_local.softtabstop = indent_size
  end,
})

local function is_full_buffer_range(line1, line2)
  local total = vim.api.nvim_buf_line_count(0)
  return line1 == 1 and line2 == total
end

local function macro_backslash_and_align(opts)
  if opts.range == 0 then
    vim.notify("Provide an explicit range", vim.log.levels.ERROR)
    return
  end

  if is_full_buffer_range(opts.line1, opts.line2) then
    vim.notify("Whole-buffer (:%) not allowed", vim.log.levels.ERROR)
    return
  end

  local start_line = opts.line1
  local end_line   = opts.line2
  local lines = vim.api.nvim_buf_get_lines(0, start_line - 1, end_line, false)

  local stripped = {}
  local max_len = 0

  -- compute max width ignoring trailing "\" + whitespace
  for i, line in ipairs(lines) do
    local base = line:gsub("%s*\\%s*$", "")
    stripped[i] = base
    local len = vim.fn.strdisplaywidth(base)
    if len > max_len then
      max_len = len
    end
  end

  -- add and align "\" on every line except the last
  for i = 1, #lines do
    local base = stripped[i]

    if i ~= #lines then
      local pad = max_len - vim.fn.strdisplaywidth(base)
      lines[i] = base .. string.rep(" ", pad) .. " \\"
    else
      lines[i] = base
    end
  end

  vim.api.nvim_buf_set_lines(0, start_line - 1, end_line, false, lines)
end

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "c", "cpp" },
  callback = function(args)
    vim.api.nvim_buf_create_user_command(
      args.buf,
      "MacroAlign",
      macro_backslash_and_align,
      { range = true }
    )
  end,
})

-- line numbers
o.number = true

-- disable line wrapping
o.wrap = false

-- disable highlighting after search
o.hlsearch = false
-- highlight while typing search
o.incsearch = true

-- number of lines to keep above and below cursor
o.scrolloff = 8

-- no swap files
o.swapfile = false

-- enable mouse support
o.mouse = "a"

-- persistent undo
o.undofile = true

-- window title shows file name
o.title = true

-- ignore case in search patterns
o.ignorecase = true
o.smartcase = true

-- honestly i don't remember what this does
o.foldmethod = "expr"
o.foldexpr = "v:lua.vim.treesitter.foldexpr()"
o.foldtext = "v:lua.vim.treesitter.foldtext()"
vim.api.nvim_command(
  "autocmd BufEnter * if !exists('b:entered_once') | let b:entered_once = 1 | set nofoldenable | endif"
)
