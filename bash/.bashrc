# If not running interactively, dont do anything
[[ $- != *i* ]] && return

. $HOME/.config/bash/.bashrc
. $HOME/.config/bash/.aliasrc

THROWAWAY=$HOME/.config/bash/.throwaway
if [ ! -f $THROWAWAY ]; then
  touch $THROWAWAY
  echo "#!/usr/bin/env bash" >> $THROWAWAY
fi

. $THROWAWAY
