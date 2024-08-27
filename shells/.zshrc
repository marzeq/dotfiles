[ -f "${XDG_DATA_HOME:-$HOME/.local/share}/zap/zap.zsh" ] && source "${XDG_DATA_HOME:-$HOME/.local/share}/zap/zap.zsh"

source "$HOME/.config/shells/.aliasrc"
source "$HOME/.config/shells/.zshrc"
source "$HOME/.config/shells/.wsl"

THROWAWAY="$HOME/.config/shells/.throwaway"
if [ ! -f $THROWAWAY ]; then
  touch $THROWAWAY
  echo "#!/usr/bin/env sh" >> $THROWAWAY
fi
 
source "$THROWAWAY"
