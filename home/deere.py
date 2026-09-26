"""Mini Operations Center y mini Files: datos de John Deere por la API oficial. SOLO LECTURA.

- Las claves de la app van en local/deere.json y el permiso en local/deere-token.json
  (los dos fuera del repo). Este archivo nunca imprime ninguno de los dos.
- Números de serie, de motor y PIN se descartan apenas llegan; si una máquina tiene el PIN
  como nombre, se tapa.
- Licencia de desarrollo de Deere: lo que llega se usa y se olvida. Solo queda en memoria
  unos minutos, para no gastar datos pidiendo lo mismo dos veces. Nada se guarda en disco.
"""
import base64
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

LOGIN = "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token"
EQUIPOS = "https://equipmentapi.deere.com/isg/equipment"
PERMISOS = "openid profile offline_access org1 ag1 ag2 eq1 files work1 work2"
ACEPTA = "application/vnd.deere.axiom.v3+json"
CACHE_S = 180            # cuánto dura una respuesta en memoria
REFRESCO_S = 600         # cada cuánto se vuelve a pedir la flota entera
DIAS_ALERTAS = 7


class Deere:
    def __init__(self, local, config, demo=False):
        self.claves = os.path.join(local, "deere.json")
        self.token_arch = os.path.join(local, "deere-token.json")
        config = config if isinstance(config, dict) else {}
        self.api = config.get("api") if re.fullmatch(r"https://[a-z0-9.-]+\.deere\.com/platform",
                                                      str(config.get("api", ""))) else "https://sandboxapi.deere.com/platform"
        self.org = str(config.get("org", "")) if re.fullmatch(r"\d{1,12}", str(config.get("org", ""))) else ""
        self.demo = demo
        self._cache = {}
        self._candado_token = threading.Lock()
        self._candado = threading.Lock()
        self.flota = {"t": 0, "org": None, "maquinas": [], "error": None, "cargando": False}
        self.archivos = {"t": 0, "org": None, "lista": [], "error": None, "cargando": False}
        self.orgs = {"t": 0, "lista": []}

    # ---------- Permiso ----------

    def configurado(self):
        return self.demo or (os.path.exists(self.claves) and os.path.exists(self.token_arch) and bool(self.org))

    def _token(self):
        with self._candado_token:
            with open(self.token_arch) as f:
                t = json.load(f)
            if time.time() * 1000 < t.get("vence", 0):
                return t["access_token"]
            if not t.get("refresh_token"):
                raise PermisoVencido()
            with open(self.claves) as f:
                c = json.load(f)
            basica = base64.b64encode(f'{c["client_id"]}:{c["client_secret"]}'.encode()).decode()
            pedido = urllib.request.Request(LOGIN, data=urllib.parse.urlencode({
                "grant_type": "refresh_token", "refresh_token": t["refresh_token"], "scope": PERMISOS}).encode(),
                headers={"Authorization": "Basic " + basica, "Accept": "application/json",
                         "Content-Type": "application/x-www-form-urlencoded"})
            try:
                nuevo = json.load(urllib.request.urlopen(pedido, timeout=30))
            except urllib.error.HTTPError as e:
                if e.code in (400, 401):
                    raise PermisoVencido()
                raise
            nuevo["vence"] = int((time.time() + nuevo.get("expires_in", 3600) - 60) * 1000)
            if not nuevo.get("refresh_token"):
                nuevo["refresh_token"] = t["refresh_token"]
            tmp = self.token_arch + ".tmp"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                json.dump(nuevo, f)
            os.replace(tmp, self.token_arch)
            return nuevo["access_token"]

    def _get(self, url, ttl=CACHE_S):
        """Solo GET: este módulo no cambia nada en Deere."""
        guardado = self._cache.get(url)
        if guardado and time.time() - guardado[0] < ttl:
            return guardado[1]
        pedido = urllib.request.Request(url, headers={"Authorization": "Bearer " + self._token(), "Accept": ACEPTA})
        datos = json.load(urllib.request.urlopen(pedido, timeout=30))
        self._cache[url] = (time.time(), datos)
        if len(self._cache) > 300:
            self._cache.pop(next(iter(self._cache)))
        return datos

    def _todo(self, url, tope=10):
        """Deere manda las listas de a pedazos, con un link "nextPage"."""
        items, d = [], self._get(url)
        for _ in range(tope):
            items += d.get("values") or []
            sig = next((l.get("uri") for l in d.get("links") or [] if l.get("rel") == "nextPage"), None)
            # El permiso viaja en cada pedido: solo se siguen links a Deere
            if not sig or not re.fullmatch(r"https://[a-z0-9.-]+\.deere\.com/\S*", str(sig)):
                break
            d = self._get(sig)
        return items

    def _ultimo(self, url):
        try:
            return (self._get(url).get("values") or [None])[0]
        except Exception:
            return None

    # ---------- Organizaciones ----------

    def lista_orgs(self):
        if self.demo:
            return [{"id": "1", "nombre": "Estancia de ejemplo"}, {"id": "2", "nombre": "Pruebas"}]
        if time.time() - self.orgs["t"] > 3600:
            try:
                vals = self._todo(self.api + "/organizations", 5)
                self.orgs.update(t=time.time(), lista=[{"id": str(o["id"]), "nombre": str(o.get("name", o["id"]))[:60]}
                                                       for o in vals if re.fullmatch(r"\d{1,12}", str(o.get("id", "")))])
            except Exception:
                pass
        return self.orgs["lista"]

    def cambiar_org(self, org):
        if not any(o["id"] == org for o in self.lista_orgs()):
            return False
        self.org = org
        self.flota.update(t=0)
        self.archivos.update(t=0)
        return True

    # ---------- Flota (mini Operations Center) ----------

    def _maquina(self, e):
        pid = str(e.get("principalId") or "")
        m = {"id": str(e.get("id")), "nombre": tapar(e.get("name")) or "(sin nombre)",
             "tipo": _nombre(e.get("type")), "marca": _nombre(e.get("make")),
             "modelo": tapar(_nombre(e.get("model"))), "anio": _entero(e.get("modelYear"), "") or "",
             "telemetria": bool(e.get("telematicsCapable") and pid),
             "lugar": None, "horas": None, "alertas": []}
        if not m["telemetria"]:
            return m
        base = f"{self.api}/machines/{urllib.parse.quote(pid)}"
        v = self._ultimo(base + "/locationHistory?lastKnown=true")
        if v and isinstance(v.get("point"), dict):
            try:
                m["lugar"] = {"lat": round(float(v["point"]["lat"]), 6), "lon": round(float(v["point"]["lon"]), 6),
                              "cuando": _ms(v.get("eventTimestamp"))}
            except (TypeError, ValueError, KeyError):
                pass
        v = self._ultimo(base + "/engineHours?lastKnown=true")
        if v and isinstance(v.get("reading"), dict):
            try:
                m["horas"] = {"horas": round(float(v["reading"]["valueAsDouble"]), 1), "cuando": _ms(v.get("reportTime"))}
            except (TypeError, ValueError, KeyError):
                pass
        try:
            desde = (time.time() - DIAS_ALERTAS * 86400) * 1000
            for a in self._todo(base + "/alerts", 3):
                cuando = _ms(a.get("time"))
                if a.get("ignored") or a.get("invisible") or not cuando or cuando < desde:
                    continue
                d = a.get("definition") or {}
                spn, fmi = d.get("suspectParameterName"), d.get("failureModeIndicator")
                m["alertas"].append({"cuando": cuando, "codigo": f"{spn}.{fmi}" if spn is not None and fmi is not None else "",
                                     "modulo": str(d.get("threeLetterAcronym") or "")[:8],
                                     "descripcion": tapar(d.get("description"))[:160],
                                     "color": str(a.get("color") or "").upper()[:10], "veces": _entero(a.get("occurrences"), 1)})
            m["alertas"].sort(key=lambda x: -x["cuando"])
            m["alertas"] = m["alertas"][:20]
        except Exception:
            pass
        return m

    def _cargar_flota(self, org):
        try:
            lista = [e for e in self._todo(f"{EQUIPOS}?organizationIds={urllib.parse.quote(org)}", 20) if not e.get("archived")]
            with ThreadPoolExecutor(5) as pool:   # de a pocas: la laptop anda con el hotspot
                maquinas = list(pool.map(self._maquina, lista))
            maquinas.sort(key=lambda m: (not m["telemetria"], -((m["lugar"] or {}).get("cuando") or 0), m["nombre"].lower()))
            self.flota.update(t=time.time(), org=org, maquinas=maquinas, error=None)
        except PermisoVencido:
            self.flota.update(t=time.time(), error="permiso")
        except Exception:
            self.flota.update(t=time.time(), error="red")
        finally:
            self.flota["cargando"] = False

    def ver_flota(self, forzar=False):
        if self.demo:
            return {"org": "1", "maquinas": DEMO_FLOTA(), "error": None, "cargando": False, "t": time.time()}
        with self._candado:
            viejo = self.flota["org"] != self.org or time.time() - self.flota["t"] > REFRESCO_S
            if (viejo or forzar) and not self.flota["cargando"] and self.org:
                self.flota["cargando"] = True
                threading.Thread(target=self._cargar_flota, args=(self.org,), daemon=True).start()
        f = self.flota
        return {"org": self.org, "maquinas": f["maquinas"] if f["org"] == self.org else [],
                "error": f["error"], "cargando": f["cargando"], "t": f["t"]}

    def maquina(self, ident):
        """Una máquina de la última lista (no se le cree nada a la página, se busca acá)."""
        lista = DEMO_FLOTA() if self.demo else self.flota["maquinas"]
        return next((m for m in lista if m["id"] == ident), None)

    # ---------- Archivos (mini Files) ----------

    def _cargar_archivos(self, org):
        try:
            vals = self._todo(f"{self.api}/organizations/{urllib.parse.quote(org)}/files", 10)
            lista = []
            for a in vals:
                fecha = _ms(a.get("modifiedTime")) or _ms(a.get("createdTime"))
                tam = _entero(a.get("nativeSize"))
                lista.append({"id": str(a.get("id", ""))[:40], "nombre": tapar(a.get("name"))[:120] or "(sin nombre)",
                              "tipo": str(a.get("type") or "")[:30], "fecha": fecha, "tam": tam,
                              "pendiente": bool(a.get("transferPending"))})
            lista.sort(key=lambda a: -(a["fecha"] or 0))
            self.archivos.update(t=time.time(), org=org, lista=lista[:60], error=None)
        except PermisoVencido:
            self.archivos.update(t=time.time(), error="permiso")
        except urllib.error.HTTPError as e:
            self.archivos.update(t=time.time(), error="prohibido" if e.code == 403 else "red")
        except Exception:
            self.archivos.update(t=time.time(), error="red")
        finally:
            self.archivos["cargando"] = False

    def ver_archivos(self, forzar=False):
        if self.demo:
            return {"org": "1", "lista": DEMO_ARCHIVOS(), "error": None, "cargando": False, "t": time.time()}
        with self._candado:
            viejo = self.archivos["org"] != self.org or time.time() - self.archivos["t"] > REFRESCO_S
            if (viejo or forzar) and not self.archivos["cargando"] and self.org:
                self.archivos["cargando"] = True
                threading.Thread(target=self._cargar_archivos, args=(self.org,), daemon=True).start()
        a = self.archivos
        return {"org": self.org, "lista": a["lista"] if a["org"] == self.org else [],
                "error": a["error"], "cargando": a["cargando"], "t": a["t"]}


