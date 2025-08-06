#!/usr/bin/env bash
set -e

if [[ ! -f "/etc/arch-release" ]]; then
  echo "This script is intended for Arch Linux only!"
  exit 1
fi

if [[ -f "/run/archiso/cowspace" ]]; then
  echo "This script is not intended to be run in a live environment!"
  exit 1
fi

if [[ $EUID -eq 0 ]]; then
  echo "Don't run this script as root, you will be asked for sudo permissions when necessary."
  exit 1
fi

RED_BOLD="\033[1;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

SHELLS_DEPS=(
  "stow"

  "zsh"
  "bash"
  "git"                                             # i guess you wouldnt get this far without git but just in case
)

NEOVIM_DEPS=(
  "stow"

  "neovim"

  "fzf"
  "ripgrep"
  "curl"
)

TERMINAL_DEPS=(
  "stow"

  "ghostty"                                         # really couldnt care less about my term, only picked it because ligatures work and nerd fonts arent fucked up
  "ttf-cascadia-code" "ttf-cascadia-code-nerd"      # main mono font
)

DESKTOP_DEPS=(
  "stow"

  "hyprland"                                        # duh

  ".AUR:python-ignis" ".AUR:goignis"                # our shell framework
  "cantarell-fonts"                                 # sans font for the shell
  
  "gdm"                                             # login manager of choice

  "xdg-desktop-portal-hyprland"                     # portals for hyprland
  "xdg-desktop-portal-gtk"                          # for gtk darkmode
  "polkit-gnome"                                    # gtk gui for polkit
  "qt5-wayland" "qt6-wayland"                       # qt wayland support

  "pipewire"                                        # audio server
  "pipewire-pulse" "pipewire-jack" "pipewire-alsa"  # pipewire modules
  "gst-plugin-pipewire"                             # gstreamer pipewire plugin
  "alsa-utils"                                      # alsa utilities

  "hyprpaper"                                       # wallpaper manager
  "hyprpicker"                                      # colour picker
  "hypridle"                                        # idle manager (sleep after inactivity etc.)

  ".AUR:hyprshot" "grim" "slurp"                    # screenshots
  "imagemagick" "tesseract" "tesseract-data-eng"    # needed for area ocr
  ".PARU"                                           # explicitly install aur manager
  ".AUR:clipse-bin" "wl-clipboard"                  # clipboard
  "pamixer" "pavucontrol"                           # audio control
  "nwg-displays"                                    # gui monitor configuration
  "adw-gtk-theme"                                   # gtk3 theme
  "pacman-contrib"                                  # pacman utilities
  "fontconfig"                                      # font configuration

  # my apps
  "nautilus"                                        # file manager
  "firefox"                                         # web browser

  # fonts
  ".AUR:ttf-ms-win11-auto"                          # microsoft fonts, needed for many websites
  ".AUR:ttf-twemoji"                                # our emoji font of choice
)

install_paru() {
  git clone https://aur.archlinux.org/paru-bin.git /tmp/paru-bin
  cd /tmp/paru-bin
  makepkg -si
  cd - > /dev/null
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


shells_installed=false
install_shells() {
  if $shells_installed; then
    return
  fi
  echo -e "${BLUE}Installing shells...${RESET}"
  shells_installed=true
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

neovim_installed=false
install_neovim() {
  if $neovim_installed; then
    return
  fi
  echo -e "${BLUE}Installing neovim...${RESET}"
  neovim_installed=true
  install_packages "${NEOVIM_DEPS[@]}"
  stow -t "$HOME" nvim
}

terminal_installed=false
install_terminal() {
  if $terminal_installed; then
    return
  fi
  echo -e "${BLUE}Installing terminal...${RESET}"
  terminal_installed=true
  install_packages "${TERMINAL_DEPS[@]}"
  stow -t "$HOME" terminal
}

desktop_installed=false
install_desktop() {
  if $desktop_installed; then
    return
  fi
  echo -e "${BLUE}Installing desktop...${RESET}"
  desktop_installed=true
  install_packages "${DESKTOP_DEPS[@]}"
  install_terminal
  stow -t "$HOME" hypr wallpapers ignis

  sudo systemctl enable gdm
  gsettings set org.gnome.desktop.wm.preferences button-layout :

  echo -e "${BLUE}Make sure you run nwg-displays to configure your displays graphically${RESET}"
}

main() {
  first_dir="$(pwd)"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

  cd "$script_dir"

  if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <package>"
    echo "Available packages: shells, neovim, terminal, desktop"
    echo "Or run $0 all to install all packages"
    exit 1
  fi

  echo -e "${RED_BOLD}ATTENTION!${RESET}"
  echo "This script was made for my personal use. You should probably not run it yourself."
  echo "By proceeding, you forefit the right to cry and complain to me about anything that might go wrong."
  read -p "Proceed? (y/n) " -n 1 -r
  echo

  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit
  fi

  if [[ $1 == "shells" ]]; then
    install_shells
  elif [[ $1 == "neovim" ]]; then
    install_neovim
  elif [[ $1 == "terminal" ]]; then
    install_terminal
  elif [[ $1 == "desktop" ]]; then
    install_desktop
  elif [[ $1 == "all" ]]; then
    install_shells
    install_neovim
    install_desktop
  else
    echo "Unknown package: $1"
    cd "$first_dir"
    exit 1
  fi

  cd "$first_dir"
}

main "$@"
