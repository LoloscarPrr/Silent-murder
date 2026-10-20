# Silent Killer — Auditoría Alpha 0.5.2

**Estado:** inspección técnica, no corrección.  
**Evidencia:** video de juego de ~101 segundos facilitado por el usuario el 20-10-2026, scripts en `main` y pruebas de CI existentes.  
**Criterio:** distinguir lo observable, lo reproducible por lectura de código y lo que requiere nueva prueba en dispositivo.

## Resumen ejecutivo

La Alpha 0.5.2 sí contiene el ciclo de misión, disparos, detección, reducción por detrás, golpes frontales y controles multitouch. El video muestra un guardia neutralizado y progreso de misión; durante la grabación aparecen aproximadamente **31–49 FPS** en los fotogramas revisados. La nueva mecánica funciona funcionalmente, pero aún no es una ejecución cinemática coordinada y la IA depende de rutas rectas.

## P0 — Fallos de gameplay a corregir antes de ampliar misiones

### SK-001: REDUCIR permite eliminar a guardias en SOSPECHA/BUSCANDO
- **Código:** `scripts/melee_controller.gd`, `_is_unaware_from_behind`.
- **Causa:** devuelve falso solo para `guard.state == ALERT`; INVESTIGATE y SEARCH siguen habilitados para reducción de un toque.
- **Evidencia:** el video muestra «REDUCCION SILENCIOSA» mientras el HUD global marca SOSPECHA (~35 s). Ese HUD es global, así que no demuestra por sí solo que ese guardia específico estuviese sospechando; el error queda confirmado por lectura de código.
- **Corrección:** permitir remate inmediato exclusivamente con estado `PATROL`, sin detección acumulada relevante y con la orientación/detección individual del guardia validadas inmediatamente antes de aplicar el golpe.
- **Aceptación:** no hay remate instantáneo para un guardia que investiga, busca o está en alerta; los golpes frontales siguen disponibles.

### SK-002: navegación enemiga sin evasión de obstáculos
- **Código:** `scripts/guard_ai.gd`, `_move_guard`.
- **Causa:** cada destino se traduce a vector directo `target-global_position`; `move_and_slide` resuelve choques, pero no calcula ruta alternativa.
- **Riesgo:** guardias atascados contra estanterías, oficinas o cajas, incapaces de completar patrulla/investigación/persecución.
- **Corrección:** NavMesh + `NavigationAgent3D`, destinos válidos, tolerancia a obstáculo y detección de atascos.
- **Aceptación:** 10 ciclos de patrulla sin atascarse y persecución alrededor de dos obstáculos no alineados.

### SK-003: disparo desde la cámara, no desde el arma
- **Código:** `scripts/weapon_controller.gd`, `_fire_now`.
- **Causa:** impacto por raycast desde cámara central, luego trazador desde boca del arma. No se comprueba si hay una pared entre boca y punto de impacto.
- **Riesgo:** disparos visualmente imposibles al apuntar pegado a esquinas/cajas.
- **Corrección:** trayectoria en dos etapas: cámara define punto deseado, muzzle ray valida salida libre y corrige impacto/retícula si hay bloqueo.
- **Aceptación:** no dispara a través de coberturas que tapen el cañón aunque la cámara vea el objetivo.

## P1 — Bugs reales y pulido funcional

### SK-004: el remate cuerpo a cuerpo no sincroniza ambos personajes
- **Video:** ~34–40 s se aprecia reducción, pero no una coreografía de sujeción ni caída convincente; personajes geométricos pueden solaparse.
- **Código:** `scripts/operative_visual.gd` mueve brazos mediante rotaciones procedimentales; `scripts/guard_ai.gd` inclina una raíz visual tras una reducción, sin sincronización posicional.
- **Corrección:** animación doble con entrada alineada, orientación al objetivo, ventana de contacto, reacción, caída y restauración del control. Hasta contar con esqueletos y rig, usar una transición provisional sin teletransporte.

### SK-005: los guardias neutralizados no quedan como cuerpos físicos
- **Código:** `scripts/guard_ai.gd`, `_disable_guard`, desactiva las capas de colisión del actor al neutralizarse.
- **Efecto:** el cuerpo se mantiene dibujado, pero deja de tener colisión e interacción.
- **Corrección:** sustituir cápsula de guardia vivo por un cuerpo inerte simple, con manejo diferenciado de visibilidad/interacción según rendimiento.

