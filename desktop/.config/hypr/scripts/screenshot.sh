FOLDER="$HOME/pictures/screenshots"
mkdir -p "$FOLDER"
FILE="$(date +%Y-%m-%d-%H-%M-%S)-$(date +%3N).png"

MODE="$1"
case "$MODE" in
  window)  HYPR_MODE="window" ;;
  area)    HYPR_MODE="region" ;;
  monitor) HYPR_MODE="output" ;;
  *)
    echo "Usage: $0 [window|area|monitor]" >&2
    exit 1
    ;;
esac

ERR=$(mktemp)

hyprshot -szm "$HYPR_MODE" -o "$FOLDER" -f "$FILE" 2>"$ERR"
HYPR_ERR=$(cat "$ERR")
rm -f "$ERR"

sleep 0.2

if [ -n "$HYPR_ERR" ]; then
  echo "Error taking screenshot: $HYPR_ERR" >&2
  exit 1
fi

if ! [ -f "$FOLDER/$FILE" ]; then
  echo "Error: Screenshot file not found: $FOLDER/$FILE" >&2
  exit 1
fi

ACTION=$(notify-send \
  --icon="$FOLDER/$FILE" \
  --app-name="Screenshot" \
  -A open="Open" \
  "Screenshot saved" "$FILE")

if [ "$ACTION" = "open" ]; then
  xdg-open "$FOLDER/$FILE" >/dev/null 2>&1 &
fi
