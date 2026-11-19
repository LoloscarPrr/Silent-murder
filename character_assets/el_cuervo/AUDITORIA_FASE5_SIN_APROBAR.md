# SILENT KILLER — El Cuervo: auditoría de Fase 5 (28 octubre 2026)

## Estado
**NO APROBADO ARTÍSTICAMENTE. No fusionar. No reemplazar personaje jugable.** 
Rama de trabajo: `feature/el-cuervo-base-humana-v1`.

Se intentó corregir el traje de la Fase 4 de dos maneras:
- Cortar la región frontal del traje Toigo: produjo roturas visibles y geometría irregular en pecho y axilas; resultado rechazado.
- Adaptar el traje elegante **MakeHuman system male_elegantsuit01** CC0 completo y a escala uniforme: mejoró notablemente la silueta del torso y la caída de pantalón frente al modelo anterior, pero la camisa/corbata/collar originales sobresalen hasta la cara.

Después, se probaron dos reparaciones del collar:
- Mover vértices superiores mediante máscara espacial: deformó solapas y hombros y produjo picos grandes; rechazado.
- Recortar zonas de textura de camisa clara mediante UV: dejó agujeros y restos de corbata muy cerca de la boca; rechazado.

### Datos confirmados del traje alternativo original (antes de las reparaciones fallidas)
- Procedencia: `male_elegantsuit01.obj`, MakeHuman system assets, CC0.
- Prenda real, no geometría de primitivas.
- 14.956 triángulos de ropa base, 7.613 vértices. Textura original y UV conservados.
- Escala **uniforme** al cuerpo de 1,84m (factor aproximado 0.11162 desde el OBJ original).
- Cuerpo humano anterior **sin modificar**, esqueleto de 163 huesos conservado.
- Importación del GLB aprobada técnicamente en Blender 4.3 y Godot 4.3.
- Animación/simulaciones de ropa: **no aprobadas**.
- FPS Android: **sin medir**.
- Protección: `main` y APK del juego **no modificados**.

### Archivo técnico de prueba
- Script: `tools/el_cuervo/fase5_system_elegant.py`.
- Workflow: `.github/workflows/el-cuervo-fase5-sastre-cc0.yml`.
- Entregables WIP y renders en `character_assets/el_cuervo/fase5_sastre_cc0/`.
- La rama también retiene pruebas anteriores de recorte no aprobadas para diagnóstico.

### Bloqueo artístico real
La ropa se creó originalmente para el cuerpo y la pose base de MakeHuman; hacerla coincidir con el cuerpo GLB aprobado mediante escalado y transferencia de pesos por vértice cercano **no es equivalente al ajuste de vestuario artístico**. Los intentos automáticos de editar collar, solapas y mangas ocasionaron defectos mayores.

**No seguir aplicando deformaciones generales ni recortes por luminosidad a la prenda existente.** La solución correcta es adaptar en Blender a nivel de piezas (jacket, collar, camisa, corbata, pantalón), respetando sus costuras y UV, hacer retopología y skinning específicos, corregir hombros y cuello en viewport y validar visualmente después de cada ajuste.

### Puerta de aprobación próxima
Un render real frontal y tres cuartos debe mostrar: chaqueta sin invadir rostro, camisa negra separada sin agujeros, hombros naturales, brazos con puños alineados y botines coherentes. Se exige inspección visual antes de publicar como "refinado".
