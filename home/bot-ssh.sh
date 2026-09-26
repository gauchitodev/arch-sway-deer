#!/bin/sh
# Entra por SSH al equipo del bot (local/config.json → "bot"), siempre con la IP al día:
# si el celular cambió de red, la pantalla de inicio lo encuentra y actualiza la config.
#   bot-ssh.sh                → te deja adentro
#   bot-ssh.sh amfbot estado  → corre ese comando allá y vuelve
CONFIG="$HOME/.config/g5/local/config.json"
set -- "$(python3 -c '
import json, sys
b = json.load(open(sys.argv[1])).get("bot") or {}
print(b.get("destino", ""), b.get("puerto", 22))' "$CONFIG" 2>/dev/null)" "$@"
destino=${1% *}; puerto=${1##* }; shift
if [ -z "$destino" ]; then
    echo "No hay bot configurado en $CONFIG"
    exit 1
fi
# La huella guardada con nombre fijo (la agrega server.py): así no pregunta de nuevo cada vez que cambia la IP
if ssh-keygen -F g5-bot >/dev/null 2>&1; then
    set -- -o HostKeyAlias=g5-bot -o StrictHostKeyChecking=yes "$destino" "$@"
else
    set -- "$destino" "$@"
fi
ssh -p "$puerto" "$@"
codigo=$?
if [ "$codigo" = 255 ]; then
    echo
    echo "No pude entrar a ${destino#*@}. Abrí la pantalla de inicio (Super+G), tocá el panel del bot"
    echo "y después \"Buscar en la red\". Cuando lo encuentre, probá de nuevo."
    # Abierto desde el menú: que no se cierre la ventana antes de leer el aviso
    printf "Enter para cerrar… "; read -r _
fi
exit "$codigo"
