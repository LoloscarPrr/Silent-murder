# SILENT KILLER

Juego original de sigilo y acción 3D para Android horizontal. Godot 4.3 / GDScript.

## Base de integración 0.7.2 (candidata, no lanzamiento aprobado)

- Rama de trabajo: `integration/phase-01-baseline`. Origen: fase 12, commit `758aceccf8e26aa63e03e2c358a973a444b190c7`.
- Misión Operación Noche Cero: infiltración, recuperar expediente y extracción; tres guardias, A* en plano, controles multitouch, disparo, recarga, sigilo y melee.
- El Cuervo: GLB real, 53 huesos, dos clips (Walk/Aim), fallback visual. Agacharse, correr y melee siguen siendo gestos temporales; arte sin aprobación definitiva.
- Android arm64, paquete `com.loloscarprr.silentmurder`, versionCode 13. APK de depuración; la actualización depende de la firma previamente instalada.
- Único workflow de producción: `.github/workflows/build-android.yml`. Pruebas de integración y nueve regresiones antes de exportar. El APK solo incluye el proyecto jugable y su GLB, sin candidatos Blender ni escenas de pruebas.

## Verificación y desarrollo

El workflow compila el commit disparador, no una rama fija. Conserva registros, SHA256 y certificado de firma. Las pruebas headless no certifican FPS, consumo ni calidad artística en Android.
Los workflows experimentales se conservan en `tools/archive/workflows/` y en la rama original. No se eliminan los archivos fuente de arte.
Consultar [Fase 01](docs/FASE_01_CONSOLIDACION.md) para la puerta de aceptación y [Fase 0.6](docs/README_ALPHA_06.md) para el historial.

Próximo hito: Fase 02, ampliar protección de regresiones y automatizar verificaciones adicionales. No fusionar en main hasta pasar CI y prueba móvil.
