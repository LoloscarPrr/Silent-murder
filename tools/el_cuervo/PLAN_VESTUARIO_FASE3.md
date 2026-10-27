# SILENT KILLER — EL CUERVO
## Fase 3 · Plan ejecutable de modelado del vestuario (Blender 4.3 → Godot 4.3 / Android)
**Estado del documento:** planificación aprobada para ejecución; **ninguna pieza de vestuario está modelada por este documento**.
**Rama de trabajo:** `feature/el-cuervo-base-humana-v1`. **No tocar `main`, la escena jugable ni la APK.**
**Revisión:** 2026-10-27.

### 1. Punto de partida verificable
- Cuerpo aprobado por el usuario como base **suficiente para continuar**: `character_assets/el_cuervo/fase1/El_Cuervo_Base_Humana_v1.blend`; GLB equivalente en la misma carpeta.
- Altura de referencia: **1,84 m**; base original: **109.064 triángulos**, **163 huesos**, malla CC0 MakeHuman/Innerscene. Se preserva el original como referencia.
- Auditoría fase 2: `character_assets/el_cuervo/fase2/Fase2_Auditoria.json`; **LOD40 candidato de 43.625 triángulos**, 60 % menos que la base, reimportado en Godot 4.3. **No aprobado visualmente ni por FPS Android.**
- Poses numéricas de hombro, codo y rodilla reportaron desplazamiento; no prueban calidad anatómica. **Prueba de muñeca y vistas de manos pendientes:** el identificador buscado por el script no se encontró. NO declarar rig aprobado.
- No confundir aprobación de la **base** con aprobación del personaje final.

### 2. Objetivo artístico fijado
**El Cuervo:** asesino profesional civil, elegante y sobrio, de figura alta y atlética; influencia general de cine de acción elegante, **sin reproducir personajes ni vestuario comercial exacto**.
Look canónico: blazer negro entallado **abierto**, camisa negra de manga larga **sin corbata**, pantalón negro formal-funcional, botines negros de perfil refinado, cinturón y funda sobria. Guantes y corbata: variantes futuras, NO versión principal.
- Silueta: hombros naturales, cintura legible, piernas largas; movilidad y lectura desde cámara al hombro.
- Paleta de materiales PBR: blazer carbón mate; camisa negro antracita con diferencia de roughness; pantalón negro mate; botín cuero negro, detalles discretos.
- Prohibidos: chalecos voluminosos, hombreras exageradas, bolsillos cargo prominentes, insignias, armadura futurista y accesorios colgantes.

### 3. Estructura editable en Blender
```
El_Cuervo_Root
├── Armature_Original             # conservar jerarquía y nombres originales
├── Body_Base_Reference           # duplicado/cuerpo fuente intacto, referencia oculta
├── Body_Visible                  # candidato para ocultar zonas bajo ropa, no destructivo
├── Clothing
│   ├── Shirt_Inner
│   ├── Jacket_Blazer
│   ├── Pants_Main
│   ├── Boots_L
│   ├── Boots_R
│   ├── Belt_Main
│   └── Holster_Discreet
└── Optional_Disabled
    ├── Tie_Optional
    └── Gloves_Optional
```
- Cada prenda debe ser malla real editables separada, con UV, material y pesos propios; NO textura pintada que simule toda la ropa.
- Preservar colecciones y nombres estables. Posición neutra A-pose para transferir pesos. Aplicar transforms solo donde no rompan escala o skinning.
- Para el GLB de juego exportar **solo** Armature + cuerpo visible + prendas activas; omitir `Body_Base_Reference`, cámaras, luces, helpers y variantes ocultas.
- GLB válido exige nodos Skin/Skeleton3D correctamente vinculados; no basta con que aparezca una malla.

### 4. Orden de fabricación y comprobaciones
| Etapa | Geometría real a fabricar | Qué validar antes de avanzar |
|---|---|---|
| 0. Preparación | duplicar el BLEND v1, congelar original y verificar orientación, escala 1,84m, nomenclatura ósea y referencias | respaldo original, escala y referencia de pose |
| 1. Blazer | solapas, cuello, cuerpo, mangas, puños, faldón y separación real respecto a camisa | silueta frontal/perfil/espalda, amplitud hombros, axilas, brazos alzados y torso agachado |
| 2. Camisa | cuello, pechera y mangas visibles con geometría independiente | sin clipping en solapas, antebrazos, cuello y puños |
| 3. Pantalón | cintura, perneras, costuras y volumen de cadera/rodillas | flexión de cadera y rodilla sin ruptura, entrepierna sin solapes |
| 4. Botines | puntera, empeine, talón, caña y suela de perfil bajo | separación tobillo/pantalón, pivote de pie, apoyo en piso |
| 5. Cinturón y funda | piezas discretas, proporciones y anclaje claro | que no atraviesen blazer al agacharse/correr, sin armas flotantes |
| 6. Integración | pesos al esqueleto original, materiales, UV, reducción de superficie no visible | integridad al reabrir BLEND y al reimportar GLB en Godot |
| 7. Optimización | LOD(s) evaluados; simplificación de detalles secundarios y materiales | comparación de silueta, transparencia/clipping, tiempo GPU y FPS reales Android |