class PermisoVencido(Exception):
    """El permiso de Deere venció y no se puede renovar solo: hay que loguearse de nuevo."""


# Un PIN de Deere son 13 a 17 letras y números mezclados. Algunos equipos lo tienen como nombre.
PIN = re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{13,17}\b", re.I)


def tapar(texto):
    return PIN.sub("(nombre oculto)", str(texto or "")).strip()


def _entero(v, defecto=0):
    try:
        return max(0, int(v))
    except (TypeError, ValueError):
        return defecto


def _nombre(v):
    return str((v.get("name") if isinstance(v, dict) else v) or "")[:40]


def _ms(iso):
    """Fecha ISO de Deere → milisegundos (o None)."""
    try:
        return int(datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp() * 1000)
    except (TypeError, ValueError):
        return None


# ---------- Datos de mentira para las capturas (G5_DEMO=1) ----------

def DEMO_FLOTA():
    ahora = time.time() * 1000
    hora = 3600 * 1000

    def m(i, nombre, tipo, modelo, horas, hace, lat, lon, alertas=()):
        return {"id": str(i), "nombre": nombre, "tipo": tipo, "marca": "John Deere", "modelo": modelo, "anio": 2020,
                "telemetria": hace is not None,
                "lugar": {"lat": lat, "lon": lon, "cuando": ahora - hace * hora} if hace is not None else None,
                "horas": {"horas": horas, "cuando": ahora - (hace or 0) * hora} if hace is not None else None,
                "alertas": [{"cuando": ahora - 5 * hora, "codigo": c, "modulo": "ECU", "descripcion": d, "color": col, "veces": 1}
                            for c, d, col in alertas]}
    return [
        m(1, "Cosechadora 1", "Cosechadora", "S770", 2140.5, 0.3, -34.10, -56.20),
        m(2, "Tractor grande", "Tractor", "8R 340", 3310.2, 1.2, -34.12, -56.25,
          [("110.0", "Temperatura del refrigerante alta", "RED")]),
        m(3, "Pulverizadora", "Pulverizadora", "R4038", 980.0, 20, -34.05, -56.18),
        m(4, "Tractor chico", "Tractor", "6130J", 5120.7, 72, -34.20, -56.30,
          [("1569.31", "Reducción de potencia del motor", "YELLOW")]),
        m(5, "Sembradora", "Sembradora", "1113", 0, None, 0, 0),
    ]


def DEMO_ARCHIVOS():
    ahora = time.time() * 1000
    return [{"id": str(i), "nombre": n, "tipo": t, "fecha": ahora - d * 86400000, "tam": s, "pendiente": p}
            for i, (n, t, d, s, p) in enumerate([
                ("Rx trigo lote 12", "PRESCRIPTION", 0.2, 48000, True),
                ("Configuración S770", "SETUP", 3, 1200000, False),
                ("Rx maíz lote 4", "PRESCRIPTION", 6, 52000, False),
                ("Cosecha soja 2026", "DOCUMENTATION", 20, 8400000, False)])]
