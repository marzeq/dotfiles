source "$HOME/.config/shells/.zshrc"
source "$HOME/.config/shells/.aliasrc"
source "$HOME/.config/shells/.wsl"

THROWAWAY="$HOME/.config/shells/.throwaway"
if [ ! -f $THROWAWAY ]; then
  touch $THROWAWAY
  echo "#!/usr/bin/env bash" >> $THROWAWAY
fi
 
source "$THROWAWAY"
