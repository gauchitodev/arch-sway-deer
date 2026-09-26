"""Panel Mapa: dónde estás (aproximado, por internet) o, si no se sabe, un lugar del mundo por día.

La laptop no tiene GPS. Una vez por día se pregunta a ip-api.com dónde queda la conexión.
Con datos del celular (hotspot) la respuesta es la ciudad de la antena o de la empresa, no la
tuya, así que en ese caso no se usa: se muestra un pueblito perdido o curioso del mundo.
"""
import json
import random
import threading
import time
import urllib.request
from datetime import date

GEO = "http://ip-api.com/json/?fields=status,country,regionName,city,lat,lon,mobile,proxy,hosting&lang=es"

# nombre, país, lat, lon, dato
LUGARES = [
    ("Hallstatt", "Austria", 47.5622, 13.6493, "Pueblo a orillas de un lago alpino; su mina de sal se trabaja hace unos 7000 años."),
    ("Ittoqqortoormiit", "Groenlandia", 70.4853, -21.9667, "Unos 350 habitantes y hielo marino nueve meses al año: de los pueblos más aislados del mundo."),
    ("Edinburgh of the Seven Seas", "Tristán de Acuña", -37.0675, -12.3105, "El lugar habitado más remoto del planeta: 2400 km hasta la tierra poblada más cercana."),
    ("Longyearbyen", "Svalbard, Noruega", 78.2232, 15.6267, "Acá está la bóveda mundial de semillas, y hace décadas que no se entierra a nadie: el suelo no se descongela."),
    ("Oymyakon", "Rusia", 63.4608, 142.7858, "El pueblo habitado más frío: registró −67,7 °C en 1933."),
    ("Giethoorn", "Países Bajos", 52.7400, 6.0772, "El centro no tiene calles: se anda en bote por los canales."),
    ("Shirakawa-gō", "Japón", 36.2578, 136.9061, "Casas con techos de paja empinados para aguantar la nieve; patrimonio de la UNESCO."),
    ("Supai", "Arizona, EE. UU.", 36.2372, -112.6891, "En el fondo del Gran Cañón: el correo llega en mula."),
    ("Manarola", "Italia", 44.1066, 9.7289, "Casas de colores colgadas sobre el mar, en las Cinque Terre."),
    ("Chefchaouen", "Marruecos", 35.1688, -5.2636, "El pueblo azul de las montañas del Rif."),
    ("Puerto Williams", "Chile", -54.9352, -67.6165, "Sobre el canal Beagle: de los pueblos más australes del mundo."),
    ("Purmamarca", "Jujuy, Argentina", -23.7453, -65.4989, "Al pie del Cerro de los Siete Colores."),
    ("Cabo Polonio", "Rocha, Uruguay", -34.4011, -53.7839, "Sin luz de la red eléctrica, con faro y lobos marinos; se llega en camión por las dunas."),
    ("Colonia del Sacramento", "Uruguay", -34.4717, -57.8442, "Fundada por los portugueses en 1680; su barrio histórico es patrimonio de la UNESCO."),
    ("Villa Epecuén", "Buenos Aires, Argentina", -37.1347, -62.8083, "Quedó bajo el agua del lago en 1985; hoy sus ruinas volvieron a asomar."),
    ("San Pedro de Atacama", "Chile", -22.9087, -68.1997, "Oasis en el desierto no polar más seco del mundo."),
    ("Isla Taquile", "Perú", -15.7725, -69.6856, "En el lago Titicaca; sus tejidos (tejen los hombres) son patrimonio de la UNESCO."),
    ("Adamstown", "Islas Pitcairn", -25.0660, -130.1015, "Unos 40 habitantes, descendientes de los amotinados del Bounty."),
    ("Reine", "Lofoten, Noruega", 67.9326, 13.0887, "Pueblo pesquero entre picos que salen del mar, arriba del círculo polar."),
    ("Bibury", "Inglaterra", 51.7597, -1.8327, "William Morris lo llamó el pueblo más lindo de Inglaterra."),
    ("Gásadalur", "Islas Feroe", 62.1103, -7.4344, "Una cascada cae directo al mar; hasta 2004 se llegaba solo a pie o en helicóptero."),
    ("Monemvasia", "Grecia", 36.6873, 23.0569, "Ciudad amurallada sobre una roca en el mar, con una sola entrada."),
    ("Matmata", "Túnez", 33.5427, 9.9681, "Casas excavadas bajo tierra; una de ellas fue la casa de Luke Skywalker."),
    ("Mawlynnong", "India", 25.2017, 91.9160, "Famoso por ser de los pueblos más limpios de Asia; cerca hay puentes hechos de raíces vivas."),
    ("Ollantaytambo", "Perú", -13.2583, -72.2633, "Sus calles y canales incas se siguen usando hoy."),
    ("Alert", "Nunavut, Canadá", 82.5018, -62.3481, "El lugar habitado todo el año más al norte del mundo, a unos 800 km del Polo."),
    ("Oia", "Santorini, Grecia", 36.4618, 25.3753, "Casas blancas sobre el borde de un volcán hundido en el mar."),
    ("Setenil de las Bodegas", "España", 36.8628, -5.1814, "Hay calles enteras con la roca de techo."),
    ("Rjukan", "Noruega", 59.8787, 8.5935, "Espejos gigantes en la montaña le llevan sol al pueblo en invierno."),
    ("Huacachina", "Perú", -14.0875, -75.7626, "Una laguna rodeada de dunas enormes."),
    ("Coober Pedy", "Australia", -29.0135, 134.7544, "Capital del ópalo: mucha gente vive bajo tierra para escapar del calor."),
    ("Hum", "Croacia", 45.3486, 14.0486, "Se presenta como la ciudad más chica del mundo: unos 20 habitantes."),
    ("Gruyères", "Suiza", 46.5840, 7.0826, "Pueblo medieval con castillo; le da nombre al queso."),
    ("Cachi", "Salta, Argentina", -25.1203, -66.1627, "Pueblo blanco en los Valles Calchaquíes, a 2280 m."),
    ("Iruya", "Salta, Argentina", -22.7917, -65.2139, "Colgado de la montaña a 2780 m, al final de un camino de cornisa."),
    ("Hanga Roa", "Isla de Pascua, Chile", -27.1500, -109.4333, "El único pueblo de la isla de los moáis."),
    ("Utqiagvik", "Alaska, EE. UU.", 71.2906, -156.7887, "Cada invierno pasa unos 65 días sin ver salir el sol."),
]
_ORDEN = list(range(len(LUGARES)))
random.Random(5).shuffle(_ORDEN)   # siempre el mismo orden, así cada día tiene su lugar


