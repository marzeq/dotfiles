#!/bin/bash
# check that we are running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi

paru -Syu --noconfirm
orphans=$(pacman -Qdtq)
if [ -n "$orphans" ]; then
  pacman -Rns $(pacman -Qdtq) --noconfirm
fi
