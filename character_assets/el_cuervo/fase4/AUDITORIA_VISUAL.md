# EL CUERVO — Auditoría visual de Fase 4 (2026-10-27)
  
**Origen de las imágenes:** renders auténticos realizados por Blender 4.3.2 sobre el archivo `El_Cuervo_Refinado_Fase4_WIP.blend`. Se revisaron la vista frontal A-pose, los brazos bajos, el acercamiento a la chaqueta y el calzado. **No está aprobado como personaje definitivo.**

## Avances comprobados
- Vestuario: geometría auténtica de traje formal de Margaret Toigo (MakeHuman Suits01, CC0) en lugar de cilindros sintéticos.
- Anatomía humana original intacta; 1,84 m; rig de 163 huesos preservado.
- Camisa/parte interior reclasificada a un material grafito oscuro usando 737 caras reales y el atlas UV existente.
- 563 vértices del área de hombros y 584 del área de cintura ajustados mediante una deformación suave de la malla del traje.
- Botines masculinos reales `toigo_ankle_boots_male` (Shoes01, CC0) importados como geometría 3D, 4.120 triángulos y pesos automáticos de deformación.
- Vistas con brazos bajos: flexión de hombros simétrica ensayada con muñecas más cerca del cuerpo; pose de prueba, no animación exportada.
- GLB reimportado en Blender y como `Skeleton3D` + `MeshInstance3D` en Godot 4.3. **No** se integró el personaje al juego.
- Renderizado visible total informado: **82.454 triángulos**; no constituye rendimiento Android validado.

## Defectos que todavía se ven
1. Mangas/cuffs: abertura oscura demasiado grande; manos parecen separadas de la tela en algunas poses. Revisar escala local de puños, pesos del antebrazo y compatibilidad con brazos al costado.
2. Hombros: la silueta mejoró en A-pose, pero continúa algo rígida; no tiene costura de manga/hombro natural de traje bien entallado.
3. Tela: superficies del torso y pantalón siguen muy lisas, con detalle de textura insuficiente; cuidado con añadir más geometría solo para simular arrugas.
4. Botines: el modelo es auténtico y tapa los pies, pero tiene un tacón y caña marcados; evaluar una variante de perfil más bajo y unión limpia pantalón-botín.
5. En la pose de brazos bajos la deformación se consiguió moviendo huesos, pero todavía no se validó articulación codo/muñeca, dedos, apuntado o marcha.
6. Materiales: la camisa cambió a grafito, pero la jerarquía entre negro de blazer y camisa aún requiere inspección desde la cámara de juego.
7. Rendimiento: se mantienen decenas de miles de triángulos en piel visible y vestuario; sin LOD de personaje vestido ni medición FPS Android.

## Próxima iteración recomendada
Priorizar **puños + brazos + silueta de hombros** mediante pesos y ajuste localizado sobre prendas auténticas. Después probar dos poses de apuntado y agacharse, y solamente entonces pasar a cabello/rostro y LOD Android.

**Puertas de aprobación:** Arte pendiente, animación pendiente, FPS Android pendiente. Mantener `main` y la APK sin cambios.
