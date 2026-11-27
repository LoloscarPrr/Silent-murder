# SILENT KILLER

Juego original de acción y sigilo 3D para Android, desarrollado en **Godot 4.3 / GDScript**.

## Alpha 0.6 — guardias con navegación A*

**Objetivo:** resolver el atasco de guardias en cajas y estanterías antes de ampliar el contenido visual o las misiones.

### Mejoras

- Ruta de navegación con **AStarGrid2D** sobre el depósito plano. El mapa se construye a partir de los **mismos volúmenes de colisión** de las estanterías, la oficina, las cajas y las paredes.
- Márgenes de seguridad alrededor de obstáculos para que una ruta no pase rozando las cajas.
- Los guardias calculan una ruta para las tres acciones existentes: **patrullar**, **investigar sonidos** y **perseguir al protagonista**.
- Recálculo de ruta cuando cambia el destino, transcurre un intervalo o el guardia detecta que se ha quedado atascado.
- Simplificación de puntos intermedios únicamente cuando la línea recta no atraviesa obstáculos.
- El A* funciona sobre el suelo del escenario actual; **todavía no es NavMesh**, no contiene escalones, desniveles ni evasión avanzada entre guardias móviles.
- Se conservan la misión **Operación Noche Cero**, el expediente, la extracción, vida, tres guardias, disparos y combate melee.
- Sin efectos adicionales que aumenten artificialmente el consumo de GPU en el Redmi 12 5G.

### Pruebas automáticas

Además de las pruebas previas de misión, derrota, disparos con cobertura, multitoque y melee, la suite incluye una prueba de navegación que obliga al guardia a encontrar una ruta alrededor de una estantería. Comprueba que los tramos no atraviesen obstáculos, que encuentre un desvío, que repita el cálculo, que cambie de ruta con un destino nuevo y que funcione en patrulla, investigación y persecución.

### Lo que se debe probar en el teléfono

- Deja que un guardia patrulle cerca de una estantería. Debe ser capaz de dar la vuelta cuando la ruta se lo exija.
- Desde detrás de una caja, dispara para provocar una investigación. Debe buscar un camino hacia el ruido.
- Provoca una alerta y cambia de lado de una estantería. Debe seguirte rodeando el obstáculo, no avanzar indefinidamente contra él.
- Verifica que reducir guardias, recargar y recuperar el expediente sigan funcionando.
- Mira los FPS durante persecuciones. **La suite de CI no mide rendimiento real en Android**.

### Limitaciones conocidas

No hay aún sonidos, NavMesh 3D, coordinación grupal avanzada, coberturas inteligentes, humanoides riggeados ni remates sincronizados. No ampliar misiones hasta aprobar la navegación real.

### Android

- Paquete: `com.loloscarprr.silentmurder` (se conserva para actualizar).
- Versión `0.6.0`, versionCode **10**, arm64 horizontal.
- Workflow **Android - Silent Killer**, artefacto `SilentKiller-v0.6-Android-debug`.
- Repositorio actual `LoloscarPrr/Silent-murder`. El nombre visible de la app es **Silent Killer**.

## Próximo hito

Si la navegación supera las pruebas manuales, la fase 0.7 se centrará en mejorar las animaciones cuerpo a cuerpo, reacciones al daño, audio y presentación visual, sin perder rendimiento ni funcionalidad.
