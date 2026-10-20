# SILENT KILLER

Juego 3D de sigilo y acción original para Android, Godot 4.3 / GDScript. Repositorio actual: `LoloscarPrr/Silent-murder` (todavía no se ha renombrado el repositorio a `Silent-Killer`).

## Alpha 0.5.1 — pulido del contrato y de la interfaz

Actualización de **Operación Noche Cero**, que ya permite recuperar el expediente y escapar por la zona de extracción o fallar si los guardias eliminan al protagonista.

### Correcciones de la 0.5.1

- **Derrota correcta:** la salud permanece en `0/100`. Se eliminó la reaparición automática con salud completa que aparecía debajo de la pantalla de fracaso.
- **Un único evento de derrota:** nuevos impactos no duplican el resultado ni cambian los puntos de salud una vez terminado el contrato.
- **Controles bloqueados:** caminar, mirar o disparar no deberían continuar durante las pantallas finales.
- **Panel de victoria/fracaso:** tarjeta oscura de alto contraste, título y resumen legibles, botón grande de REINTENTAR o NUEVA PARTIDA con márgenes dentro de la tarjeta.
- **HUD de misión:** objetivo resaltado, vida y guardias más fáciles de leer; se oculta el contador de blancos de entrenamiento, pues no forma parte del contrato.
- **Sin romper lo existente:** expediente azul, extracción verde, patrullas con estados de alerta, pistola y multitouch se mantienen.
- **Menos builds redundantes:** GitHub Actions usa `concurrency` para cancelar ejecuciones obsoletas en la misma rama.

### Cómo jugar

1. Entra al depósito y busca el terminal azul al noreste.
2. Acércate y pulsa **RECUPERAR**.
3. Cruza hacia la baliza verde del suroeste.
4. Pulsa **EXTRAER** para completar el contrato.
5. Si pierdes, se mostrará **VIDA 0 / 100**, **OPERACIÓN FALLIDA** y **REINTENTAR**.

Neutralizar a los guardias no es obligatorio. Es posible intentar completar la misión en sigilo.

### Compilación Android

- Package ID preservado: `com.loloscarprr.silentmurder`.
- Versión: `0.5.1` / versionCode **7**, posterior a la 0.5.0.
- Debug APK arm64, orientado a actualizar la versión anterior si el certificado de firma coincide.
- Workflow **Android - Silent Killer**, artifact `SilentKiller-v0.5.1-Android-debug`.

### Pruebas automáticas

El workflow verifica la escena, control multitáctil, disparos y recarga, percepción de guardias, misión de infiltración/extracción, tarjeta de victoria, derrota con salud cero y botón REINTENTAR.

### Pendiente

Optimización para estabilizar FPS en dispositivos reales, mejorar las rutas y coberturas de guardias, nuevos modelos 3D y un HUD artístico definitivo. Esta versión sigue siendo un prototipo funcional.
