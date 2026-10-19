# SILENT KILLER

Juego original de sigilo y acción en tercera persona para Android, realizado con Godot 4.3 / GDScript. Repositorio actual: `LoloscarPrr/Silent-murder` (pendiente de renombrar a `Silent-Killer`).

## Alpha 0.4 — Guardia, visión y sigilo

El depósito de pruebas de la 0.3 ahora contiene **tres guardias patrullando** en rutas predefinidas y cuatro blancos de entrenamiento.

### Qué probar

- **Patrulla:** los guardias recorren distintas zonas del depósito.
- **Visión real:** el guardia usa distancia, ángulo frontal y un raycast físico que no puede atravesar paredes ni cajas; agacharse reduce la rapidez de detección y correr la aumenta.
- **Sospecha:** al observar algo extraño, investiga el lugar; al perder el contacto, busca antes de volver a patrullar.
- **Ruido:** la pistola con supresor todavía se oye a corta distancia (9 metros en el prototipo). Los guardias cercanos investigan.
- **Combate:** si te detectan y tienen línea de visión, pueden disparar. El protagonista tiene 100 HP, tiempo breve de invulnerabilidad tras un golpe, y reaparece en la entrada si se queda sin vida.
- **Guardias resistentes:** 3 impactos de pistola para neutralizarlos. Los neutralizados ya no disparan ni bloquean balas.
- **Indicadores:** GUARDIAS neutralizados, VIDA y ESTADO PATRULLA / SOSPECHA / ALERTA.
- **Multitouch:** joysticks, apuntado, disparo, carrera, agacharse y recarga conservan los contactos independientes de 0.2.1.

### Límites de esta fase

Los guardias son modelos de bloque de prueba con animaciones simples, no humanos riggeados. Las patrullas todavía no usan navegación por malla; pueden atascarse con determinados objetos (eso es algo que evaluaremos en el teléfono). Los enemigos hacen daño por disparo cuando tienen línea de visión, pero todavía faltan efectos de sonido, animaciones y sistemas completos de cobertura, misión y extracción.

### Cómo obtener el APK

Abre [GitHub Actions](https://github.com/LoloscarPrr/Silent-murder/actions) y descarga el artefacto **SilentKiller-v0.4-Android-debug** de la última ejecución exitosa. La app usa el mismo ID `com.loloscarprr.silentmurder`, código de versión 5 y Android arm64.

### Pruebas automatizadas

GitHub valida importación de Godot, carga de escena, multitouch independiente, disparos y recarga, y añade pruebas de visión, obstáculos, ruido, IA, daño y neutralización. La aprobación real de jugabilidad y FPS requiere prueba en tu Android.

### Próximo objetivo

Después de validar la IA, implementar navegación/cobertura y una misión pequeña con objetivo y extracción. Mantener la identidad original de espía elegante + táctico oscuro; no reutilizar contenido de Contract Killer 2.
