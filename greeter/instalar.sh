#!/bin/sh
# Instala la pantalla de login (tema para lightdm-webkit2-greeter).
# Uso: sudo ~/.config/g5/greeter/instalar.sh
# Para volver al login de antes: sudo rm /etc/lightdm/lightdm.conf.d/50-arch-sway-deer.conf
set -e
[ "$(id -u)" = 0 ] || { echo "Correlo con sudo: sudo $0"; exit 1; }
AQUI="$(cd "$(dirname "$0")" && pwd -P)"
G5="$(dirname "$AQUI")"
TEMA=/usr/share/lightdm-webkit/themes/arch-sway-deer
CONF=/etc/lightdm/lightdm-webkit2-greeter.conf

[ -f /usr/share/xgreeters/lightdm-webkit2-greeter.desktop ] || {
    echo "Falta el programa. Instalalo con: sudo pacman -S lightdm-webkit2-greeter"; exit 1; }

# 1. Copiar el tema (el greeter corre como el usuario "lightdm" y no puede leer tu carpeta personal)
rm -rf "$TEMA"
install -d -m 755 "$TEMA"
install -m 644 "$AQUI/index.html" "$TEMA/index.html"
install -m 644 "$G5/bloqueo.jpg" "$AQUI/ejemplo/montanas.png" "$TEMA/"
if [ -f "$G5/local/greeter/usuarios.js" ]; then
    for f in "$G5/local/greeter/"*; do
        # Solo archivos comunes: nunca seguir enlaces (podrían apuntar a archivos del sistema)
        [ -f "$f" ] && [ ! -L "$f" ] || continue
        case "$f" in *.js|*.jpg|*.jpeg|*.png|*.webp) install -m 644 "$f" "$TEMA/";; esac
    done
else
    install -m 644 "$AQUI/usuarios.ejemplo.js" "$TEMA/usuarios.js"
fi

# 2. Elegir este tema (guardando una copia de la config original la primera vez)
[ -f "$CONF.antes-g5" ] || cp "$CONF" "$CONF.antes-g5"
sed -i -E 's/^[[:space:]]*webkit_theme[[:space:]]*=.*/webkit_theme        = arch-sway-deer/' "$CONF"
sed -i -E 's/^[[:space:]]*secure_mode[[:space:]]*=.*/secure_mode         = true/' "$CONF"
sed -i -E 's/^[[:space:]]*debug_mode[[:space:]]*=.*/debug_mode          = false/' "$CONF"

# 3. Decirle a LightDM que use este greeter (un archivo aparte, fácil de borrar)
install -d -m 755 /etc/lightdm/lightdm.conf.d
printf '[Seat:*]\ngreeter-session=lightdm-webkit2-greeter\n' > /etc/lightdm/lightdm.conf.d/50-arch-sway-deer.conf

echo "Listo. Se ve la próxima vez que cierres sesión o reinicies."
echo "Si algo falla: Ctrl+Alt+F2, entrá con tu usuario y corré"
echo "  sudo rm /etc/lightdm/lightdm.conf.d/50-arch-sway-deer.conf && sudo systemctl restart lightdm"
