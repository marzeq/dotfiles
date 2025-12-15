#!/bin/bash
layout=$(hyprctl getoption general:layout | grep -oE '(master|dwindle)')
case "$layout" in
  master)
    hyprctl dispatch layoutmsg swapwithmaster master
    ;;
  dwindle)
    hyprctl dispatch togglesplit
    ;;
esac
