#!/usr/bin/env bash

if [[ "$1" == "first-start" ]]; then
  if [[ -f ~/.local/share/awww-first-start-done ]]; then
    exit 0
  fi

  touch ~/.local/share/awww-first-start-done
  wallpaper="~/.config/ignis/default_wallpaper.jpg"
else
  wallpaper=$(jq -r '.wallpaper // empty' ~/.local/share/ignis/settings/style.json)
  if [[ -z "$wallpaper" ]] || [[ ! -f "$wallpaper" ]]; then
    wallpaper="~/.config/ignis/default_wallpaper.jpg"
  fi
fi

ln -s "$wallpaper" ~/.local/state/wallpaper

awww img "$wallpaper" \
  --transition-fps=144 \
  --transition-step=128 \
  --transition-type=any
