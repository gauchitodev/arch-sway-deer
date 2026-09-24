#!/usr/bin/env python3
"""Carga del internet para Waybar, como la carga del motor de la cosechadora.

Queda andando en segundo plano (lo arranca lanzar.sh junto con la barra).
Una vez por segundo mide cuántos bytes pasaron por la placa de red, y la
rampa se va acercando de a poco a ese valor, como una aguja con inercia:
no salta de golpe. Cada vez que el dibujo cambia, escribe el SVG y le avisa
a Waybar con una señal para que lo vuelva a mostrar. Si nada cambia, no
dibuja ni avisa.

El 100 % es la mayor velocidad vista hace poco (se va olvidando de a poco),
así se adapta al hotspot o a un wifi rápido.
"""
import os
import signal
import time

MINIMO = 1_000_000 / 8      # 1 Mbps: menos que esto no cuenta como "tope"
OLVIDO = 0.995              # el pico baja ~0.5 % por segundo
CUADRO = 0.1                # 10 cuadros por segundo mientras se mueve
SUAVE = 0.18                # cuánto se acerca al valor nuevo en cada cuadro
SENAL = 9                   # Waybar: "signal": 9 → SIGRTMIN+9
CARPETA = os.environ.get("XDG_RUNTIME_DIR") or f"/tmp/g5-{os.getuid()}"
DIBUJO = os.path.join(CARPETA, "g5-carga-red.svg")
SALIDA = os.path.join(CARPETA, "g5-carga-red.txt")   # lo que lee Waybar: ruta + ayuda

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
    """SVG: triángulo con la base abajo y la punta alta a la derecha, lleno hasta pct."""
    y0 = 2
    tri = f"0,{y0 + H} {W},{y0 + H} {W},{y0}"
    lleno = W * pct / 100
    zonas = (
        f'<rect x="0" y="0" width="{W * .6:.1f}" height="{H + 4}" fill="{VERDE}"/>'
        f'<rect x="{W * .6:.1f}" y="0" width="{W * .25:.1f}" height="{H + 4}" fill="{AMARILLO}"/>'
        f'<rect x="{W * .85:.1f}" y="0" width="{W * .15 + 1:.1f}" height="{H + 4}" fill="{ROJO}"/>'
    )
    numero = round(pct)
    color_num = ROJO if numero > 85 else AMARILLO if numero > 60 else TEXTO
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{H + 4}" viewBox="0 0 {ANCHO} {H + 4}">'
        f'<defs><clipPath id="t"><polygon points="{tri}"/></clipPath>'
        f'<clipPath id="l"><rect x="0" y="0" width="{lleno:.1f}" height="{H + 4}"/></clipPath></defs>'
        f'<polygon points="{tri}" fill="{VACIO}"/>'
        f'<g clip-path="url(#t)"><g clip-path="url(#l)">{zonas}</g></g>'
        f'<text x="{ANCHO}" y="{y0 + H}" text-anchor="end" font-family="sans-serif" font-weight="bold" '
        f'font-size="14" fill="{color_num}">{numero}%</text></svg>'
    )


def escribir(ruta, texto):
    tmp = ruta + ".tmp"
    with open(tmp, "w") as f:
        f.write(texto)
    os.replace(tmp, ruta)


def edad(pid):
    """Segundos que lleva andando un proceso."""
    with open(f"/proc/{pid}/stat") as f:
        inicio = int(f.read().rsplit(")", 1)[1].split()[19])   # campo 22: starttime
    with open("/proc/uptime") as f:
        return float(f.read().split()[0]) - inicio / os.sysconf("SC_CLK_TCK")


def avisar_waybar():
    """Manda SIGRTMIN+9 a las barras Waybar de este usuario.

    Solo a las que llevan unos segundos andando: si la señal llega antes de que
    Waybar prepare su manejador, la acción por defecto la cierra."""
    yo = os.getuid()
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() != "waybar":
                    continue
            if os.stat(f"/proc/{pid}").st_uid == yo and edad(pid) > 3:
                os.kill(int(pid), signal.SIGRTMIN + SENAL)
        except (OSError, ValueError, IndexError):
            pass


def main():
    os.makedirs(CARPETA, mode=0o700, exist_ok=True)
    pico = MINIMO
    antes = None               # (placa, rx, tx, momento) de la última medición
    meta = mostrado = 0.0      # valor medido y valor que se ve (el que se acerca de a poco)
    dibujado = None            # (lleno, número) del último dibujo
    ayuda = ayuda_escrita = ""
    proxima = 0.0
    while True:
        ahora = time.monotonic()
        if ahora >= proxima:
            proxima = ahora + 1
            nombre = interfaz()
            rx = leer(nombre, "rx") if nombre else None
            tx = leer(nombre, "tx") if nombre else None
            if rx is None or tx is None:
                meta, antes, ayuda = 0.0, None, "Sin conexión"
            else:
                baja = sube = 0.0
                if antes and antes[0] == nombre and ahora > antes[3]:
                    dt = ahora - antes[3]
                    baja = max(0, rx - antes[1]) / dt
                    sube = max(0, tx - antes[2]) / dt
                antes = (nombre, rx, tx, ahora)
                total = baja + sube
                pico = max(MINIMO, total, pico * OLVIDO)
                meta = min(100.0, 100 * total / pico)
                ayuda = (f"Carga del internet: {round(meta)} %   ↓ {mbps(baja)} · ↑ {mbps(sube)}   "
                         f"Tope reciente: {mbps(pico)}")

        # La aguja se acerca de a poco; cerca del valor, se queda quieta
        mostrado += (meta - mostrado) * SUAVE
        if abs(meta - mostrado) < 0.3:
            mostrado = meta
        cuadro = (round(mostrado * 2) / 2, round(mostrado))
        if cuadro != dibujado or ayuda != ayuda_escrita:
            escribir(DIBUJO, rampa(cuadro[0]))
            escribir(SALIDA, f"{DIBUJO}\n{ayuda}\n")
            dibujado, ayuda_escrita = cuadro, ayuda
            avisar_waybar()
        time.sleep(CUADRO)


if __name__ == "__main__":
    main()