def lugar_del_dia(salto=0):
    n = (date.today().toordinal() + salto) % len(LUGARES)
    nombre, pais, lat, lon, dato = LUGARES[_ORDEN[n]]
    return {"fuente": "lugar", "nombre": nombre, "pais": pais, "lat": lat, "lon": lon, "dato": dato}


class Mapa:
    """Guarda en estado.json (que no va al repo) lo último que averiguó y el modo elegido."""

    def __init__(self, leer_estado, guardar_estado, demo=False):
        self.leer, self.guardar = leer_estado, guardar_estado
        self.demo = demo
        self.buscando = False
        self._candado = threading.Lock()

    def _buscar(self):
        res = {"fecha": date.today().isoformat(), "ok": False, "t": int(time.time())}
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(GEO, headers={"User-Agent": "g5"}), timeout=10))
            if d.get("status") == "success":
                lat, lon = float(d["lat"]), float(d["lon"])
                res["movil"] = bool(d.get("mobile") or d.get("proxy") or d.get("hosting"))
                if not res["movil"] and -90 <= lat <= 90 and -180 <= lon <= 180:
                    partes = [str(d.get(k) or "")[:40] for k in ("city", "regionName")]
                    res.update(ok=True, lat=round(lat, 4), lon=round(lon, 4),
                               nombre=", ".join(dict.fromkeys(p for p in partes if p)) or "Tu zona",
                               pais=str(d.get("country") or "")[:40])
        except (OSError, ValueError, KeyError, TypeError):
            res["error"] = True
        self.guardar({"mapa_auto": res})
        self.buscando = False

    def ver(self, buscar=False):
        e = self.leer()
        salto = e.get("mapa_salto") if isinstance(e.get("mapa_salto"), dict) else {}
        salto = salto.get("n", 0) if salto.get("fecha") == date.today().isoformat() else 0
        if e.get("mapa_modo") == "fijo" and isinstance(e.get("mapa"), str) and e["mapa"]:
            return {"modo": "fijo", "fuente": "fijo", "nombre": e["mapa"][:80]}
        if self.demo:
            return dict(lugar_del_dia(salto), modo="auto", buscando=False)
        auto = e.get("mapa_auto") if isinstance(e.get("mapa_auto"), dict) else {}
        with self._candado:
            if (buscar or auto.get("fecha") != date.today().isoformat()) and not self.buscando:
                self.buscando = True
                threading.Thread(target=self._buscar, daemon=True).start()
        if auto.get("ok") and auto.get("fecha") == date.today().isoformat() and not salto:
            r = {"fuente": "ip", "nombre": auto["nombre"], "pais": auto.get("pais", ""),
                 "lat": auto["lat"], "lon": auto["lon"]}
        else:
            r = lugar_del_dia(salto)
            r["motivo"] = "otro" if salto else "movil" if auto.get("movil") else "error" if auto.get("error") else "buscando"
        return dict(r, modo="auto", buscando=self.buscando, revisado=auto.get("t"))

    def accion(self, que, lugar=None):
        hoy = date.today().isoformat()
        if que == "buscar":
            self.guardar({"mapa_modo": "auto", "mapa_salto": {"fecha": hoy, "n": 0}})
            self.ver(buscar=True)
            return True
        if que == "otro":
            e = self.leer()
            s = e.get("mapa_salto") if isinstance(e.get("mapa_salto"), dict) else {}
            n = s.get("n", 0) if s.get("fecha") == hoy and isinstance(s.get("n"), int) else 0
            self.guardar({"mapa_modo": "auto", "mapa_salto": {"fecha": hoy, "n": (n + 1) % len(LUGARES)}})
            return True
        if que == "auto":
            self.guardar({"mapa_modo": "auto"})
            return True
        if que == "fijo" and isinstance(lugar, str) and 0 < len(lugar.strip()) <= 80:
            self.guardar({"mapa_modo": "fijo", "mapa": lugar.strip()})
            return True
        return False
