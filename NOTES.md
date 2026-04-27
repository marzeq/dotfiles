# Philosophy

Although I have adapted this configuration to be easy to use by others, it is still primairly aimed towards my use case,
so it is highly opinionated and not extensively customisable.

# Desktop docs

## Hyprland customisation

Edit the `hyprland-custom.conf` file to overwrite/add any custom hyprland settings you want, that way updating won't cause merge issues.

To overwrite the programs that binds like `super` + `return` (terminal), `super` + `b` (browser) etc. depend on,
you should look to the `programs-custom.conf` file instead. There, you can change the variables to your desired programs like this:

```hyprlang
$terminal = alacritty # instead of ghostty
$fileManager = thunar # instead of nautilus
$menu = rofi -show drun # instead of our custom launcher
$browser = google-chrome-stable # instead of firefox
env = EDITOR,nano # instead of neovim
```

## Keybindings

Default keybindings for the desktop are as follows:

### Window management

| Keys                                                 | Action                                      |
|------------------------------------------------------|---------------------------------------------|
| `super` + `q`                                        | Kill active window                          |
| `super` + `t`                                        | Toggle floating                             |
| `super` + `s`                                        | Swap slave with master/Toggle dwindle split |
| `super` + `shift` + `f`                              | Fullscreen                                  |
| `super` + `h` / `j` / `k` / `l`                      | Move focus                                  |
| `super` + `left` / `down` / `up` / `right`           | Move focus                                  |
| `super` + `shift` + `h` / `j` / `k` / `l`            | Move window                                 |
| `super` + `shift` + `left` / `down` / `up` / `right` | Move window                                 |

### Shell

| Keys              | Action          |
|-------------------|-----------------|
| `super` + `space` | Open launcher   |

### Applications

| Keys               | Action            |
|--------------------|-------------------|
| `super` + `return` | Open terminal     |
| `super` + `b`      | Open browser      |
| `super` + `f`      | Open file manager |

### Workspaces

| Keys                        | Action                        |
|-----------------------------|-------------------------------|
| `super` + `1`–`0`           | Switch to workspace 1–10      |
| `super` + `shift` + `1`–`0` | Move window to workspace 1–10 |

### Screenshots / OCR / Colour picker

| Keys                    | Action             |
|-------------------------|--------------------|
| `super` + `shift` + `s` | Area screenshot    |
| `super` + `shift` + `w` | Window screenshot  |
| `super` + `shift` + `m` | Monitor screenshot |
| `super` + `shift` + `t` | OCR script         |
| `super` + `shift` + `c` | Colour picker      |

## Unbinding

Use `hyprland-custom.conf` and Hyprland's `unbind` funcionality.

See Hyprland docs on how to unbind keys.
