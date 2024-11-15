STATUS=$(playerctl status 2> /dev/null)
EXITCODE=$?

if [ "$STATUS" = "No players found" ]; then
    exit 1
fi

# get artist and title
ARTIST=$(playerctl metadata artist)
TITLE=$(playerctl metadata title)

if [ "$STATUS" = "Playing" ]; then
    echo "
$ARTIST - $TITLE"
elif [ "$STATUS" = "Paused" ] || [ "$STATUS" = "Stopped" ]; then
    echo "
$ARTIST - $TITLE"
fi

exit $EXITCODE
