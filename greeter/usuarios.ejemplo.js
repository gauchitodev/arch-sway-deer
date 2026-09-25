// Copiá este archivo a ~/.config/g5/local/greeter/usuarios.js y poné ahí tus fotos.
// Cambiá "usuario1"/"usuario2" por los nombres de usuario reales (los de `ls /home`).
// "lado": "izquierda" o "derecha". "color": borde y aro. "resalte": chispas al escribir.
// "encuadre": qué parte de la foto se ve, ej. "35% 60%" (opcional). "tinte": true tiñe la foto con el color.
// "brillo": aclara u oscurece la foto (1 = normal, de 0.5 a 2), ej. 1.4 para una foto oscura.
// Las fotos van en la misma carpeta, con nombres sin espacios (ej: yo.jpg).
// campo.png y montanas.png son dibujos de ejemplo (greeter/ejemplo/): reemplazalos por los tuyos.
window.G5_USUARIOS = {
  "usuario1": { "nombre": "Usuario 1", "detalle": "", "foto": "campo.png",    "color": "#5ea23a", "resalte": "#ffde00", "lado": "derecha" },
  "usuario2": { "nombre": "Usuario 2", "detalle": "", "foto": "montanas.png", "color": "#9a86cf", "resalte": "#e7e1f6", "lado": "izquierda" }
};
