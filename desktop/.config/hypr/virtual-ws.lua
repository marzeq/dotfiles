---@param a table
---@param b table
local function merge(a, b)
  local r = {}

  for k, v in pairs(a) do
    r[k] = v
  end

  for k, v in pairs(b) do
    r[k] = v
  end

  return r
end

---@param rules table<string, HL.WorkspaceRuleSpec>
local function M(rules)
  local monitors = hl.get_monitors()

  ---@param monitor integer
  ---@param vws integer
  local function get_hl_ws_id(monitor, vws)
    return (vws - 1) * #monitors + monitor + 1
  end

  ---@return HL.Monitor|nil
  local function get_active_monitor()
    local active = hl.get_active_monitor()
    if not active then
      return nil
    end
    return active
  end

  ---@param active HL.Monitor|nil
  local function restore_active(active)
    if not active then return end
    hl.dispatch(
      hl.dsp.focus { monitor = active.name }
    )
  end

  ---@param monitor HL.Monitor
  ---@param vws integer
  local function move_focus(monitor, vws)
    local hl_ws_id = get_hl_ws_id(monitor.id, vws)
    -- try and get rule for this monitor if it exists, otherwise default to {}
    local rule = rules[monitor.name] or {}
    hl.workspace_rule(merge(rule, {
      workspace = tostring(hl_ws_id),
      monitor = monitor.name,
    }))
    hl.dispatch(
      hl.dsp.focus { workspace = tostring(hl_ws_id) }
    )
  end

  ---@param vws integer
  local function goto_vws(vws)
    local active = get_active_monitor()

    for _, monitor in ipairs(monitors) do
      move_focus(monitor, vws)
    end

    restore_active(active)
  end

  ---@param vws integer
  ---@param opts table
  local function move_to_vws(vws, opts)
    local monitor = hl.get_active_monitor()
    if not monitor then
      return
    end
    local hl_ws_id = get_hl_ws_id(monitor.id, vws)
    hl.dispatch(
      hl.dsp.window.move(merge(opts, { workspace = tostring(hl_ws_id) }))
    )
  end

  -- pre-run workspace rules for 10 virtual workspaces
  for vws = 1, 10 do
    for _, monitor in ipairs(monitors) do
      local hl_ws_id = get_hl_ws_id(monitor.id, vws)
      local rule = rules[monitor.name] or {}
      hl.workspace_rule(merge(rule, {
        workspace = tostring(hl_ws_id),
        monitor = monitor.name,
      }))
    end
  end

  return {
    ---@param vws integer
    goto_vws = function(vws)
      return function()
        goto_vws(vws)
      end
    end,
    ---@param vws integer
    ---@param opts table
    move_to_vws = function(vws, opts)
      return function()
        move_to_vws(vws, opts)
      end
    end,
  }
end

return M
