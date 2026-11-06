"""El Cuervo Fase 2: inspeccion real de anatomia, pruebas de pose y LOD candidato.
Blender 4.3: blender -b --python tools/el_cuervo/fase2_review.py -- --blend ...v1.blend --out .../fase2
NO reemplaza personaje, NO aprueba rig ni rendimiento Android.
"""
import bpy, sys, os, json, math, struct
from mathutils import Vector

def arg(name):
    a = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return a[a.index(name)+1]

src=os.path.abspath(arg("--blend"))
out=os.path.abspath(arg("--out"))
assert os.path.isfile(src), "Falta el BLEND v1 validado"
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
scene=bpy.context.scene
arms=[x for x in scene.objects if x.type=="ARMATURE"]
assert len(arms)==1,"Se esperaba exactamente un esqueleto humano"
arm=arms[0]
meshes=[x for x in scene.objects if x.type=="MESH" and
        (x.parent==arm or any(m.type=="ARMATURE" and m.object==arm for m in x.modifiers))]
assert len(meshes)>=1 and sum(len(m.data.vertices) for m in meshes)>10000
bpy.context.view_layer.update()

def tris(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)
def bound():
    p=[o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    return [min(x[i] for x in p) for i in range(3)],[max(x[i] for x in p) for i in range(3)]
lo,hi=bound()
height=hi[2]-lo[2]
assert abs(height-1.84)<0.015, "Altura base inesperada"
cx=(lo[0]+hi[0])/2
cy=(lo[1]+hi[1])/2

cam=scene.camera
assert cam is not None,"Falta la camara del estudio"
cam.data.type="ORTHO"
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=12
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.render.resolution_x=720
scene.render.resolution_y=720

def render(name,target,offset,scale,portrait=False):
    cam.data.ortho_scale=scale
    scene.render.resolution_x=640 if portrait else 720
    scene.render.resolution_y=880 if portrait else 720
    t=Vector(target)
    cam.location=t+Vector(offset)
    cam.rotation_euler=(t-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>3000, "Render vacio: "+name

# Vistas de detalle genuinas de la malla, no imagenes generativas.
# Localizar manos en los huesos reales; un fallback aproxima la region,
# y queda marcado como tal en el manifiesto.
def bone_target(key,side):
    side=side.lower()
    candidates=[b for b in arm.pose.bones if key in b.name.lower() and
                (b.name.lower().endswith("."+side) or b.name.lower().endswith("_"+side))]
    if not candidates:
        candidates=[b for b in arm.pose.bones if key in b.name.lower()]
    if candidates:
        return tuple(arm.matrix_world @ candidates[0].head),candidates[0].name
    return None,None

hand_l,hand_l_bone=bone_target("hand","l")
hand_r,hand_r_bone=bone_target("hand","r")
shoulder,shoulder_bone=bone_target("upperarm","l")
knee,knee_bone=bone_target("lowerleg","l")
if knee is None: knee,knee_bone=bone_target("shin","l")
face=(cx,cy,lo[2]+height*.90)
render("01_Rostro_Cuello",face,(0,-2.5,.06),.51)
render("02_Perfil_Rostro",face,(2.5,0,.02),.51)
for name,pos,source in [
    ("03_Mano_Izquierda",hand_l,hand_l_bone),
    ("04_Mano_Derecha",hand_r,hand_r_bone),
    ("05_Hombro",shoulder,shoulder_bone),
    ("06_Rodilla",knee,knee_bone),
]:
    if pos is None:
        print("DIAGNOSTIC_VIEW_SKIPPED",name,"bone not found",flush=True)
        continue
    render(name,pos,(0,-2.5,.18),.49)

# Se cuantifica el movimiento de vertices skinned, sin afirmar que
# la articulacion haya quedado biomecanicamente bien deformada.
def posed_verts():
    deps=bpy.context.evaluated_depsgraph_get()
    result=[]
    for obj in meshes:
        ev=obj.evaluated_get(deps)
        me=ev.to_mesh()
        step=max(1,len(me.vertices)//1200)
        result.extend(obj.matrix_world @ me.vertices[i].co for i in range(0,len(me.vertices),step))
        ev.to_mesh_clear()
    return result

pose_specs=[
    ("07_Pose_Hombro",["upperarm"],"l",0.40),
    ("08_Pose_Codo",["forearm","lowerarm"],"l",0.55),
    ("09_Pose_Rodilla",["lowerleg","shin","calf"],"l",0.50),
    ("10_Pose_Muneca",["hand"],"l",0.40),
]
tests=[]
before=posed_verts()
for name,terms,side,angle in pose_specs:
    bone=None
    for term in terms:
        _,bname=bone_target(term,side)
        if bname:bone=arm.pose.bones[bname];break
    if bone is None:
        tests.append({"view":name,"executed":False,"reason":"hueso no encontrado"})
        continue
    old_mode=bone.rotation_mode
    bone.rotation_mode="XYZ"
    old=bone.rotation_euler.copy()
    bone.rotation_euler.x+=angle
    bpy.context.view_layer.update()
    after=posed_verts()
    delta=max(((a-b).length for a,b in zip(after,before)),default=0)
    render(name,(cx,cy,lo[2]+height*.51),(2.7,-3.8,.3),2.35,portrait=True)
    tests.append({"view":name,"executed":True,"bone":bone.name,"test_rotation_degrees":round(math.degrees(angle),1),
                  "max_sample_displacement_m":round(delta,6),
                  "skin_moves":delta>.001,"visual_deformation_approved":False})
    bone.rotation_euler=old
    bone.rotation_mode=old_mode
    bpy.context.view_layer.update()
assert all(t.get("skin_moves",False) for t in tests if t["executed"]),"Una prueba de pose no desplazo la piel"

# Candidato LOD conservando esqueleto, pesos, materiales y el original intacto.
# Decimate se aplica ANTES del modificador Armature para no hornear poses.
original_tris=sum(tris(o) for o in meshes)
lods=[]
for srcmesh in meshes:
    dup=srcmesh.copy()
    dup.data=srcmesh.data.copy()
    dup.name="LOD40_"+srcmesh.name
    scene.collection.objects.link(dup)
    dup.matrix_world=srcmesh.matrix_world.copy()
    bpy.ops.object.select_all(action="DESELECT")
    dup.select_set(True)
    bpy.context.view_layer.objects.active=dup
    modifier=dup.modifiers.new("LOD40_reduccion_candidata","DECIMATE")
    modifier.ratio=.40
    # subir antes de Armature; Blender mantiene pesos por interpolacion.
    for _ in range(len(dup.modifiers)-1):
        bpy.ops.object.modifier_move_up(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    assert len(dup.vertex_groups)>0,"LOD perdio los grupos de pesos"
    lods.append(dup)
low_tris=sum(tris(x) for x in lods)
assert 10000<low_tris<original_tris*.65,(original_tris,low_tris)
bpy.context.view_layer.update()

# Seleccionar solamente el rig y los objetos LOD.
# GLB no debe contener el cuerpo original de 109k tris.
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for ob in lods: ob.select_set(True)
bpy.context.view_layer.objects.active=arm
glb=os.path.join(out,"El_Cuervo_LOD40_CANDIDATO.glb")
bpy.ops.export_scene.gltf(filepath=glb,export_format="GLB",use_selection=True,
                          export_materials="EXPORT",export_yup=True)
with open(glb,"rb") as f:
    header=f.read(12)
    magic,version,size=struct.unpack("<4sII",header)
    assert magic==b"glTF" and version==2 and size==os.path.getsize(glb)
    chunk_size,chunk_kind=struct.unpack("<I4s",f.read(8))
    assert chunk_kind==b"JSON"
    gltf=json.loads(f.read(chunk_size).decode("utf-8"))
nodes=[n for n in gltf["nodes"] if "mesh" in n]
assert nodes and all(n.get("name","").startswith("LOD40_") for n in nodes),nodes
assert all("skin" in n for n in nodes),"LOD sin esqueleto"
assert sum(len(s.get("joints",[])) for s in gltf.get("skins",[]))>=100
result={
 "source_blend":"El_Cuervo_Base_Humana_v1.blend",
 "original_triangles_blender":original_tris,
 "lod40_triangles_blender":low_tris,
 "reduction_percent":round(100*(1-low_tris/original_tris),2),
 "lod_glb":os.path.basename(glb),
 "lod_glb_mesh_nodes":[n.get("name") for n in nodes],
 "lod_glb_skinned":True,
 "lod_visual_approved":False,
 "android_fps_measured":False,
 "face_and_hands_visual_approved":False,
 "pose_checks":tests,
 "closeup_bone_mapping":{"left_hand":hand_l_bone,"right_hand":hand_r_bone,"shoulder":shoulder_bone,"knee":knee_bone},
 "note":"LOD experimental. No integrar al juego hasta inspeccionar rostro, manos, deformaciones y FPS en Android real."
}
with open(os.path.join(out,"Fase2_Auditoria.json"),"w",encoding="utf-8") as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print("FASE2_COMPLETE",json.dumps(result,ensure_ascii=False),flush=True)
