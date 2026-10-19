# Silent Murder — Alpha 0.2: criterios de aceptación

**El APK compila** no significa que la experiencia en el teléfono ya esté aprobada.

1. El workflow importa el proyecto, arranca la escena sin errores de GDScript y exporta un APK Android arm64.
2. Inicia en horizontal mostrando el depósito y el protagonista articulado.
3. Joystick izquierdo permite movimiento analógico; al soltar frena suavemente.
4. Giro de cámara táctil con otro dedo a la vez que se camina.
5. CORRER acelera sin saltos de movimiento.
6. AGACHAR modifica velocidad, altura visual y colisión; levantarse no debe atravesar obstáculos.
7. APUNTAR acerca la cámara sin activar disparos ficticios.
8. Cerca de paredes, la cámara acorta distancia para evitar atravesarlas.
9. FPS visibles en HUD, tomar observaciones en el Redmi 12 5G.
10. Mantener el juego abierto varios minutos, explorar esquinas y verificar que no cierre.

### Fuera de alcance de 0.2

Enemigos, IA, armas, disparos, ejecuciones, mallas humanoides definitivas y animaciones capturadas con rig.

### Actualizaciones APK

La versión se incrementó a versionCode 2. Las actualizaciones directas requieren **idéntico package ID e idéntica firma**. La firma debug del contenedor debe verificarse antes de prometer actualizaciones sin desinstalación. Para releases estables, configurar keystore persistente como secreto.
