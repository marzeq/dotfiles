#!/bin/bash

SLEEP="Sleep"
LOGOUT="Logout"
REBOOT="Reboot"
SHUTDOWN="Shutdown"
UEFI="UEFI Settings"

MODE=$(echo "$SLEEP
$LOGOUT
$REBOOT
$SHUTDOWN
$UEFI" | rofi -dmenu -p "Power menu" -i)

if [[ ! -z "$MODE" ]]; then
  if [ "$MODE" == "$LOGOUT" ]; then
    hyprctl dispatch exit
  elif [ "$MODE" == "$REBOOT" ]; then
    systemctl reboot
  elif [ "$MODE" == "$SHUTDOWN" ]; then
    systemctl poweroff
  elif [ "$MODE" == "$SLEEP" ]; then
    systemctl suspend
  elif [ "$MODE" == "$UEFI" ]; then
    systemctl reboot --firmware-setup
  elif [ "$MODE" == "bar" ]; then
    pkill waybar; hyprctl dispatch exec waybar
  fi
fi
