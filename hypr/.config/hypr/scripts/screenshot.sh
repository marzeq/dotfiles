FOLDER="$HOME/pictures/screenshots/"
mkdir -p $FOLDER

if [[ ! -z "$1" ]]; then
  MODE=$1
else
  MODE=$(echo "area
window
monitor" | rofi -dmenu -p "Screenshot")

  sleep 0.2
fi


if [[ ! -z "$MODE" ]]; then
  if [ $MODE == "window" ]; then
    hyprshot -szm window -o $FOLDER
  elif [ $MODE == "area" ]; then
    hyprshot -szm region -o $FOLDER
  elif [ $MODE == "monitor" ]; then
    hyprshot -szm output -o $FOLDER
  fi
fi
