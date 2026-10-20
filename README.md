# SILENT KILLER

Juego de acción y sigilo 3D original para Android, realizado con Godot 4.3 / GDScript.

## Alpha 0.5.2 — combate cuerpo a cuerpo y reducción sigilosa

Video de prueba del usuario confirmó que ya era posible aproximarse a guardias, pero faltaba neutralizarlos sin disparar.

### Qué hay de nuevo

- **REDUCIR:** acercarte a menos de 1,9 metros por detrás de un guardia que no esté en alerta roja. Un toque ejecuta una eliminación sigilosa y no consume balas.
- **GOLPEAR:** cuando un guardia está de frente o ya te ha descubierto, un golpe cuerpo a cuerpo reduce 1 punto de sus 3 de salud; tres golpes lo neutralizan.
- **Sin ataques a través de paredes:** un raycast verifica que no haya cobertura entre el operativo y el guardia.
- **Sin spam:** cooldown de 0,75 segundos para los golpes y el remate.
- **Reacción:** una pelea abierta provoca alerta en el guardia y los más cercanos pueden escuchar el forcejeo.
- **Efectos visuales provisionales:** gesto de ataque con brazos articulados y caída procedural del guardia al ser neutralizado. No hay gore.
- **Botón contextual táctil:** aparece solo si existe un guardia accesible y alcanzable. El multitouch existente sigue funcionando al moverse o girar la cámara.
- **Misión intacta:** recuperar el expediente, alcanzar la baliza de extracción, victoria y derrota. Las reducciones cuentan en el HUD de guardias.

### Limitaciones visuales

Las animaciones aún son procedimentales con modelos geométricos y no hay sincronización completa de dos personajes con animación de captura. El objetivo es validar distancia, orientación, funcionamiento y FPS en el Redmi 12 5G antes de crear un sistema de remates cinematográficos.

### Android

- `com.loloscarprr.silentmurder` conserva el ID de la aplicación para actualizar sin desinstalar.
- `versionCode=8`, `versionName=0.5.2`.
- Build Android arm64 / horizontal.
- [GitHub Actions](https://github.com/LoloscarPrr/Silent-murder/actions) genera `SilentKiller-v0.5.2-Android-debug`.

### Pruebas automáticas

Antes de exportar, CI comprueba: arranque, multitouch, armas y recarga, IA y visión de guardias, misión y extracción, derrota a 0 HP, interacción de REDUCIR por la espalda, golpes frontales, cooldown, paredes y contador de eliminaciones.

**Repositorio actual:** `LoloscarPrr/Silent-murder`, a la espera de que el propietario lo renombre a `Silent-Killer`.
