#!/bin/bash

MODE=$(echo "suspend
logout
reboot
poweroff" | rofi -dmenu -p "Power menu")

if [[ ! -z "$MODE" ]]; then
  if [ $MODE == "logout" ]; then
    hyprctl dispatch exit
  else
    systemctl $MODE
  fi
fi
