#!/bin/bash
pkexec ./update.sh
pkill -SIGRTMIN+8 waybar
