#!/bin/sh
# La pantalla de inicio es una capa encima de tu escritorio. Este vigilante la esconde sola
# cuando se abre otra ventana (si no, quedaría tapada por la capa) o cuando cambiás de escritorio.
APP='[app_id="^chrome-127\.0\.0\.1"]'

# Uno solo por sesión (exec_always lo vuelve a lanzar en cada recarga)
for viejo in $(pgrep -u "$(id -u)" -f "^sh $HOME/.config/g5/home/vigilar.sh"); do
    [ "$viejo" != "$$" ] && kill "$viejo" 2>/dev/null
done

swaymsg -t subscribe -m '["window","workspace"]' | while read -r evento; do
    hay=$(printf '%s' "$evento" | jq -r '
        if (.change == "focus" and .current != null) then "escritorio"
        elif (.change == "new" and ((.container.app_id // "") | startswith("chrome-127.0.0.1") | not)) then "ventana"
        else empty end')
    [ -n "$hay" ] && swaymsg -q "$APP move scratchpad" 2>/dev/null
done
