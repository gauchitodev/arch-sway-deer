#!/bin/sh
# Tecla de calculadora: abre la Calculadora G5. Si ya está abierta la trae
# al frente, y si ya estaba al frente la cierra.
TITULO='^Calculadora G5$'

enfocada=$(swaymsg -t get_tree | jq -r '.. | objects | select(.focused == true) | .name // ""')
existe=$(swaymsg -t get_tree | jq '[.. | objects | select((.name // "") == "Calculadora G5")] | length')

if [ "$existe" -gt 0 ]; then
    if [ "$enfocada" = "Calculadora G5" ]; then
        swaymsg "[title=\"$TITULO\"] kill" >/dev/null
    else
        swaymsg "[title=\"$TITULO\"] focus" >/dev/null
    fi
    exit 0
fi

# Mismo modo (día o noche) que la pantalla de inicio
modo=$(jq -r '.modo // "dia"' "$HOME/.config/g5/home/estado.json" 2>/dev/null)
[ "$modo" = "noche" ] || modo="dia"

exec chromium \
    --user-data-dir="$HOME/.local/share/g5/calculadora" \
    --app="file://$HOME/.config/g5/calculadora/index.html#$modo" \
    --no-first-run --no-default-browser-check \
    --disable-features=Translate --disable-pinch \
    >/dev/null 2>&1
