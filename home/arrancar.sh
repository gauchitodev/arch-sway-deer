#!/bin/sh
# Arranca (o reinicia) el servidor de la pantalla de inicio G5.
pkill -u "$(id -u)" -f "^python3 $HOME/.config/g5/home/server.py"
exec python3 "$HOME/.config/g5/home/server.py"
