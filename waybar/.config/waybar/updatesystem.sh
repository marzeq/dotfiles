#!/bin/bash
remove-orphans() {
  orphans=$(pacman -Qdtq)
  if [ -n "$orphans" ]; then
    sudo pacman -Rns $(pacman -Qdtq)
  fi
}

paru && remove-orphans
pkill -SIGRTMIN+8 waybar

