#!/bin/bash

for f in $HOME/.config/autostart/*.desktop; do
  gio launch $f
done
