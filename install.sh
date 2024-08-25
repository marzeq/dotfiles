#!/usr/bin/env bash

SHELLS_DEPS=(
  "zsh"
  "bash"
  "git"
)

NEOVIM_DEPS=(
  "neovim"
  "python"
  "fzf"
  "ripgrep"
  "nodejs"
  "npm"
  "curl"
  ".PARU"
  ".AUR:prettierd"
)

ALACRITTY_DEPS=(
  "alacritty"
)

HYPRLAND_DEPS=(
  "hyprland"
  "xdg-desktop-portal-hyprland"
  "hyprpaper"
  "hyprpicker"
  "rofi-wayland"
  "alacritty"
  "nautilus"
  "firefox"
  "grim" "slurp"
  "wl-clip-persist" "clipse"
  "swaync"
  "pamixer"

  "waybar"
  ".PARU"
  "pavucontrol"
  "pacman-contrib"
)

install_paru() {
  git clone https://aur.archlinux.org/paru-bin.git
  cd paru-bin
  makepkg -si
  cd ..
  rm -rf paru-bin
}

install_packages() {
  # filter out AUR packages
  local aur_packages=()
  local pacman_packages=()
  local install_paru=false

  for package in "$@"; do
    if [[ $package == ".AUR:"* ]]; then
      aur_packages+=("${package:5}")
      install_paru=true
    elif [[ $package == ".PARU" ]]; then
      install_paru=true
    else
      pacman_packages+=("$package")
    fi
  done

  if command -v paru &> /dev/null; then
    install_paru=false
  fi

  if $install_paru; then
    install_paru
  fi

  if [[ ${#aur_packages[@]} -gt 0 ]]; then
    paru -S --noconfirm "${aur_packages[@]}"
  fi

  if [[ ${#pacman_packages[@]} -gt 0 ]]; then
    sudo pacman -S --noconfirm "${pacman_packages[@]}"
  fi
}

install_shells() {
  install_packages "${SHELLS_DEPS[@]}"
  stow -t "$HOME" shells
}

install_neovim() {
  install_packages "${NEOVIM_DEPS[@]}"
  stow -t "$HOME" nvim
}

install_alacritty() {
  install_packages "${ALACRITTY_DEPS[@]}"
  stow -t "$HOME" alacritty
}

install_hyprland() {
  install_packages "${HYPRLAND_DEPS[@]}"
  stow -t "$HOME" hypr waybar rofi wallpapers
}

main() {
  if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <package>"
    echo "Available packages: shells, neovim, alacritty, hyprland"
    exit 1
  fi

  case $1 in
    "shells")
      install_shells
      ;;
    "neovim")
      install_neovim
      ;;
    "alacritty")
      install_alacritty
      ;;
    "hyprland")
      install_hyprland
      ;;
    *)
      echo "Unknown package: $1"
      exit 1
      ;;
  esac
}

main "$@"
