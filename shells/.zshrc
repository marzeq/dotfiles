source "$HOME/.config/shells/.aliasrc"
source "$HOME/.config/shells/.zshrc"

THROWAWAY="$HOME/.config/shells/.throwaway"
if [ ! -f $THROWAWAY ]; then
  touch $THROWAWAY
  echo "#!/usr/bin/env sh" >> $THROWAWAY
fi
 
source "$THROWAWAY"
