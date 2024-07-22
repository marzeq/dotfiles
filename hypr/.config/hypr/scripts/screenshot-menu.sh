FILENAME=$(date "+%Y-%m-%d %H-%M-%S").png

# Take screenshot
grim -g "$(slurp -d)" - > "/tmp/${FILENAME}"

# if file is empty (user cancelled), exit

if [ ! -s "/tmp/${FILENAME}" ]; then
  rm "/tmp/${FILENAME}"
  exit
fi

wl-copy -t image/png < "/tmp/${FILENAME}"
mkdir -p ~/Pictures/Screenshots
mv "/tmp/${FILENAME}" ~/Pictures/Screenshots/

