#!/usr/bin/env bash

if [[ ! -f "/etc/arch-release" ]]; then
  echo "This script is intended for Arch Linux only!"
  exit 1
fi

if [[ $EUID -eq 0 ]]; then
  echo "This script shall not be run as root!"
  exit 1
fi

SHELLS_DEPS=(
  "stow"
  "zsh"
  "bash"
  "git"
)

NEOVIM_DEPS=(
  "stow"
  "neovim"
  "python"
  "fzf"
  "ripgrep"
  "nodejs"
  "npm"
  "curl"
  "stylua"
  ".AUR:prettierd"
)

ALACRITTY_DEPS=(
  "stow"
  "alacritty"
)

FONTS_DEPS=(
  "wget"
  "unzip"
  "fontconfig"
  
  ".AUR:ttf-ms-win11-auto" # microsoft fonts, needed for many websites
  ".AUR:ttf-twemoji" # out emoji font of choice
)

HYPRLAND_DEPS=(
  "stow"
  "hyprland"
  "xdg-desktop-portal-hyprland"
  "xdg-desktop-portal-gtk" # for gtk darkmode
  "polkit-gnome"
  "hyprpaper"
  "hyprpicker"
  "rofi-wayland"
  "alacritty"
  "nautilus"
  "firefox"
  "grim" "slurp"
  ".AUR:clipse-bin" "wl-clipboard"
  "swaync"
  "pamixer"
  "nwg-displays"
  "adw-gtk-theme"
  "waybar"
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

install_fonts() {
  local twemojilinkcmd="sudo ln -sf /usr/share/fontconfig/conf.avail/75-twemoji.conf /etc/fonts/conf.d/75-twemoji.conf"

  install_packages "${FONTS_DEPS[@]}" && \
  echo "Running: $twemojilinkcmd" && \
  echo "This will require root permissions!" && \
  eval $twemojilinkcmd && \

  mkdir -p "$HOME/.local/share/fonts" && \
  wget -O "/tmp/CascadiaCode.zip" "https://github.com/microsoft/cascadia-code/releases/download/v2404.23/CascadiaCode-2404.23.zip" && \
  unzip -o "/tmp/CascadiaCode.zip" -d "/tmp/CascadiaCode" && \
  mv "/tmp/CascadiaCode/ttf"/* "$HOME/.local/share/fonts" && \
  fc-cache -f
}

install_shells() {
  install_packages "${SHELLS_DEPS[@]}"
  if [[ -f "$HOME/.bashrc" ]]; then
    mv "$HOME/.bashrc" "$HOME/.bashrc.bak"
    echo "Moved existing .bashrc to .bashrc.bak"
  fi
  if [[ -f "$HOME/.zshrc" ]]; then
    mv "$HOME/.zshrc" "$HOME/.zshrc.bak"
    echo "Moved existing .zshrc to .zshrc.bak"
  fi
  stow -t "$HOME" shells
}

install_neovim() {
  install_packages "${NEOVIM_DEPS[@]}" && \
  install_fonts && \
  stow -t "$HOME" nvim
}

install_alacritty() {
  install_packages "${ALACRITTY_DEPS[@]}" && \
  install_fonts && \
  stow -t "$HOME" alacritty
}

install_hyprland() {
  install_packages "${HYPRLAND_DEPS[@]}" && \
  install_fonts && \
  stow -t "$HOME" hypr waybar rofi wallpapers gtk3 && \

  echo "Make sure you run nwg-displays to configure your displays graphically"
}

main() {
  first_dir="$(pwd)"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

  cd "$script_dir"

  if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <package>"
    echo "Available packages: shells, neovim, alacritty, hyprland, fonts"
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
    "fonts")
      install_fonts
      ;;
    *)
      echo "Unknown package: $1"
      cd "$first_dir"
      exit 1
      ;;
  esac

  cd "$first_dir"
}

main "$@"
