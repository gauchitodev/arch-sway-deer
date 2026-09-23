#!/usr/bin/env python3
"""Carga del internet para Waybar, como la carga del motor en la G5.

Mide cuántos bytes pasan por la placa de red cada segundo y lo muestra
como una barrita: verde con poca carga, amarilla media, roja cuando la
conexión está al tope. El 100 % es la mayor velocidad vista hace poco
(se va olvidando de a poco), así se adapta al hotspot o a un wifi rápido.
"""
import json
import os
import sys
import time

SEGMENTOS = 8
MINIMO = 1_000_000 / 8      # 1 Mbps: menos que esto no cuenta como "tope"
OLVIDO = 0.995              # el pico baja ~0.5 % por segundo


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


def barra(pct):
    llenos = round(pct / 100 * SEGMENTOS)
    partes = []
    for i in range(SEGMENTOS):
        if i >= llenos:
            partes.append("<span color='#2c6b5d'>▮</span>")
            continue
        tramo = (i + 1) / SEGMENTOS
        color = "#5ea23a" if tramo <= 0.6 else "#ffde00" if tramo <= 0.85 else "#e0453c"
        partes.append(f"<span color='{color}'>▮</span>")
    return "".join(partes)


def main():
    pico = MINIMO
    antes = None
    while True:
        nombre = interfaz()
        rx = leer(nombre, "rx") if nombre else None
        tx = leer(nombre, "tx") if nombre else None
        ahora = time.monotonic()
        if rx is None or tx is None:
            salida = {"text": "", "class": "sin-red", "tooltip": "Sin conexión"}
            antes = None
        else:
            baja = sube = 0.0
            if antes and antes[0] == nombre and ahora > antes[3]:
                dt = ahora - antes[3]
                baja = max(0, rx - antes[1]) / dt
                sube = max(0, tx - antes[2]) / dt
            antes = (nombre, rx, tx, ahora)
            total = baja + sube
            pico = max(MINIMO, total, pico * OLVIDO)
            pct = min(100, round(100 * total / pico))
            clase = "alta" if pct > 85 else "media" if pct > 60 else "baja"
            salida = {
                "text": f"<span size='small' color='#9fc9bc'>CARGA</span> {barra(pct)}",
                "tooltip": f"Carga del internet: {pct} %\n↓ {mbps(baja)} · ↑ {mbps(sube)}\n"
                           f"Tope reciente: {mbps(pico)} ({nombre})",
                "class": clase,
                "percentage": pct,
            }
        try:
            print(json.dumps(salida), flush=True)
        except BrokenPipeError:
            # Waybar se cerró: terminamos sin ruido
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
            return
        time.sleep(1)


if __name__ == "__main__":
    main()
