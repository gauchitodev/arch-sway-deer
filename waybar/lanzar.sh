#!/bin/sh
# Sway llama a este script en lugar de "waybar" a secas, para usar la barra G5.
exec waybar -c "$HOME/.config/g5/waybar/config.jsonc" -s "$HOME/.config/g5/waybar/style.css" "$@"
