#!/bin/bash
Xvfb :1 -screen 0 1024x768x24 &
export DISPLAY=:1
export PYNPUT_BACKEND=xorg
