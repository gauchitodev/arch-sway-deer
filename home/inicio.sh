#!/bin/sh
# Muestra u oculta la pantalla de inicio G5 (tecla Super+G o el botón Inicio de la barra).
# Es una capa encima de tu escritorio (el scratchpad de sway): no tiene escritorio propio,
# y al esconderla quedás exactamente donde estabas.
APP='[app_id="^chrome-127\.0\.0\.1"]'
YO=$(id -u)
# Mismo cálculo que server.py: un puerto por usuario
PUERTO="${G5_PUERTO:-$((8765 + (YO > 1000 ? YO - 1000 : 0) % 1000))}"

# ¿Existe la ventana? ¿Se está viendo ahora?
estado() {
    swaymsg -t get_tree | jq -r '[.. | objects | select((.app_id // "") | startswith("chrome-127.0.0.1"))][0]
        | if . == null then "no" elif .visible then "visible" else "escondida" end'
}

case "$(estado)" in
    visible)
        swaymsg -q "$APP move scratchpad"
        exit 0
        ;;
    no)
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
        # Espera a que aparezca (sway la manda al scratchpad sola, por la regla de sway.conf)
        i=0
        while [ "$(estado)" = no ] && [ $i -lt 50 ]; do sleep 0.2; i=$((i + 1)); done
        ;;
esac

# Mostrarla ocupando todo el escritorio actual (sin tapar la barra de arriba)
set -- $(swaymsg -t get_workspaces | jq -r '.[] | select(.focused).rect | "\(.x) \(.y) \(.width) \(.height)"')
swaymsg -q "$APP scratchpad show, resize set $3 px $4 px, move absolute position $1 px $2 px"
