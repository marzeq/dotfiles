FOLDER="$HOME/pictures/screenshots/"
mkdir -p $FOLDER

if [[ ! -z "$1" ]]; then
  MODE=$1
else
  echo "Usage: $0 [window|area|monitor]"
  exit 1
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
