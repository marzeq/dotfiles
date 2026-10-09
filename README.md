# dotfiles

This is my personal dotfiles repository for Hyprland, Neovim, and other applications.

Every component is opt-in. Using only the desktop, only Neovim, only the shell configuration, or any combination of
components is supported and encouraged; there is no need to adopt the entire setup.

## Components

- **Desktop** — a Hyprland desktop with a custom shell. Installing it through the management CLI also installs the
  Terminal component.
- **Neovim** — a ready-to-use Neovim configuration.
- **Shells** — shared Bash and Zsh configuration for an ergonomic command-line environment.
- **Terminal** — Ghostty configuration and the accompanying terminal font.

The desktop targets Arch Linux and Hyprland. The Neovim, shell and Ghostty configurations are not tied to Arch and also
work on macOS.

### Personal extras

- **mpv** — my personal player configuration.
- **Wallpapers** — the background collection I use with the desktop.

These are not managed by the installer and are more “mine” than components designed for general use, but they remain
available to copy or Stow manually.

The installer is an optional convenience, not a requirement or a special runtime for these configurations. On Arch it can
install dependencies, Stow selected components and remember that selection for later updates or removal. The underlying
files remain ordinary dotfiles. Advanced users can instead use Git and GNU Stow directly, mapping the dependency lists in
the `marzeq-dotfiles` script to equivalent packages for their distribution or macOS. See the installation guide for both
approaches.

The Hyprland configuration is a faithful adaptation of how the GNOME desktop environment looks and feels,
while preserving the superior ergonomics of a tiler like Hyprland. All design credits go to the GNOME team where due.

The Neovim setup is my personal balance between minimalism and IDE-like usability, so I get all of the modern features
I deem necessary without the bloat and unresponsiveness.

## Installation

Instructions [here](./INSTALL.md).

## Notes/info for customisation

[Here](./NOTES.md).

## Desktop overview

![The desktop with tiled applications and the Ignis settings window](./screenshots/hero.png)

### Launcher

The unified launcher searches installed applications and also provides calculator, currency-conversion and power-action
modes.

![Application launcher](./screenshots/launcher.png)

### Control centre

Frequently used audio, network, Bluetooth, power-profile and session controls are available from the status area without
leaving the current workspace. Just like GNOME.

![Control centre](./screenshots/cc.png)

### Notifications and calendar

The clock opens a combined view for media controls, notifications and the calendar. Again, just like GNOME.

![Notifications, media controls and calendar](./screenshots/nc.png)

### Integrated settings

Shell appearance, display arrangement and Hyprland behavior can be configured graphically.

I share GNOME's “do not break colours” philosophy: personalisation should preserve the contrast and visual hierarchy
designed into the interface. The shell still offers more extensive accent-colour customisation than GNOME itself,
including wallpaper-derived suggestions and arbitrary custom colours. Suggested accents are chosen with legibility in
mind, while custom colours remain available for people who want full control.

![Wallpaper and accent colour settings](./screenshots/settings_appearance.png)

Displays can be arranged and configured without editing the Hyprland configuration by hand. You don't often see this in a tiler,
do you :)?

![Display configuration](./screenshots/settings_displays.png)

Hyprland shortcuts can be enabled, disabled and remapped individually.

![Shortcut configuration](./screenshots/settings_shortcuts.png)

Of course, the settings window has more sections than shown here.

## Neovim

![2025-10-01-190830_hyprshot](https://github.com/user-attachments/assets/7e574460-4892-4093-9024-51c8472a38c0)
![2025-10-01-190841_hyprshot](https://github.com/user-attachments/assets/17e991b6-c1c6-4969-b2a5-1b4bd79e72b7)
