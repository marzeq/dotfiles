#!/bin/bash 
set -e

PROGNAME="hypr-ocr"
OUTDIR="/tmp"

IMG_FILENAME="$PROGNAME.png"
IMG_FILEPATH="/tmp/$IMG_FILENAME"

TESSERACT_OUTPUT="$OUTDIR/$PROGNAME"
TXT_FILE="$TESSERACT_OUTPUT.txt"

hyprshot -szm region -f $IMG_FILENAME -o $OUTDIR --silent
mogrify -modulate 100,0 -resize 400% $IMG_FILE
tesseract $IMG_FILEPATH $TESSERACT_OUTPUT &> /dev/null
wl-copy < $TXT_FILE
rm $TXT_FILE $IMG_FILEPATH
