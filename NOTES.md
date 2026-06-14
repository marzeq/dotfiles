# Philosophy

Although I have adapted this configuration to be easy to use by others, it is still primairly aimed towards my use case,
so it is highly opinionated and not extensively customisable.

# Desktop docs

## Hyprland customisation

### Overwriting settings

To modify the values the main config depends on, edit the `opts.lua` file.

The spec is:

```lua
return {
  -- overwrites for programs launched by keybindings
  programs = {
    terminal = "alacritty",
    fileManager = "thunar",
    menu = "rofi -show drun",
    browser = "helium-browser",
    editor = "nano"
  },
  mod = "SUPER", -- mod key
  mod2 = "ALT", -- alt mod key, used for some keybindings
  monitoropts = {
    ["DP-1"] = {
      -- workspace rules but for each monitor
      -- same as workspace rules, but the monitor and workspace key will be overwritten
      -- by the config, so you only need to specify things like layout_opts etc.
    }
  },
  virtualworkspaces = false, -- whether to use virtual workspaces or not, if false, workspaces will be per monitor. note - if set to true, monitoropts has no effect
}
```

If things are not provided, a default value will be used, so you only need to specify the values you want to change.

### Custom config additions

Edit the `hyprland-custom.lua` file to overwrite/add any custom hyprland settings you want, that way updating won't cause merge issues.

## Keybindings

Default keybindings for the desktop are as follows:

### Window management

| Keys                                                 | Action                                      |
|------------------------------------------------------|---------------------------------------------|
| `mod` + `q`                                          | Kill active window                          |
| `mod` + `t`                                          | Toggle floating                             |
| `mod` + `s`                                          | Swap slave with master/Toggle dwindle split |
| `mod` + `shift` + `f`                                | Fullscreen                                  |
| `mod` + `h` / `j` / `k` / `l`                        | Move focus                                  |
| `mod` + `left` / `down` / `up` / `right`             | Move focus                                  |
| `mod` + `shift` + `h` / `j` / `k` / `l`              | Move window                                 |
| `mod` + `shift` + `left` / `down` / `up` / `right`   | Move window                                 |

### Shell

| Keys              | Action                   |
|-------------------|--------------------------|
| `mod` + `space`   | Open launcher            |
| `mod` + `n`       | Toggle notification view |

### Applications

| Keys               | Action            |
|--------------------|-------------------|
| `mod` + `return`   | Open terminal     |
| `mod` + `b`        | Open browser      |
| `mod` + `f`        | Open file manager |

### Workspaces/monitor

| Keys                        | Action                        |
|-----------------------------|-------------------------------|
| `mod` + `1`–`0`             | Switch to workspace 1–10      |
| `mod` + `shift` + `1`–`0`   | Move window to workspace 1–10 |
| `mod2` + `1`–`0`            | Switch to monitor 1–10        |

#### What are virtual workspaces and how do they differ from regular workspaces

Virtual workspaces are our own concept. Each virtual workspace spans
across all monitors instead of being tied to a specific monitor -
similar to GNOME's, KDE's and Windows' workspaces/virtual desktops.

### Screenshots / OCR / Colour picker

| Keys                    | Action             |
|-------------------------|--------------------|
| `mod` + `shift` + `s`   | Area screenshot    |
| `mod` + `shift` + `w`   | Window screenshot  |
| `mod` + `shift` + `m`   | Monitor screenshot |
| `mod` + `shift` + `t`   | OCR script         |
| `mod` + `shift` + `c`   | Colour picker      |

## Unbinding

Use `hyprland-custom.conf` and Hyprland's `unbind` funcionality.

See Hyprland docs on how to unbind keys.
