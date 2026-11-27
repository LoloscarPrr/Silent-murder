# Fase 01 — Consolidación técnica (27-11-2026)

## Línea base
- Rama origen: feature/el-cuervo-base-humana-v1, commit 758aceccf8e26aa63e03e2c358a973a444b190c7.
- main: d8b6c2aea75f91cdab50b846ea8400653d410b10; la rama de origen estaba 135 commits por delante, 0 por detrás.
- Evidencia previa: Actions 45511535716 (integración y regresiones fase 11) y 45511668390 (exportación fase 12).
- La nueva versión 0.7.2 / código 13 es una candidata de consolidación, no añade contenido jugable.

## Cambios
1. Rama de integración separada. No modificar main ni la rama artística.
2. Un pipeline obligatorio de regresión + exportación Android, usa el commit del evento y el mismo GLB en ambos stages; no reimporta todas las versiones históricas.
3. Archivar workflows anteriores sin destruir su contenido; originales y recursos artísticos quedan en historial y en la rama de origen.
4. Versionado Android centralizado en export_presets.cfg; conservar paquete y ARM64. SHA256 y certificado de APK disponibles como evidencia.
5. Mantener intactos los scripts de juego, modelos, escenas y tests existentes.

## Puerta de aceptación (pendiente hasta obtener evidencia)
- [x] CI del commit de integración: integración real Cuervo + misión y las 9 regresiones existentes. Run 45993305038, commit 4a8b3781d0c739874ca856f2edde1e069a25bd76.
- [x] APK exportada, metadatos y firma verificados en run 45993305038.
- [ ] Comparar certificado SHA256 con APK anterior antes de afirmar actualización compatible.
- [ ] Android físico: instalación sobre versión previa sin desinstalar; iniciar Noche Cero, movimiento/cámara/disparo simultáneos, sigilo, navegación, expediente, extracción, derrota y reintento.
- [ ] Sesión Android de 30 minutos con registro FPS, temperatura, memoria y fallos. Objetivo mínimo propuesto: 30 FPS sostenidos, no medido todavía.
- [ ] Revisar pull request antes de fusionar; conservar main intacta hasta aprobar.

## Deuda técnica para próximas fases
- CI más robusta y escenarios de regresión; recursos externos a scripts, escenas reutilizables y separación de entrada/HUD.
- Animación anatómica, navegación 3D, audio y diseño de niveles.
- Firma persistente de distribución: no reemplazar la clave de depuración actual sin estrategia de migración. No hay firma de producción certificada.
- Los .blend y candidatos históricos se conservan por ahora; no se reescribe el historial ni se usa Git LFS sin plan de migración.

## Rollback
La rama de origen y main no se alteran. Se puede regresar a fase 12 por su commit exacto. Android no admite degradar versionCode por defecto; rollback instalable requiere una compilación posterior firmada con la clave compatible.
