#!/bin/bash
remove-orphans() {
  orphans=$(pacman -Qdtq)
  if [ -n "$orphans" ]; then
    sudo pacman -Rns $(pacman -Qdtq) --noconfirm
  fi
}

paru -Syu --noconfirm && remove-orphans
pkill -SIGRTMIN+8 waybar

