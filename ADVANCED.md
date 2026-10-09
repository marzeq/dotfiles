# Advanced manual installation

This path is intended for advanced users who are comfortable managing their own packages, dotfile links and updates.
For the supported Arch Linux x86-64 experience, use the [managed installation](./INSTALL.md) instead.

## Portable components

The `shells`, `nvim` and `terminal` packages are not Linux-specific and also work on macOS. Clone the repository directly,
install GNU Stow and each application's dependencies using your own package manager, then Stow only the packages you
want. For example:

```bash
git clone https://github.com/marzeq/dotfiles.git
cd dotfiles
stow -t "$HOME" shells nvim terminal
```

The final command is only an example: pass one package or any combination. Ghostty itself and the bundled terminal font
must also be installed manually; the font files are in `font/`.

## Dependencies

Use the `SHELLS_DEPS`, `NEOVIM_DEPS`, `TERMINAL_DEPS` and `DESKTOP_DEPS` lists near the top of the
[`marzeq-dotfiles`](./marzeq-dotfiles) script as the dependency reference. Map each listed Arch package one-to-one to its
equivalent on your distribution or macOS. You are responsible for installing, updating and troubleshooting those
packages yourself.

For a manual installation, the equivalent of `marzeq-dotfiles update` is to run `git pull` inside the cloned repository,
update the packages you mapped from those dependency lists and re-run GNU Stow for your chosen components.

## Desktop and personal extras

`desktop` is Linux-specific and targets Hyprland, so it is not supported on macOS. You can still Stow it manually on
other distributions, but you must resolve and manage its full dependency set yourself. In the managed path, installing
`desktop` also installs `terminal`; reproduce that dependency manually if you want the setup as designed.

The `mpv` and `wallpapers` directories can likewise be copied or Stowed manually, but they are deliberately not tracked
by the management CLI. They are personal extras rather than supported installation components.
