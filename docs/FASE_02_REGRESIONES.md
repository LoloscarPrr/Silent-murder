# Fase 02 — Protección de regresiones

Base CI validada: 0.7.2, commit 4a8b3781d0c739874ca856f2edde1e069a25bd76, run 45993305038. Pruebas físicas aún pendientes. Nueva candidata 0.7.3 (versionCode 14); no modifica scripts de juego.

## Nuevas suites
- touch_lifecycle_test: eventos sintéticos de la interfaz, cinco dedos independientes, dos propietarios de disparo, arrastre fuera de botón, pérdida de foco, eventos obsoletos y recuperación de movimiento.
- ammo_boundary_test: cargador vacío, reserva parcial, recarga repetida, disparo durante recarga, conservación de munición y recarga con cargador lleno o sin reserva.
- mission_restart_test: escena real, derrota y victoria, pulsación de reintento, reemplazo real de escena y restauración de jugador, munición, expediente, indicadores, HUD y guardias.

## Puerta de aceptación
- 13 suites en CI (10 anteriores + 3 nuevas). El marcador de éxito, código de salida y ausencia de errores de script son obligatorios.
- APK solo tras aprobar todas las suites. Paquete y ARM64 conservados; certificado y hash registrados.
- No confundir evento sintético ni headless con prueba Android real. La instalación sobre APK previa, rendimiento sostenido, cámara, calidad artística y controles físicos siguen pendientes.
- main y rama artística permanecen intactas. No fusionar ni iniciar refactor de jugabilidad hasta verificar el nuevo run.
