# SILENT KILLER

Videojuego original de sigilo y combate 3D para Android, creado con Godot 4.3 y GDScript.

**Repositorio actual:** `LoloscarPrr/Silent-murder` (renombrable por el propietario a `Silent-Killer`).

## Alpha 0.5 — Operación Noche Cero

Primera misión completa en el depósito industrial. No es necesario derrotar a todos los guardias:

1. **Infiltrarte** en el depósito y acercarte a la terminal azul, en el sector noreste.
2. Cuando aparezca **RECUPERAR**, pulsarlo para asegurar el expediente protegido.
3. La zona de extracción del extremo suroeste se iluminará en verde.
4. Llegar a la baliza verde y pulsar **EXTRAER** para completar el contrato.

La pantalla muestra la distancia aproximada hasta el siguiente objetivo y el estado de misión. La terminal y la extracción se activan solamente por proximidad: no puede recogerse el expediente desde lejos ni extraer antes de cumplir el objetivo.

Si los guardias neutralizan al protagonista, la misión falla y aparece **REINTENTAR**. Al tener éxito aparece **NUEVA PARTIDA**. Ambos reinician la escena.

### Se mantiene de 0.4

- Tres guardias con patrulla, sospecha (amarillo), alerta (rojo), línea de visión y reacción al sonido.
- Sigilo agachado, carrera, visión de cámara, pistola de 12 balas y recarga.
- Controles multitouch independientes para movimiento, cámara y disparo.
- Vida del jugador, HUD de munición, guardias, blancos de entrenamiento y FPS.
- Los guardias y las placas de entrenamiento siguen siendo prototipos geométricos.

### Alcance y límites

Es un primer ciclo de juego, no una campaña ni un escenario artístico terminado. No hay aún menús de selección de misión, narrativa cinemática, navegación con NavMesh, cobertura táctica avanzada ni modelado humanoide riggeado. Los guardias conservan sus rutas prototipo y pueden atascarse ante determinadas cajas.

### Android

- `com.loloscarprr.silentmurder` se conserva para permitir actualización de la app existente.
- versionCode **6** y versión **0.5.0**.
- Godot 4.3 / Android arm64 / orientación horizontal.
- GitHub Actions: `Android - Silent Killer`, artifact `SilentKiller-v0.5-Android-debug`. Las actualizaciones requieren firma digital idéntica.

### Pruebas CI

El workflow ejecuta pruebas de arranque, multitouch, disparos/recarga, guardias con cobertura y el ciclo de la misión (sin extracción prematura, expediente, extracción, victoria y derrota). La experiencia final se valida en el dispositivo.
