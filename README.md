# SILENT MURDER

Juego original de acción y sigilo en tercera persona para Android, desarrollado con **Godot 4.3 / GDScript**.

## Estado — Alpha v0.2 (movimiento y cámara)

Prototipo funcional de exploración sin combate; pensada para probar directamente en un teléfono Android.

- Depósito industrial 3D con colisiones.
- Protagonista **articulado provisional** construido con primitivas 3D (no es un humanoide riggeado definitivo).
- Transiciones procedurales de caminar, correr, agacharse, apuntar, brazos y rodillas.
- Movimiento analógico suavizado con aceleración y frenado.
- Agacharse también reduce la cápsula de colisión; se comprueba espacio para levantarse.
- Cámara sobre el hombro con suavizado, zoom al apuntar y chequeo de obstáculos.
- Joystick izquierdo independiente de la cámara táctil derecha.
- Contador de FPS para medir rendimiento en el Redmi 12 5G.
- Exportación Android arm64 mediante GitHub Actions y prueba automática de arranque.

**Todavía no existen:** disparos, arma real, enemigos, IA, animaciones definitivas, misiones ni progresión.

## Dirección artística

Combinación aprobada de asesino elegante y operador táctico discreto; depósito industrial nocturno. No utiliza recursos ni código de Contract Killer 2.

## Android — sin PC

En GitHub: **Actions → Android - Silent Murder → ejecución verde más reciente → artifact SilentMurder-v0.2-Android-debug**.

GitHub normalmente entrega un ZIP con el APK. Comprueba primero si Android permite actualizar la versión anterior; si dice «La aplicación no se instaló», conserva la versión previa y comparte el mensaje: puede tratarse de la firma debug. No desinstales la 0.1 sin guardar los datos que necesites.

## Próximo paso

0.3: fase de combate (arma visible y sistema de disparos). No implementarla hasta validar controles y estabilidad de la 0.2 en dispositivo.

## Criterios y pruebas

Revisar `docs/CRITERIOS_ACEPTACION.md`.
