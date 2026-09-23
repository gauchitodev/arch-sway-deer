#!/usr/bin/env python3
"""Carga del internet para Waybar, como la carga del motor de la cosechadora.

Waybar lo llama cada segundo (módulo "image"). Cada vez mide cuántos bytes
pasaron por la placa de red desde la llamada anterior, dibuja una rampa
triangular que se llena de izquierda a derecha (verde, amarilla, roja) y
devuelve la ruta del dibujo y el texto de ayuda.

El 100 % es la mayor velocidad vista hace poco (se va olvidando de a poco),
así se adapta al hotspot o a un wifi rápido.
"""
import json
import os
import time

MINIMO = 1_000_000 / 8      # 1 Mbps: menos que esto no cuenta como "tope"
OLVIDO = 0.995              # el pico baja ~0.5 % por segundo
CARPETA = os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/g5-{os.getuid()}"
ESTADO = os.path.join(CARPETA, "g5-carga-red.json")
DIBUJO = os.path.join(CARPETA, "g5-carga-red.svg")

# Colores (los mismos de la barra): vacío, verde, amarillo, rojo, texto
VACIO, VERDE, AMARILLO, ROJO, TEXTO = "#2c6b5d", "#5ea23a", "#ffde00", "#e0453c", "#d8ecd0"
# Rampa 5:1, más el número a la derecha
W, H, ANCHO = 75, 15, 112


def interfaz():
    """La placa por donde sale internet (la de la ruta por defecto)."""
    try:
        with open("/proc/net/route") as f:
            for linea in f.readlines()[1:]:
                campos = linea.split()
                if len(campos) > 1 and campos[1] == "00000000":
                    return campos[0]
    except OSError:
        pass
    return None


def leer(nombre, cual):
    try:
        with open(f"/sys/class/net/{nombre}/statistics/{cual}_bytes") as f:
            return int(f.read())
    except (OSError, ValueError):
        return None


def mbps(bytes_seg):
    return f"{bytes_seg * 8 / 1e6:.1f} Mbps"


def rampa(pct):
    """SVG: triángulo con la base abajo y la punta alta a la derecha."""
    y0 = 2
    tri = f"0,{y0 + H} {W},{y0 + H} {W},{y0}"
    lleno = W * pct / 100
    zonas = (
        f'<rect x="0" y="0" width="{W * .6:.1f}" height="{H + 4}" fill="{VERDE}"/>'
        f'<rect x="{W * .6:.1f}" y="0" width="{W * .25:.1f}" height="{H + 4}" fill="{AMARILLO}"/>'
        f'<rect x="{W * .85:.1f}" y="0" width="{W * .15 + 1:.1f}" height="{H + 4}" fill="{ROJO}"/>'
    )
    color_num = ROJO if pct > 85 else AMARILLO if pct > 60 else TEXTO
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{H + 4}" viewBox="0 0 {ANCHO} {H + 4}">'
        f'<defs><clipPath id="t"><polygon points="{tri}"/></clipPath>'
        f'<clipPath id="l"><rect x="0" y="0" width="{lleno:.1f}" height="{H + 4}"/></clipPath></defs>'
        f'<polygon points="{tri}" fill="{VACIO}"/>'
        f'<g clip-path="url(#t)"><g clip-path="url(#l)">{zonas}</g></g>'
        f'<text x="{ANCHO}" y="{y0 + H}" text-anchor="end" font-family="sans-serif" font-weight="bold" '
        f'font-size="14" fill="{color_num}">{pct}%</text></svg>'
    )


def main():
    os.makedirs(CARPETA, mode=0o700, exist_ok=True)
    try:
        with open(ESTADO) as f:
            antes = json.load(f)
    except (OSError, ValueError):
        antes = {}
    nombre = interfaz()
    rx = leer(nombre, "rx") if nombre else None
    tx = leer(nombre, "tx") if nombre else None
    ahora = time.time()
    pico = max(MINIMO, float(antes.get("pico", MINIMO)))
    baja = sube = 0.0
    if rx is not None and tx is not None and antes.get("red") == nombre:
        dt = ahora - float(antes.get("t", 0))
        if 0.2 < dt < 30:
            baja = max(0, rx - int(antes.get("rx", rx))) / dt
            sube = max(0, tx - int(antes.get("tx", tx))) / dt
    total = baja + sube
    pico = max(MINIMO, total, pico * OLVIDO)
    pct = min(100, round(100 * total / pico)) if rx is not None else 0

    tmp = ESTADO + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"red": nombre, "rx": rx, "tx": tx, "t": ahora, "pico": pico}, f)
    os.replace(tmp, ESTADO)
    tmp = DIBUJO + ".tmp"
    with open(tmp, "w") as f:
        f.write(rampa(pct))
    os.replace(tmp, DIBUJO)

    if rx is None:
        ayuda = "Sin conexión"
    else:
        ayuda = f"Carga del internet: {pct} %   ↓ {mbps(baja)} · ↑ {mbps(sube)}   Tope reciente: {mbps(pico)}"
    # Waybar: primera línea = dibujo, segunda = texto de ayuda
    print(DIBUJO)
    print(ayuda)


if __name__ == "__main__":
    main()