### SK-006: la IA tiene percepción demasiado básica
- **Código:** `can_see_player` usa un solo rayo a un punto y `_update_detection` cambia velocidad por agacharse/correr; no tiene ocultación por luminosidad, visión periférica gradual, aviso grupal ni investigación cooperativa.
- **Corrección:** intensidad de visibilidad + múltiples muestras raycast de torso/cabeza; aviso limitado a compañeros; estados de búsqueda con última posición conocida.

### SK-007: indicador «ESTADO» mezcla conceptos
- **Código:** `scripts/main.gd` actualiza estado global según guardias; `scripts/mission_manager.gd` llama a `hud.set_alert_status("OBJETIVO ASEGURADO")`.
- **Efecto:** mensaje del objetivo se sobreescribe al cambiar estados de guardias; la pantalla no distingue estado de un guardia y el estado general.
- **Corrección:** indicadores separados de misión, alarma global y sospecha local.

### SK-008: notificaciones de acciones quedan fijas
- **Video:** «REDUCCION SILENCIOSA», «Bajo fuego», «De pie» aparecen como título superior mientras transcurre el juego.
- **Código:** `scripts/mobile_controls.gd`, `_set_status` reemplaza el texto sin tiempo de caducidad.
- **Corrección:** encabezado fijo `SILENT KILLER` + toast de evento durante 1–2 segundos con animación y cola de prioridad.

### SK-009: visibilidad intermitente del botón melee
- **Código:** `scripts/melee_controller.gd`, `_physics_process` lo oculta durante el cooldown y `scripts/mobile_controls.gd` cambia `visible`.
- **Efecto:** control aparece/desaparece cerca del enemigo, difícil de ubicar táctilmente.
- **Corrección:** posición fija; deshabilitado atenuado cuando no haya objetivo; feedback de recarga del golpe.

### SK-010: salud/daño sin retroalimentación visual clara
- **Video:** se observa HUD de HP y un mensaje de -7 HP, pero sin indicador direccional del atacante, sacudida/viñeta ligera ni barra rápida.
- **Corrección:** flash acotado, flecha direccional, pequeña barra de salud, sin saturar pantalla.

## P2 — Sistemas que faltan (no confundir con bugs)

1. **Audio:** no hay `AudioStreamPlayer` ni recursos de audio en el árbol del proyecto; faltan pasos, pistola/supresor, impactos, forcejeos, alertas, música y ambientes con mezclador independiente.
2. **Arte final y animación riggeada:** humanoides, armas, objetos y entorno siguen siendo primitivas. Faltan esqueletos, transiciones de locomoción, apuntado, daño, cobertura y remates.
3. **Cobertura y táctica:** asomarse, transición de esquinas, acciones contextualizadas, IA usando coberturas, coordinación de guardias, investigación fiable.
4. **Diseño de nivel:** variantes espaciales, iluminación jugable, rutas de infiltración, objetivos múltiples, alarmas y zonas restringidas.
5. **UX móvil:** controles reubicables y tamaños configurables, ajuste de sensibilidad, inversión de ejes, calibración, pausa/configuración, accesibilidad, guía inicial, indicadores objetivos en mundo y brújula.
6. **Misión/campaña:** briefing, progresión, puntos de control, puntuación de sigilo, recompensas, guardado, elección de contratos y dificultad.
7. **Rendimiento:** los fotogramas de video revisados muestran indicadores entre ~31 y ~49 FPS en distintas escenas, inferior a 57 FPS visto antes. Faltan perfiles de CPU/GPU, medidas de frame time, límites de físicas/raycast, LOD e instancias.
8. **Automatización:** CI valida lógica funcional, pero no render en Android real, latencia de controles, FPS, consumo de memoria, sonido, pausas/reanudación ni múltiples relaciones de aspecto.

## Plan de reparación recomendado

| Fase | Prioridad | Alcance | Criterio de salida |
|---|---|---|---|
| 0.5.3 | P0/P1 | SK-001, SK-003, SK-007, SK-008, SK-009; tests adicionales | reducción coherente, sin tiros a través de coberturas y HUD estable |
| 0.6 | P0/P1 | SK-002 y fundamentos de percepción/cobertura | guardias completan patrulla e investigación sin atascarse |
| 0.7 | P1/P2 | Sincronización melee, cuerpo inerte, feedback de daño y audio básico | remates legibles y acciones identificables a oído/vista |
| 0.8+ | P2 | Arte riggeado, UX de móvil, misiones, optimización | experiencia jugable sostenida con FPS estables en dispositivo |

**Conclusión:** no implementar una misión más grande todavía. Priorizar navegación de guardias, reglas de sigilo y sincronización de cuerpo a cuerpo, tras reparar exploits de combate.
