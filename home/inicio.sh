#!/bin/sh
# Muestra u oculta la pantalla de inicio G5 (tecla Super+G).
# La pantalla vive en su propio escritorio, "Inicio".
ESCRITORIO="Inicio"
YO=$(id -u)
# Mismo cálculo que server.py: un puerto por usuario
PUERTO="${G5_PUERTO:-$((8765 + (YO > 1000 ? YO - 1000 : 0) % 1000))}"

actual=$(swaymsg -t get_workspaces | jq -r '.[] | select(.focused).name')
if [ "$actual" = "$ESCRITORIO" ]; then
    swaymsg workspace back_and_forth
    exit 0
fi

swaymsg workspace "$ESCRITORIO"

# Si la ventana todavía no existe, la abrimos.
if ! swaymsg -t get_tree | jq -e '[.. | objects | select((.app_id // "") | startswith("chrome-127.0.0.1"))] | length > 0' >/dev/null; then
    pgrep -u "$YO" -f "^python3 $HOME/.config/g5/home/server.py" >/dev/null || {
        "$HOME/.config/g5/home/arrancar.sh" >/dev/null 2>&1 &
        sleep 0.5
    }
    chromium \
        --user-data-dir="$HOME/.local/share/g5/chromium" \
        --app="http://127.0.0.1:$PUERTO/" \
        --no-first-run --no-default-browser-check \
        --disable-pinch --disable-features=Translate --overscroll-history-navigation=0 \
        >/dev/null 2>&1 &
fi
