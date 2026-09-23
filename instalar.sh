#!/bin/sh
# Instala la capa G5 encima de una config de Sway con Waybar (pensada para sway-workstation).
# Se puede correr las veces que quieras: no duplica nada.
set -e
G5="$HOME/.config/g5"
if [ "$(cd "$(dirname "$0")" && pwd -P)" != "$(cd "$G5" 2>/dev/null && pwd -P)" ]; then
    echo "Este repo tiene que estar en ~/.config/g5 (git clone ... ~/.config/g5)"; exit 1
fi

faltan=""
for p in sway waybar wofi mako swaylock chromium python3 jq playerctl pamixer brightnessctl grim wl-copy foot gtk-launch; do
    command -v "$p" >/dev/null 2>&1 || faltan="$faltan $p"
done
[ -n "$faltan" ] && echo "Ojo, faltan estos programas:$faltan"

mkdir -p "$G5/local"

# Lo que necesita rutas completas se genera acá, porque depende de cada usuario
cat > "$G5/local/barra.conf" <<FIN
bar bar-0 {
    swaybar_command $G5/waybar/lanzar.sh
}
FIN
sed "s|@G5@|$G5|" "$G5/swaylock/config.in" > "$G5/local/swaylock"
[ -f "$G5/local/config.json" ] || cp "$G5/config.ejemplo.json" "$G5/local/config.json"

# Enlaces; si ya había un archivo propio, lo guarda con el nombre .antes-g5
enlazar() {
    mkdir -p "$(dirname "$1")"
    if [ -e "$1" ] && [ ! -L "$1" ]; then mv "$1" "$1.antes-g5"; fi
    ln -sfn "$2" "$1"
}
enlazar "$HOME/.config/wofi/style.css" "$G5/wofi/style.css"
enlazar "$HOME/.config/mako/config" "$G5/mako/config"
enlazar "$HOME/.config/swaylock/config" "$G5/local/swaylock"
enlazar "$HOME/.config/gtk-3.0/gtk.css" "$G5/gtk/gtk3.css"
enlazar "$HOME/.config/gtk-4.0/gtk.css" "$G5/gtk/gtk4.css"

chmod +x "$G5/home/"*.sh "$G5/home/server.py" "$G5/waybar/lanzar.sh"

# Una sola línea al final de la config de Sway
SWAY="$HOME/.config/sway/config"
if ! grep -q 'include ~/.config/g5/sway.conf' "$SWAY" 2>/dev/null; then
    printf '\n# Capa G5 (estilo pantalla de cosechadora)\ninclude ~/.config/g5/sway.conf\n' >> "$SWAY"
fi

# El servicio que abre los selectores de archivos toma el estilo nuevo al reiniciarse
systemctl --user try-restart xdg-desktop-portal-gtk 2>/dev/null || true

if [ -n "$SWAYSOCK" ]; then swaymsg reload >/dev/null && echo "Listo. Probá Super+G."; else echo "Listo. Entrá a Sway y probá Super+G."; fi
