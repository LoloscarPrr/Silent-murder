# El Cuervo 2.0 — Prototipo de personaje 3D

## Objetivo
Segunda iteración de un personaje propio de Silent Killer, para reemplazar a futuro la figura geométrica del juego. Partiendo del feedback del usuario (el v0.1 parecía un muñeco de bloques), esta versión mejora anatomía, silueta, materiales y acabado, antes de integrar en Godot.

## Qué se genera
En GitHub Actions, flujo `3D Assets - Blender El Cuervo 2.0`, se ejecuta `tools/blender/build_el_cuervo_v2.py` de forma automática en Blender y produce:
- `El_Cuervo_v2.blend`: modelo editable de Blender, con piezas y armature.
- `El_Cuervo_v2.glb`: modelo importable en Godot o visor web 3D.
- Cuatro vistas PNG: frente, tres cuartos, perfil y espalda para revisarlo desde el móvil sin instalar aplicaciones.

## Dirección
Traje de operador elegante grafito, chaleco antibalas discreto, guantes, equipo leve. Cabeza con orejas, nariz, ojos, boca, cabello corto y mandíbula; pecho y extremidades orgánicos y proporcionados; manos con dedos diferenciados, botas con suela; sin accesorios futuristas exagerados.

## Alcance técnico real
Este es un **prototipo semirrealista estilizado**, no un escaneo ni un personaje AAA. Las piezas están asignadas a un esqueleto básico con pesos rígidos por pieza, para facilitar la inspección y una primera sustitución de placeholder. Antes de producir animaciones de combate definitivas habrá que unificar o refinar mallas, añadir skinning suave y corregir deformaciones en articulaciones.

## Proceso móvil
1. Revisar primero el PNG de cuatro ángulos.
2. Abrir el GLB en 3dviewer.net desde Chrome para girar el modelo.
3. Recolectar feedback de proporciones, rostro, vestuario y accesorios.
4. Revisar animación y retargeting en Godot en una rama de pruebas, sin reemplazar el APK estable.
