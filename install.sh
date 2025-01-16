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
  "imagemagick"                                     # for image.nvim to work
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
  ".AUR:hyprshot" "grim" "slurp"                    # screenshots
  "imagemagick" "tesseract" "tesseract-data-eng"    # needed for area ocr
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

  install_packages "${FONTS_DEPS[@]}"
  echo "Running: $twemojilinkcmd"
  echo "This will require root permissions!"
  eval $twemojilinkcmd

  mkdir -p "$HOME/.local/share/fonts"
  wget -O "/tmp/CascadiaCode.zip" "https://github.com/microsoft/cascadia-code/releases/download/v2404.23/CascadiaCode-2404.23.zip" && \
  unzip -o "/tmp/CascadiaCode.zip" -d "/tmp/CascadiaCode"
  mv "/tmp/CascadiaCode/ttf"/* "$HOME/.local/share/fonts"
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
  install_packages "${NEOVIM_DEPS[@]}"
  install_fonts
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
  install_gpu_drivers # hyprland relies on gpu acceleration
  install_packages "${HYPRLAND_DEPS[@]}"
  install_fonts
  install_ghostty
  stow -t "$HOME" hypr waybar rofi wallpapers gtk3

  echo "Make sure you run nwg-displays to configure your displays graphically"
}

multilib_enabled=false
enable_multilib() {
  if $multilib_enabled; then
    return
  fi
  multilib_enabled=true
  if ! grep -q "^\[multilib\]" /etc/pacman.conf; then
    echo "Enabling multilib repository"
    echo "[multilib]" | sudo tee -a /etc/pacman.conf
    echo "Include = /etc/pacman.d/mirrorlist" | sudo tee -a /etc/pacman.conf

    sudo pacman -Sy --noconfirm
  fi
}

gpu_dr_installed=false
install_gpu_drivers() {
  if $gpu_dr_installed; then
    return
  fi
  gpu_dr_installed=true
  install_packages "mesa" "libva-mesa-driver" "mesa-vdpau"
  for gpu in /sys/class/drm/card[0-9]/device; do
    if [[ -d $gpu ]]; then
      vendor_id="$(cat $gpu/vendor)"

      if [[ $vendor_id == "0x1002" ]]; then
        echo "AMD GPU detected"
        install_packages "vulkan-radeon"
      elif [[ $vendor_id == "0x8086" ]]; then
        echo "Intel GPU detected"
        install_packages "vulkan-intel" "intel-media-driver"
      elif [[ $vendor_id == "0x10de" ]]; then
        install_packages "nvidia-dkms" "nvidia-utils"
      else
        echo "Unknown GPU vendor for GPU $gpu, install drivers in this shell and exit to continue the process"
        bash
      fi
    fi
  done
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

  if [[ $1 == "shells" ]]; then
    install_shells
  elif [[ $1 == "neovim" ]]; then
    install_neovim
  elif [[ $1 == "ghostty" ]]; then
    install_ghostty
  elif [[ $1 == "hyprland" ]]; then
    install_hyprland
  elif [[ $1 == "fonts" ]]; then
    install_fonts
  elif [[ $1 == "gaming" ]]; then
    install_gaming
  elif [[ $1 == "all" ]]; then
    install_gaming
    install_shells
    install_neovim
    install_hyprland
  else
    echo "Unknown package: $1"
    cd "$first_dir"
    exit 1
  fi

  cd "$first_dir"
}

main "$@"
