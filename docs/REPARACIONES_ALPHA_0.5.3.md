# Silent Killer — Alpha 0.5.3: reparaciones críticas

Base: auditoría `docs/AUDITORIA_ALPHA_0.5.2.md`. Estas correcciones se concentran en el combate y el HUD. No amplían la misión ni introducen más guardias.

## Cambios

- **SK-001, sigilo coherente**: `REDUCIR` solo elimina instantáneamente a un guardia realmente desprevenido, en estado **PATRULLA** y con detección acumulada prácticamente nula (≤0,05). Guardias investigando, buscando o en alerta se enfrentan con golpes normales aunque se les ataque desde atrás. Se comprueba en el mismo instante del golpe.
- **SK-003, salida de bala real**: primero la cámara determina el punto de mira; un segundo raycast desde la **boca de la pistola** decide el primer choque físico, impidiendo que la cámara vea un blanco al otro lado de una caja y que el arma atraviese esa caja al disparar. El trazador llega al primer punto real desde el cañón.
- **SK-007, HUD separado**: el mensaje de expediente/objetivo no sobrescribe el estado global de guardias. El HUD distingue `ALARMA: …` de la misión.
- **SK-008, avisos temporales**: los mensajes de impacto, melee o recarga duran 1,8 segundos sin sustituir el encabezado permanente `SILENT KILLER / NOCHE CERO`.
- **SK-009, botón estable**: el espacio del botón de ataque melee permanece fijo. Se atenúa y deshabilita fuera de rango o durante la recuperación; `REDUCIR` o `GOLPEAR` aparecen cuando el blanco es válido.

## Compatibilidad

- VersionCode 9, versión 0.5.3 y paquete `com.loloscarprr.silentmurder` para actualizar encima de 0.5.2.
- El proyecto y el workflow conservan exportación arm64 y Android horizontal.
- No se cambia el sistema de misión, armas base, cámara ni joystick salvo validación del disparo.

## Nuevas pruebas CI

1. Guardias en PATRULLA/SOSPECHA/BUSCANDO/ALERTA, con umbral de detección.
2. Botón fijo, deshabilitado si no corresponde y reactivado con etiqueta contextual.
3. Estado global de alarma conservado al cambiar misión.
4. Mensajes temporales que desaparecen tras 1,8 segundos.
5. Cobertura entre boca del arma y blanco mientras la cámara sigue viéndolo: la bala NO atraviesa cobertura.
6. Regresión completa de disparo, recarga, sigilo, misión, muerte, multitouch y combate melee.

## Pendientes

- **SK-002** NavMesh y pathfinding de patrullas (fase 0.6).
- **SK-004/SK-005** remates sincronizados y cuerpos físicos (fase 0.7).
- Audio, arte con rig, optimización de FPS y niveles más ricos requieren fases independientes.

## QA manual en Android

Acercarse a un guardia de frente y por detrás, hacerlo investigar mediante disparo cercano, comprobar botones y probar disparar al lado de una caja con la cámara asomando por encima.
