#!/usr/bin/env bash

if [[ ! -f "/etc/arch-release" ]]; then
  echo "This script is intended for Arch Linux only!"
  exit 1
fi

if [[ -f "/run/archiso/cowspace" ]]; then
  echo "This script is not intended to be run in a live environment!"
  exit 1
fi

if [[ $EUID -eq 0 ]]; then
  echo "This script shall not be run as root!"
  exit 1
fi

SHELLS_DEPS=(
  "stow"

  "zsh"                                             # best shell ever
  "bash"                                            # just in case you somehow dont have bash
  "git"                                             # i guess you wouldnt get this far without git but just in case
)

NEOVIM_DEPS=(
  "stow"

  "neovim"                                          # duh

  "python"                                          # honestly i dont remember why but its probably important if its here
  "fzf"                                             # fzf is a godsend
  "ripgrep"                                         # same for you rg <3
  "nodejs" "npm"                                    # i think this is needed for a lot of lsp stuff
  "curl"                                            # for downloading stuff
)

GHOSTTY_DEPS=(
  "stow"

  "ghostty"                                         # duh
)

FONTS_DEPS=(
  "wget"                                            # for downloading stuff (again)
  "unzip"                                           # why is .zip still a thinggg
  "fontconfig"                                      # duh
  
  ".AUR:ttf-ms-win11-auto"                          # microsoft fonts, needed for many websites
  ".AUR:ttf-twemoji"                                # our emoji font of choice
)

HYPRLAND_DEPS=(
  "stow"

  "hyprland"                                        # duh

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

  "rofi-wayland"                                    # app launcher
  ".AUR:grimblast-git" "grim" "slurp"               # screenshots
  "waybar"                                          # status bar
  ".PARU"                                           # explicitly install aur manager
  ".AUR:clipse-bin" "wl-clipboard"                  # clipboard
  "swaync"                                          # notifications
  "pamixer" "pavucontrol"                           # audio control
  "nwg-displays"                                    # gui monitor configuration
  "adw-gtk-theme"                                   # gtk3 theme
  "pacman-contrib"                                  # for update module in waybar

  # my apps
  "nautilus"                                        # file manager
  "firefox"                                         # web browser
)

GAMING_DEPS=(
  "steam"                                           # duh
  ".AUR:proton-ge-custom-bin"                       # latest proton-ge
  "gamemode"                                        # cpu governor optimisation, to squeeze out a couple more framses
  "gamescope"                                       # game compositor
  "mangohud"                                        # performance monitoring hud
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


fonts_installed=false
install_fonts() {
  if $fonts_installed; then
    return
  fi
  fonts_installed=true
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

shells_installed=false
install_shells() {
  if $shells_installed; then
    return
  fi
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
  neovim_installed=true
  install_packages "${NEOVIM_DEPS[@]}" && \
  install_fonts && \
  stow -t "$HOME" nvim
}

ghostty_installed=false
install_ghostty() {
  if $ghostty_installed; then
    return
  fi
  ghostty_installed=true
  install_packages "${GHOSTTY_DEPS[@]}" && \
  install_fonts && \
  stow -t "$HOME" ghostty
}

hyprland_installed=false
install_hyprland() {
  if $hyprland_installed; then
    return
  fi
  hyprland_installed=true
  install_gpu_drivers && \ # hyprland relies on gpu acceleration
  install_packages "${HYPRLAND_DEPS[@]}" && \
  install_fonts && \
  install_ghostty && \
  stow -t "$HOME" hypr waybar rofi wallpapers gtk3 && \

  echo "Make sure you run nwg-displays to configure your displays graphically"
}

check_yn() {
  local prompt="$1"

  if [[ -z "$prompt" ]]; then
    prompt="Are you sure?"
  fi

  echo -n "$prompt [y/n]: "

  while true; do
    read -r response
    case $response in
      [Yy]*)
        return 0
        ;;
      [Nn]*)
        return 1
        ;;
      *)
        echo -n "$prompt [y/n]: "
        ;;
    esac
  done
}

enable_multilib() {
  if ! grep -q "^\[multilib\]" /etc/pacman.conf; then
    echo "Enabling multilib repository"
    echo "[multilib]" | sudo tee -a /etc/pacman.conf
    echo "Include = /etc/pacman.d/mirrorlist" | sudo tee -a /etc/pacman.conf

    sudo pacman -Sy --noconfirm
  fi
}

install_gpu_drivers() {
  if [[ -f "/sys/class/drm/card0/device/vendor" ]]; then
    if [[ "$(cat /sys/class/drm/card0/device/vendor)" == "0x1002" ]]; then
      local pkglist=("mesa" "vulkan-radeon" "libva-mesa-driver" "mesa-vdpau")

      echo "AMD GPU detected, installing packages: ${pkglist[@]}"
      check_yn "Do you want to install these packages?" && install_packages "${pkglist[@]}"
    elif [[ "$(cat /sys/class/drm/card0/device/vendor)" == "0x10de" ]]; then
      local lspci_output=$(lspci -k | grep -A 2 -E "(VGA|3D)")
      local common_packages=("nvidia-utils" "nvidia-settings")
      
      if echo "$lspci_output" | grep -qE "GTX 1650|20[0-9]{2}|30[0-9]{2}|40[0-9]{2}"; then
        echo "Modern NVIDIA GPU (1650, 20xx, 30xx, or 40xx series) detected, installing these packages: nvidia-open ${common_packages[@]}"
        check_yn "Do you want to install these packages?" && install_packages "nvidia-open" "${common_packages[@]}"
      else
        echo "Older NVIDIA GPU detected, installing these packages: nvidia ${common_packages[@]}"
        check_yn "Do you want to install these packages?" && install_packages "nvidia" "${common_packages[@]}"
      fi
    else
      echo "Unknown GPU vendor, install GPU drivers in this shell and exit to continue the process"
      bash
    fi
  fi
}

install_gaming() {
  enable_multilib

  install_gpu_drivers

  install_packages "${GAMING_DEPS[@]}"
}

main() {
  first_dir="$(pwd)"
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

  cd "$script_dir"

  if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <package>"
    echo "Available packages: shells, neovim, ghostty, hyprland, fonts, gaming"
    echo "Or run $0 all to install all packages"
    exit 1
  fi

  case $1 in
    "shells")
      install_shells
      ;;
    "neovim")
      install_neovim
      ;;
    "ghostty")
      install_ghostty
      ;;
    "hyprland")
      install_hyprland
      ;;
    "fonts")
      install_fonts
      ;;
    "gaming")
      install_gaming
      ;;
    "all")
      install_gaming && \
      install_shells && \
      install_neovim && \
      install_hyprland
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
