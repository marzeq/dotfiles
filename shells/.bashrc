# If not running interactively, dont do anything
[[ $- != *i* ]] && return

. $HOME/.config/shells/.bashrc
. $HOME/.config/shells/.aliasrc
. "$HOME/.config/shells/.wsl"

THROWAWAY=$HOME/.config/shells/.throwaway
if [ ! -f $THROWAWAY ]; then
  touch $THROWAWAY
  echo "#!/usr/bin/env bash" >> $THROWAWAY
fi

. $THROWAWAY
