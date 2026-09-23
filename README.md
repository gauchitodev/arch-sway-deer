# arch-sway-deer

Escritorio estilo G5 para Sway.

Una capa de personalización para [Sway](https://swaywm.org/) que le da a tu escritorio Linux
la estética de las pantallas de cabina **G5 CommandCenter** de las cosechadoras y tractores:
barra verde, bloque de estado verde azulado, lo seleccionado en amarillo, íconos en
cuadrados con la franjita verde y una **pantalla de inicio táctil** con paneles de datos.

Hecho por un operador de maquinaria agrícola que aprende a programar, para su laptop con
pantalla táctil.

## Qué trae

- **Barra de arriba** (Waybar) con el estilo de la barra de título de la G5.
- **Colores de ventanas, lanzador de apps (wofi), notificaciones (mako) y pantalla de bloqueo** a juego.
- **Pantalla de inicio** (`Super+G`), pensada para el dedo:
  - **Páginas de trabajo** con paneles de 3 tamaños (Chico, Ancho, Grande), que se editan como en el monitor:
    batería (salud, temperatura, consumo), procesador, memoria, datos usados por día (para cuidar el hotspot),
    temperaturas, wifi, disco, reloj, música sonando (YouTube / YouTube Music), mapa, últimos videos de YouTube,
    notas y el estado de un bot que corre en otro equipo por SSH.
  - Si una página no entra en la pantalla, lo que sobra pasa solo a la siguiente.
  - **Menú de apps** estilo G5: Favoritas, Todas las apps y Sistema (apagar y reiniciar piden dos toques).
  - Modo **día** y **noche**, y un **bip** al tocar los botones, como el monitor.
- Fondo de pantalla y pantalla de bloqueo con fotos propias de una S770 en cosecha.

## Requisitos

Funciona encima de [sway-workstation](https://github.com/carlosplanchon/sway-workstation)
(de Carlos Planchón): usa su barra y sus atajos como base. La barra G5 carga la config y los estilos
de esa barra y los retoca, y atajos como `Super+D` (lanzador) o `Super+Shift+X` (bloquear) son de ahí.
Sobre otro Sway con Waybar también anda, pero puede que falten módulos en la barra o algunos atajos.

```
sudo pacman -S sway waybar wofi mako swaylock chromium python jq playerctl pamixer brightnessctl grim slurp wl-clipboard foot cantarell-fonts
```

No hace falta instalar nada de Python: el servidor de la pantalla de inicio usa solo la librería estándar.

## Instalación

```
git clone https://github.com/gauchitodev/arch-sway-deer.git ~/.config/g5
~/.config/g5/instalar.sh
```

El instalador:
- agrega **una sola línea** al final de `~/.config/sway/config` (`include ~/.config/g5/sway.conf`),
- enlaza los estilos de wofi, mako y swaylock (si ya tenías uno propio, lo guarda como `.antes-g5`),
- crea la carpeta `local/` con lo que depende de tu usuario.

Se puede correr las veces que quieras.

## Uso

| Qué | Cómo |
|---|---|
| Abrir o cerrar la pantalla de inicio | `Super+G`, o el botón verde **Inicio** de la barra |
| Pasar de página | flechas de arriba, deslizar el dedo o las flechas del teclado |
| Acomodar paneles | botón **Editar** |
| Menú de apps | botón verde **Menú** (se cierra con la X amarilla o Esc) |

## Panel del bot (opcional)

Muestra si un bot que corre en otro equipo (por ejemplo, un celular con Termux) está andando.
Se configura en `local/config.json`, que no se sube al repo:

```json
{
  "bot": {
    "nombre": "Mi bot",
    "dispositivo": "el celular",
    "destino": "usuario@192.168.1.50",
    "puerto": 8022,
    "comando": "pgrep -f mi-bot.js >/dev/null || exit 1"
  }
}
```

El `comando` corre en el otro equipo: tiene que salir con `0` si el bot anda (y puede imprimir cuántos
segundos lleva andando) y con `1` si está detenido. Hace falta entrar por SSH **con llave**, sin contraseña.

## Desinstalar

Borrá la línea `include ~/.config/g5/sway.conf` de tu config de Sway, borrá los enlaces
`~/.config/wofi/style.css`, `~/.config/mako/config` y `~/.config/swaylock/config`
(y renombrá los `.antes-g5` si tenías), y recargá con `Super+Shift+C`.

## Un detalle

Hay un **easter egg** escondido. Pista: las fotos tienen historia.

## Licencia y aviso

- Código: licencia MIT, ver [LICENSE](LICENSE).
- Fotos (`fondo.jpg`, `bloqueo.jpg`): © gauchitodev, sacadas en el campo en Uruguay. No están bajo la licencia MIT.
- Proyecto personal inspirado en la estética de las pantallas G5 CommandCenter. **No está afiliado ni
  respaldado por Deere & Company.** John Deere, G5 CommandCenter y el logo del ciervo son marcas de
  Deere & Company. Este repo no incluye software de John Deere.
