#!/bin/bash

for f in $HOME/.config/autostart/*.desktop; do
  gio launch $f
done

eval "$(ssh-agent -s)"
if [ -f $HOME/.ssh/sshkey ]; then
  ssh-add $HOME/.ssh/sshkey
fi
