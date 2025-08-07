#!/bin/sh
# This program is licensed under GPLv3
# https://www.gnu.org/licenses/gpl-3.0.html

# Ensure argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <#hex_colour>"
  exit 1
fi

hex_colour="$1"

# Validate hex colour format
case "$hex_colour" in
  \#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) ;;
  *) echo "Error: Invalid hex colour. Use format #RRGGBB."; exit 1 ;;
esac

backup_number=$(date +%s)
gtk3_file="$HOME/.config/gtk-3.0/gtk.css"
gtk4_file="$HOME/.config/gtk-4.0/gtk.css"

# Ensure gsettings exists
command -v gsettings >/dev/null || { echo "Error: gsettings not found."; exit 1; }

# Unlink old config
unlink "$gtk3_file" 2>/dev/null
unlink "$gtk4_file" 2>/dev/null
unlink "$HOME/.config/gtk-3.0/assets" 2>/dev/null
unlink "$HOME/.config/gtk-4.0/assets" 2>/dev/null

# Backup and recreate files
for file in "$gtk3_file" "$gtk4_file"; do
  [ -f "$file" ] && cp "$file" "${file}.${backup_number}.bak" && echo "Backup created: ${file}.${backup_number}.bak"
  mkdir -p "$(dirname "$file")" && touch "$file"
done

# Apply raw hex to gtk-4.0
echo ":root { --accent-bg-color: $hex_colour; }" > "$gtk4_file"

# Write to gtk-3.0
cat <<EOF > "$gtk3_file"
@define-color accent_bg_color $hex_colour;
EOF

# Apply using gsettings
gsettings set org.gnome.desktop.interface accent-color "$hex_colour"

echo "Accent colour set to $hex_colour. Restart apps to apply."
