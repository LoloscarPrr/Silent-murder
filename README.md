# SILENT MURDER

Videojuego original de sigilo y acción 3D para Android. Godot 4.3 y GDScript.

## Alpha 0.2.1 — multitouch independiente

- **Dedo izquierdo** en la mitad inferior izquierda: joystick analógico, camina o cambia dirección.
- **Otro dedo** en la derecha: deslizar para girar la cámara mientras te mueves.
- **Dedo adicional en CORRER**: mantén pulsado y sigue moviéndote/mirando.
- **APUNTAR**: toca para activar o desactivar zoom y postura (todavía sin armas).
- **AGACHAR**: toca para alternar postura de sigilo, con colisión reducida.
- La entrada se identifica por el índice de cada dedo. Levantar uno no interrumpe los demás.
- Desactivada la emulación táctil del ratón para evitar duplicar eventos.
- Los botones son superficies visuales; sus acciones son procesadas por un único gestor multitáctil.
- Al minimizar la app se liberan los botones sostenidos y se centra el joystick.
- Escalado del HUD para distintas resoluciones y contador de FPS.
- Prueba automática de cuatro dedos en GitHub Actions (escena en `tests/multitouch_test.tscn`).

La cámara, el nivel industrial y el protagonista articulado procedural de la 0.2 se mantienen.

**Esta versión es todavía una demo técnica:** no hay pistola funcional, enemigos, IA ni misión.

## Exportación Android sin PC

La rama `main` genera APK en GitHub Actions: **Actions → Android - Silent Murder → última ejecución verde → SilentMurder-v0.2.1-Android-debug**.

Archivo firmado para depuración, `com.loloscarprr.silentmurder`, `versionCode=3`.
La actualización encima de la 0.2 exige que ambas APK utilicen la misma firma. Si Android rechaza la actualización, revisaremos el certificado antes de sugerir desinstalar.

## Dirección artística

Asesino elegante + equipamiento táctico discreto. Assets y código originales, sin reutilizar materiales protegidos de Contract Killer 2.

## Próxima fase

Tras validación manual del multitouch en Redmi 12 5G, considerar la 0.3 con arma visible, apuntado y disparo; se mantendrán los identificadores de dedos para que disparar tampoco interrumpa movimiento o cámara.
