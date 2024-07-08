VOLUME=$(seq 0 100 | rofi -dmenu -p "Set your volume")

if [[ ! -z "$VOLUME" ]]; then
  pamixer --set-volume $VOLUME
fi

