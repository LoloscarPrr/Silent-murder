# El Cuervo — base humana profesional (Fase 1)

Esta rama es un área de producción **aislada del juego**: no altera la escena jugable ni la APK existente.

## Fuente legal
- Malla de estudio: [Male Base Mesh — Rigged A-Pose](https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89), distribuida por Innerscene bajo CC0 y derivada de MakeHuman.
- [Licencia oficial de MakeHuman/MPFB](https://www.makehumancommunity.org/about/license.html): recursos principales CC0. El programa es GPL/AGPL según herramienta.
- No se usan personajes comerciales ni modelos de John Wick.

## Producción automatizada
El workflow [el-cuervo-base-humana.yml](../../.github/workflows/el-cuervo-base-humana.yml) prepara Blender 4.3.2, obtiene el GLB humano original, verifica su estructura, reescala la figura a 1,84 m, guarda el archivo editable .blend y un GLB de Godot, produce seis imágenes desde la malla real y hace una segunda comprobación de archivos en Blender. También intenta importar el GLB en Godot 4.3 estable.

La procedencia y los contadores medidos se guardan junto a los archivos en `character_assets/el_cuervo/fase1/` **solo si la ejecución termina correctamente**.

## Descargar desde Android
Abre la carpeta `character_assets/el_cuervo/fase1/` de esta rama en GitHub cuando aparezca una ejecución correcta. Puedes abrir y descargar cada archivo individualmente desde GitHub. También puedes abrir la pestaña Actions > El Cuervo y revisar los resultados. Como alternativa, el workflow genera un paquete de respaldo.

## Auditoría
Un archivo generado y una compilación verde no aprueban la anatomía, la calidad del rig ni el rendimiento en un dispositivo. Son obligatorias las inspecciones frontales, laterales, posteriores, de manos, hombros, rostro y pruebas reales en Android antes de reemplazar el personaje del juego.
