#!/bin/bash

toggle_mute_volume() {
  wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
}

inc_volume() {
  wpctl set-mute @DEFAULT_AUDIO_SINK@ 0

  if [[ -z "$1" ]]; then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 2%+
  else
    wpctl set-volume @DEFAULT_AUDIO_SINK@ $1%+
  fi
}

dec_volume() {
  wpctl set-mute @DEFAULT_AUDIO_SINK@ 0

  if [[ -z "$1" ]]; then
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 2%-
  else
    wpctl set-volume @DEFAULT_AUDIO_SINK@ $1%-
  fi
}

toggle_mic_mute() {
  wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
}

play_pause() {
  playerctl play-pause
}

play() {
  playerctl play
}

pause() {
  playerctl pause
}

next() {
  playerctl next
}

previous() {
  playerctl previous
}

stop() {
  playerctl stop
}

if [[ "$1" == "toggle_mute_volume" ]]; then
  toggle_mute_volume
elif [[ "$1" == "inc_volume" ]]; then
  inc_volume "$2"
elif [[ "$1" == "dec_volume" ]]; then
  dec_volume "$2"
elif [[ "$1" == "toggle_mic_mute" ]]; then
  toggle_mic_mute
elif [[ "$1" == "play_pause" ]]; then
  play_pause
elif [[ "$1" == "play" ]]; then
  play
elif [[ "$1" == "pause" ]]; then
  pause
elif [[ "$1" == "next" ]]; then
  next
elif [[ "$1" == "previous" ]]; then
  previous
elif [[ "$1" == "stop" ]]; then
  stop
else
  echo "Invalid command"
fi
