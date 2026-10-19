# SILENT MURDER

Juego original de acción y sigilo en tercera persona para Android, desarrollado con **Godot 4.3 / GDScript**.

## Estado — prototipo v0.1

- Depósito industrial 3D provisional con colisiones.
- Protagonista de geometría básica: traje elegante + chaleco táctico y guantes negros.
- Cámara sobre el hombro, joystick izquierdo y arrastre derecho para la cámara.
- Botones de correr, agacharse (visual) y apuntar (zoom de cámara).
- Exportación Android arm64 con GitHub Actions.

**No contiene aún:** disparos, armas funcionales, enemigos, IA, animaciones definitivas, misiones ni progresión.

## Dirección artística

Combinación de un asesino elegante y un operador táctico discreto, con identidad original y sin reutilizar recursos ni código de Contract Killer 2.

## APK para probar (sin PC)

En GitHub abre **Actions → Android - Silent Murder**. Si el workflow termina en verde, abre su ejecución y descarga el artefacto **SilentMurder-Android-debug**. GitHub suele entregarlo en un ZIP que contiene el APK.

La exportación es preliminar. Si aparece un error, revisar los logs antes de asumir que funciona.

## Compatibilidad y actualizaciones

Configurado para Android horizontal y arquitectura arm64. El rendimiento de 30 FPS en Redmi 12 5G es un objetivo por probar. Para instalar futuras versiones encima de una misma app será imprescindible configurar una clave de firma estable: esta primera firma debug no está garantizada entre builds.

Consulta `docs/DIRECCION_DE_ARTE.md` y `docs/CRITERIOS_ACEPTACION.md`.
