# EL CUERVO — AUDITORÍA ARTÍSTICA Y TÉCNICA v1
Fecha: 2026-10-25 (Chile) / ejecución en GitHub Actions el 2026-10-26 UTC.

## Entregables y verificaciones reales
- Fuente: Innerscene Male Base Mesh - 3D Person, Rigged A-pose (MakeHuman CC0): https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89
- Generación realizada usando Blender oficial 4.3.2 (GitHub Actions).
- Archivo editable BLEND guardado y reabierto; GLB válido reimportado en Blender, importado en Godot 4.3.
- GLB contiene nodos de malla: base_male_body y base_male_body.high-poly. 163 huesos y un material.
- Altura tras exportación y reimportación: 1,839948 m; objetivo 1,84 m.
- 109.064 triángulos en geometría importada, 72.771 vértices en Blender antes de exportar.
- Se excluyó el helper Icosphere de la fuente antes del escalado. Blender reimportador vuelve a crear una Icosphere auxiliar SIN NODO en el JSON GLB; no pertenece a la escena GLB exportada. El verificador comprueba este hecho y no la cuenta como figura.
- Prueba de deformación: hueso upperarm01.L rotado, se observó desplazamiento geométrico en los vértices asociados. NO sustituye revisión exhaustiva de articulaciones.
- No hay medición de FPS, LOD ni benchmark en Android.

## Revisión visual real de los renders PNG
Se inspeccionaron las vistas frontal, lateral, posterior, tres cuartos y la imagen de topología generadas en Blender, no imágenes generadas con IA.

Hallazgos:
- Silueta humana continua, proporciones generalistas convincentes, A-pose de brazos descendentes, manos y pies presentes.
- Modelo es un maniquí anatómico neutro; no está caracterizado todavía como hombre de 38 años ni protagonista cinematográfico. Rostro, manos, dedos y articulaciones requieren planos detalle.
- La topología es muy densa y fundamentalmente triangulada. 109k triángulos son un presupuesto alto para un único protagonista Android si se suman traje, piel, cabello y armas.
- El wireframe frontal es visible pero con sombras/cortes contrastados en la zona facial; debe mejorarse la iluminación de la vista técnica para una auditoría limpia.
- La imagen llamada `06_Manos_y_Rostro.png` es una vista de figura completa desde otro ángulo y **no** constituye un plano detalle válido de rostro y manos.
- No se ha examinado una secuencia de flexiones en rodilla, codo, muñeca, hombro y dedos; solo prueba de desplazamiento automática en brazo.
- La geometría del cuerpo puede usarse como base de modelado y futura confección de vestuario, pero NO está aprobada aún como personaje final ni como rig completo de animación.

## Próximo requisito antes de integración en el juego
1. Render auténtico con zoom de cada mano, cuello, cara, hombros y articulaciones.
2. Probar poses doblando hombros, codos, rodillas, manos y dedos y documentar defectos reales.
3. Retopología/LOD conservando silueta y deformaciones, con recuentos reales medidos después.
4. Medir en Godot 4.3 sobre Android real antes de aprobar rendimiento.

**Estado: entregables técnicos generados y verificados; aceptación artística y optimización Android pendientes.**