**Nota:** el blazer se **prototipa primero**, pero las piezas se terminan y ajustan juntas para verificar superposiciones.

### 5. Reglas de construcción y deformación
1. Base anatómica v1 conservada en archivo separado. Hacer copias de trabajo: nunca aplicar Decimate o booleans destructivos a la fuente original.
2. Ropa por retopología/modelado sobre la silueta **sin exponer todo el cuerpo debajo**. Usar máscara no destructiva o malla `Body_Visible` para reducir superficie oculta; conservar manos, cuello y cabeza.
3. Mantener una holgura visual controlada para impedir clipping. En zona de blazer abierto, camisa y faldón deben coexistir con espesor creíble, sin geometría solapada visible.
4. Transferir pesos al rig existente y corregir manualmente shoulder/upperarm, elbow/forearm, pelvis, knee, ankle. Comprobar nombres de huesos en archivo real: no asumir `hand.L` (la fase 2 no pudo resolver manos/muñeca).
5. Si el faldón del blazer se deforma mal, considerar huesos auxiliares o shape keys compatibles con Godot; registrar sus costos, no añadir por defecto.
6. UV sin solapamientos inintencionales; texturas solo con licencia verificada. Materiales PBR compatibles con Godot 4.3 / Mobile/Compatibility (Base Color, Roughness, Metallic, Normal cuando aporte valor).
7. Mantener coherencia de escala y ejes entre Blender y Godot, con inspección visual del import antes de cualquier integración al proyecto jugable.

### 6. Presupuesto de rendimiento (orientativo, NO validado)
- El cuerpo actual completo cuesta **109.064 tris**; LOD40 cuerpo candidato **43.625 tris**. Ninguno constituye todavía presupuesto final del personaje vestido.
- Antes de agregar ropa registrar **triángulos por pieza**, draw calls, número de materiales, huesos influyentes y tamaño de texturas; medir todo después de exportar/reimportar.
- Objetivo de diseño inicial, sujeto a benchmark: **una sola familia de materiales compartidos cuando sea posible**, texturas comprimibles, detalles secundarios simples y máximo aprovechamiento de la malla oculta. **No imponer cifras definitivas de triángulos sin prueba en dispositivos objetivo.**
- Validar LOD de cerca y desde la cámara de juego: dedos, nariz, ojos, hombros y articulaciones son áreas críticas. Una simplificación que los destruya se rechaza aunque baje triángulos.
- Los benchmarks deben incluir escenas con iluminación, animación, arma y NPC, no solo una malla inmóvil en visor.

### 7. Protocolo mínimo de QA artístico y técnico
- Renders desde geometría Blender real: frontal, lateral, posterior y tres cuartos, **más acercamientos verdaderos** a cara, ambas manos, cuello/hombros, codos, cintura, rodillas y calzado; versión con wireframe.
- Poses capturadas antes/después: A-pose, apuntar con ambos brazos, giro de torso, carrera, crouch/agacharse, flexión codo y rodilla, muñeca y agarre de arma. Documentar clipping, autointersección, hundimientos y deformación de ropa.
- Verificación automatizada: `.blend` abre sin errores; `.glb` tiene cabecera válida; reimporta en Blender; Godot 4.3 reporta MeshInstance3D y Skeleton3D; escala 1,84m; ningún mesh de control en export; licencias registradas.
- Verificación humana: aprobar frontal, perfil, espalda, cara y manos **antes** de optimización final. Pruebas de rig automáticas NO equivalen a aprobación visual.
- Android físico: FPS y estabilidad en dispositivos objetivos, con captura de ajustes gráficos, resolución, consumo de memoria y escena de prueba; ausencia de dispositivo significa **rendimiento pendiente**.

### 8. Entregables esperados (NO generados por este plan)
```
character_assets/el_cuervo/fase3/
  El_Cuervo_Vestuario_WIP.blend
  El_Cuervo_Vestuario_CANDIDATO.glb
  renders/...
  PIEZAS_MATERIALES_TRIANGULOS.json
  AUDITORIA_VESTUARIO.md
  LICENCIAS.md
```
No se aceptan screenshots genéricos, renders IA fingiendo ser 3D, ni meshes hechos con primitivas como sustitutos de ropa anatómica. Todo render debe provenir del modelo 3D realmente producido.

### 9. Puertas de aprobación (go / no-go)
- **G0:** base v1 y rig/documentación disponibles; paleta, patrón y silueta aceptados.
- **G1:** blazer y camisa con geometría real en archivos editables + vistas verificadas.
- **G2:** pantalón, botines, cinturón y funda coherentes, UV y materiales completos.
- **G3:** pesos y clipping auditados con secuencia de poses, incluida muñeca/manos.
- **G4:** GLB importado en Godot 4.3, costos medidos y rendimiento real probado en Android.
- **G5:** aprobación artística explícita; **solo después** estudiar integrar al protagonista jugable con respaldo y PR independiente.

### 10. Próxima acción concreta
**Construir en Blender un primer bloque visual real de blazer + camisa** sobre una copia del BLEND v1, registrar versiones y mostrar sus capturas frontales/laterales/espalda. No anunciar “traje completo” antes de que existan esos archivos y su validación.
