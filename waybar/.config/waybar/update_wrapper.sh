#!/bin/bash
UPDATES=$(~/.config/waybar/update_count.sh)
if [[ -z "$UPDATES" ]]; then
  UPDATES=0
fi
if [[ "$UPDATES" -gt 0 ]]; then
  NOTIFY_STR="Updated $UPDATES package"
  if [[ "$UPDATES" -gt 1 ]]; then
    NOTIFY_STR="${NOTIFY_STR}s"
  fi
  ~/.config/waybar/update.sh && pkill -SIGRTMIN+8 waybar && notify-send -u normal "Update" "$NOTIFY_STR"
else
  pkill -SIGRTMIN+8 waybar
fi
