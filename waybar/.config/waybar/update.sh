#!/bin/bash
paru -Syu --noconfirm
orphans=$(pacman -Qdtq)
if [ -n "$orphans" ]; then
  sudo pacman -Rns $(pacman -Qdtq) --noconfirm
fi
