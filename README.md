# SILENT MURDER

Prototipo Android original de acción y sigilo 3D en **Godot 4.3 / GDScript**.

## Alpha 0.3 — polígono de entrenamiento

Primera iteración con disparos reales y blancos estacionarios, no humanos. Conserva el depósito 3D y los controles multitouch de la 0.2.1.

- Pistola de entrenamiento provisional con supresor visual y destello de boca.
- Disparos por **raycast** desde el centro de la cámara; efecto luminoso breve del cañón al punto de impacto.
- Cargador de 12 balas, 48 de reserva, 1,3 segundos de recarga.
- Disparo sostenido con cadencia limitada, independiente de caminar y mirar.
- Cuatro blancos en el depósito. Cada uno soporta **tres impactos** antes de quedar desactivado.
- Marcador de blancos abatidos, contador de munición y FPS.
- Botones táctiles adicionales **DISPARAR** (mantener) y **RECARGAR** (tocar).
- Se mantiene el apuntado con cámara cercana, carrera, postura agachada y los identificadores independientes de cada dedo.
- Prueba automática de disparo, impactos, recarga y multitouch, además de la prueba de escena y la anterior de multitouch.

### Controles Android

| Acción | Control |
|---|---|
| Mover | Joystick táctil izquierdo |
| Girar cámara | Deslizar libremente a la derecha sin ocupar botones |
| Correr | Mantener CORRER |
| Sigilo | Tocar AGACHAR |
| Apuntar | Tocar APUNTAR (alternar) |
| Disparar | Mantener DISPARAR |
| Recargar | Tocar RECARGAR |

En esta Alpha no hay enemigos, IA, bajas humanas, contratos ni campaña; los blancos son placas de entrenamiento.

## Compilar sin PC

[GitHub Actions](https://github.com/LoloscarPrr/Silent-murder/actions) → ejecución más reciente verde de **Android - Silent Murder** → artefacto `SilentMurder-v0.3-Android-debug`.

La exportación usa Android arm64 y package `com.loloscarprr.silentmurder` con versionCode 4. Las APK de prueba solo se actualizan directamente si mantienen el mismo certificado de firma.

## Línea de producción

- 0.1: motor, entorno 3D, cámara y control básico.
- 0.2: locomoción procedimental, sigilo, cámara anticolisión.
- 0.2.1: multitouch con contactos independientes.
- **0.3:** disparos, munición, recarga y blancos estacionarios.
- 0.4 propuesta: estados básicos de guardias y reacción ante disparos, luego evaluaremos audio, animaciones y objetivos de misión.

Los elementos gráficos son provisionales y originales. No se reutilizan archivos ni personajes de Contract Killer 2.
