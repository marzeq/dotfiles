#!/bin/sh
gtk3_file="$HOME/.config/gtk-3.0/gtk.css"
gtk4_file="$HOME/.config/gtk-4.0/gtk.css"

command -v gsettings >/dev/null || { echo "Error: gsettings not found."; exit 1; }

restore_backup() {
  file="$1"
  dir=$(dirname "$file")
  name=$(basename "$file")
  latest_backup=$(ls -t "$dir/$name".*.bak 2>/dev/null | head -n 1)

  if [ -n "$latest_backup" ]; then
    cp "$latest_backup" "$file"
    echo "Restored backup: $latest_backup → $file"
  else
    rm -f "$file" && echo "Removed: $file"
  fi
}

unlink "$HOME/.config/gtk-3.0/assets" 2>/dev/null
unlink "$HOME/.config/gtk-4.0/assets" 2>/dev/null

restore_backup "$gtk3_file"
restore_backup "$gtk4_file"
echo "" > ~/.local/share/ignis/accent.scss

gsettings reset org.gnome.desktop.interface accent-color
