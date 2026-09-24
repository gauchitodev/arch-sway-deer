#!/bin/sh
# Mantiene el escritorio "Inicio" solo para la pantalla de inicio.
# Si abrís otra ventana estando ahí (terminal, menú, lo que sea), la manda
# al escritorio de donde veniste y te lleva con ella, así la pantalla de
# inicio nunca se achica.
ESCRITORIO="Inicio"

# Uno solo por sesión (exec_always lo vuelve a lanzar en cada recarga)
for viejo in $(pgrep -u "$(id -u)" -f "^sh $HOME/.config/g5/home/vigilar.sh"); do
    [ "$viejo" != "$$" ] && kill "$viejo" 2>/dev/null
done

mover() {
    # Al escritorio anterior; si no hay anterior (recién prendida), al 1
    swaymsg "[con_id=$1] move container to workspace back_and_forth" >/dev/null 2>&1 \
        || swaymsg "[con_id=$1] move container to workspace number 1" >/dev/null
    swaymsg "[con_id=$1] focus" >/dev/null
}

swaymsg -t subscribe -m '["window"]' | while read -r evento; do
    id=$(printf '%s' "$evento" | jq -r '
        select(.change == "new")
        | .container
        | select(.type == "con")
        | select(((.app_id // "") | startswith("chrome-127.0.0.1")) | not)
        | .id')
    [ -n "$id" ] || continue
    donde=$(swaymsg -t get_tree | jq -r --argjson id "$id" '
        .. | objects | select(.type == "workspace")
        | select([.. | objects | .id] | index($id)) | .name' | head -n1)
    [ "$donde" = "$ESCRITORIO" ] && mover "$id"
done
