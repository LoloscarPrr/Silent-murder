# El Cuervo — producción 3D (Fases 1–3)

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


## Situación de producción (27-10-2026)
- **Fase 1:** base humana BLEND/GLB generada y reimportada en Blender/Godot 4.3. La anatomía base fue aceptada por el usuario como punto de partida, **no como personaje terminado**.
- **Fase 2:** inspección de poses y [LOD40 experimental](../../character_assets/el_cuervo/fase2/Fase2_Auditoria.json) producido: 43.625 triángulos frente a 109.064 originales. La prueba de muñeca y vistas de manos no quedaron resueltas; la evaluación visual y FPS Android siguen pendientes.
- **Fase 3:** [PLAN_VESTUARIO_FASE3.md](PLAN_VESTUARIO_FASE3.md) es el plan de producción modular para blazer, camisa, pantalón, botines y accesorios. **Es documentación de trabajo; no implica que las prendas ya estén modeladas.**

El siguiente hito verificable es producir y revisar el bloque geométrico **blazer + camisa** en un archivo BLEND independiente, sin reemplazar el personaje jugable ni alterar la APK.
