local zap_location="${XDG_DATA_HOME:-$HOME/.local/share}/zap/zap.zsh"
if ! [ -f "$zap_location" ]; then
  zsh <(curl -s https://raw.githubusercontent.com/zap-zsh/zap/master/install.zsh) --branch release-v1 --keep
fi
source "$zap_location"

source "$HOME/.config/shells/.zshrc"
source "$HOME/.config/shells/.aliasrc"
source "$HOME/.config/shells/.wsl"

local throwaway="$HOME/.config/shells/.throwaway"
if [ ! -f "$throwaway" ]; then
  touch "$throwaway"
  echo "#!/usr/bin/env bash" >> "$throwaway"
fi
 
source "$throwaway"
# vim: ft=bash
