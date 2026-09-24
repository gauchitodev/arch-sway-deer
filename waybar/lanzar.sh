#!/bin/sh
# Sway llama a este script en lugar de "waybar" a secas, para usar la barra G5.
# Antes arranca (o reinicia) el medidor de carga del internet, que dibuja la
# rampa en segundo plano y le avisa a la barra cuando cambia.
pkill -u "$(id -u)" -f "^python3 $HOME/.config/g5/waybar/carga-red.py" 2>/dev/null
python3 "$HOME/.config/g5/waybar/carga-red.py" >/dev/null 2>&1 &
exec waybar -c "$HOME/.config/g5/waybar/config.jsonc" -s "$HOME/.config/g5/waybar/style.css" "$@"
