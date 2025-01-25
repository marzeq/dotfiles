#!/bin/bash

MODE=$(echo "Sleep
Logout
Reboot
Shutdown" | rofi -dmenu -p "Power menu")

if [[ ! -z "$MODE" ]]; then
  if [ $MODE == "Logout" ]; then
    hyprctl dispatch exit
  elif [ $MODE == "Reboot" ]; then
    systemctl reboot
  elif [ $MODE == "Shutdown" ]; then
    systemctl poweroff
  elif [ $MODE == "Sleep" ]; then
    systemctl suspend
  elif [ $MODE == "bar" ]; then
    pkill waybar; hyprctl dispatch exec waybar
  fi
fi
