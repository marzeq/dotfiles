#!/bin/bash

entries=(
  "Sleep"         "systemctl suspend"
  "Logout"        "hyprctl dispatch exit"
  "Reboot"        "systemctl reboot"
  "Shutdown"      "systemctl poweroff"
  "UEFI Settings" "systemctl reboot --firmware-setup"
)

options=()
commands=()
for ((i = 0; i < ${#entries[@]}; i += 2)); do
  options+=("${entries[i]}")
  commands+=("${entries[i + 1]}")
done

selected=$(printf "%s\n" "${options[@]}" | rofi -dmenu -p "Power menu" -i -format i)
eval "${commands[$selected]}"
