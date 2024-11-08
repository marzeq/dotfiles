#!/bin/bash

MODE=$(echo "sleep
logout
reboot
shutdown" | rofi -dmenu -p "Power menu")

if [[ ! -z "$MODE" ]]; then
  if [ $MODE == "logout" ]; then
    hyprctl dispatch exit
  elif [ $MODE == "reboot" ]; then
    systemctl reboot
  elif [ $MODE == "shutdown" ]; then
    systemctl poweroff
  elif [ $MODE == "sleep" ]; then
    systemctl suspend
  fi
fi
