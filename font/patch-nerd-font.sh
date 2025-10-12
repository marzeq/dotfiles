#!/usr/bin/env bash

PATCHER_URL="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"
PATCHER_FN="FontPatcher.zip"
PATCHER_DIR="font-patcher"

FONT_ZIP="CommitMonoV143.zip"
FONT_EXTRACT_DIR="extracted-fonts"

wget -O "$PATCHER_FN" "$PATCHER_URL"
unzip -q "$PATCHER_FN" -d "$PATCHER_DIR"

mkdir -p "$FONT_EXTRACT_DIR"
unzip -q "$FONT_ZIP" -d "$FONT_EXTRACT_DIR"

for fontfile in "$FONT_EXTRACT_DIR"/*.otf; do
  "$PATCHER_DIR/font-patcher" "$fontfile" --complete --outputdir .
done

rm -rf "$PATCHER_FN" "$PATCHER_DIR" "$FONT_EXTRACT_DIR"
