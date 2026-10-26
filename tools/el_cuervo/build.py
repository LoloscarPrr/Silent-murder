"""
Silent Killer - El Cuervo Fase 1
Produce un personaje a partir de una malla CC0 existente, nunca desde primitivas.
Ejecutar con Blender 4.3:
 blender -b --python tools/el_cuervo/build.py -- --source source.glb --out output
"""
import bpy
import sys
import os
import json
import math
from datetime import datetime, timezone
from mathutils import Vector

def arg(name, default=None):
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return a[a.index(name)+1] if name in a else default

src=arg("--source")
out=os.path.abspath(arg("--out","output"))
assert src and os.path.isfile(src), "GLB original no encontrado"
os.makedirs(out,exist_ok=True)
basename="El_Cuervo_Base_Humana_v1"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
imported=list(bpy.context.scene.objects)
arms=[o for o in imported if o.type=="ARMATURE"]
assert arms, "La fuente no contiene armature"
# La fuente incluye una Icosphere aislada para visualización. NO es anatomía.
# Solo conservamos los objetos de malla enlazados efectivamente al esqueleto.
mesh_candidates=[o for o in imported if o.type=="MESH"]
meshes=[o for o in mesh_candidates if (o.parent in arms or any(mod.type=="ARMATURE" and mod.object in arms for mod in o.modifiers))]
excluded=[o for o in mesh_candidates if o not in meshes]
for o in excluded:
    print("EXCLUDED_SOURCE_HELPER",o.name,"verts",len(o.data.vertices),"reason","not skinned or parented to human rig",flush=True)
    bpy.data.objects.remove(o,do_unlink=True)
imported=list(bpy.context.scene.objects)
assert meshes, "La fuente no contiene malla humana unida al esqueleto"
roots=[o for o in imported if o.parent is None]
assert roots, "No se encontraron raices de jerarquia"

def bounds(objects):
    p=[o.matrix_world @ Vector(corner) for o in objects for corner in o.bound_box]
    return tuple(min(v[i] for v in p) for i in range(3)),tuple(max(v[i] for v in p) for i in range(3))

bpy.context.view_layer.update()
low,high=bounds(meshes)
initial_height=high[2]-low[2]
print("SOURCE_WORLD_BOUNDS", low, high, "HEIGHT", initial_height, flush=True)
for o in meshes:
    p=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    zz=[v.z for v in p]
    print("SOURCE_MESH_OBJECT",o.name,"verts",len(o.data.vertices),"faces",len(o.data.polygons),"Z",round(min(zz),5),round(max(zz),5),"dimensions",tuple(round(n,5) for n in o.dimensions),"parent",o.parent.name if o.parent else None,flush=True)
print("SOURCE_RIGS",[(x.name,len(x.data.bones)) for x in arms],flush=True)
assert initial_height>0.8 and initial_height<3.6, "La altura inicial está fuera de límites de diagnóstico: "+str(initial_height)
scale=1.84/initial_height
for obj in roots:
    obj.scale=tuple(x*scale for x in obj.scale)
bpy.context.view_layer.update()
low,high=bounds(meshes)
for obj in roots:
    obj.location.z-=low[2]
bpy.context.view_layer.update()
low,high=bounds(meshes)
height=high[2]-low[2]
assert abs(height-1.84)<0.005, "Falló el escalado a 1,84m: "+str(height)

# Conservamos la topología y pesos originales; no se aplica decimate ni
# remeshing automático sin inspección manual de rostro, manos y articulaciones.
original_materials={o.name: [m for m in o.data.materials] for o in meshes}
for o in meshes:
    for poly in o.data.polygons:
        poly.use_smooth=True

def poly_stats():
    return {
        "mesh_objects":len(meshes),
        "vertices":sum(len(o.data.vertices) for o in meshes),
        "edges":sum(len(o.data.edges) for o in meshes),
        "faces":sum(len(o.data.polygons) for o in meshes),
        "triangles":sum(sum(len(face.vertices)-2 for face in o.data.polygons) for o in meshes),
        "armatures":len(arms),
        "bones":sum(len(a.data.bones) for a in arms),
        "materials":len(set(m.name for o in meshes for m in o.data.materials if m)),
        "all_imported_objects":len(imported),
        "mesh_object_names":[o.name for o in meshes],
        "height_m":round(height,5),
        "width_m":round(high[0]-low[0],5),
        "depth_m":round(high[1]-low[1],5)
    }

stats=poly_stats()
stats["original_import_height_m"]=round(initial_height,5)
stats["source_helpers_excluded"]=[o.name for o in excluded]
stats["scale_factor_applied"]=round(scale,6)
rig_tests=[]
for arm in arms:
    influenced=[m for m in meshes if any(mod.type=="ARMATURE" and mod.object==arm for mod in m.modifiers)]
    weights=sum(sum(1 for v in m.data.vertices if len(v.groups)) for m in influenced)
    candidates=[b for b in arm.pose.bones if any(k in b.name.lower() for k in ("forearm","lowerarm","upperarm","thigh","shin"))]
    test={"armature":arm.name,"skinned_meshes":len(influenced),"weighted_vertices":weights,"pose_deformation_verified":False}
    if candidates and influenced and weights:
        b=candidates[0]
        m=influenced[0]
        indices=list(range(0,len(m.data.vertices),max(1,len(m.data.vertices)//600)))
        deps=bpy.context.evaluated_depsgraph_get()
        em=m.evaluated_get(deps).to_mesh()
        before=[(m.matrix_world @ em.vertices[i].co).copy() for i in indices if i<len(em.vertices)]
        m.evaluated_get(deps).to_mesh_clear()
        b.rotation_mode="XYZ"
        prior=b.rotation_euler.copy()
        b.rotation_euler.x+=0.25
        bpy.context.view_layer.update()
        deps=bpy.context.evaluated_depsgraph_get()
        em=m.evaluated_get(deps).to_mesh()
        after=[(m.matrix_world @ em.vertices[i].co).copy() for i in indices if i<len(em.vertices)]
        m.evaluated_get(deps).to_mesh_clear()
        test["bone_tested"]=b.name
        test["max_sample_displacement_m"]=round(max((x-y).length for x,y in zip(after,before)),6) if before and after else 0
        test["pose_deformation_verified"]=test["max_sample_displacement_m"]>0.0001
        b.rotation_euler=prior
        bpy.context.view_layer.update()
    rig_tests.append(test)

stats["rig_tests"]=rig_tests
stats["visual_quality_approved"]=False
stats["android_performance_approved"]=False
stats["source"]="Innerscene / MakeHuman CC0"
stats["source_url"]="https://www.innerscene.com/tools/library/3d-parts/male-base-mesh-3d-person-rigged-a-pose-380e6d89"

# Estudios de iluminación neutral usando una escena REAL de Blender.
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=16
scene.cycles.use_denoising=True
scene.render.resolution_x=768
scene.render.resolution_y=1024
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
world=bpy.data.worlds.new("Estudio gris neutro")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.30,0.31,0.33,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.7
for name,xyz,energy,size in [
    ("Area principal",(-2.8,-3.6,4.3),750,4.0),
    ("Area relleno",(2.9,-1.0,2.7),420,3.8),
    ("Area posterior",(1.1,3.5,3.6),620,3.2)
]:
    light=bpy.data.lights.new(name,"AREA")
    light.energy=energy
    light.shape="DISK"
    light.size=size
    obj=bpy.data.objects.new(name,light)
    scene.collection.objects.link(obj)
    obj.location=xyz
    direction=Vector((0,0,1))-obj.location
    obj.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
cam_data=bpy.data.cameras.new("Camara de evaluacion")
cam=bpy.data.objects.new("Camara de evaluacion",cam_data)
scene.collection.objects.link(cam)
scene.camera=cam
cam.data.type="ORTHO"
cam.data.ortho_scale=2.48
target=Vector(((low[0]+high[0])/2,(low[1]+high[1])/2,0.94))
centerx,centery=target[0],target[1]
def render_view(name,offset):
    cam.location=target+Vector(offset)
    direction=target-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>1000, "Render vacio "+name

render_view("01_Frontal",(0,-4,0.16))
render_view("02_Lateral",(4,0,0.16))
render_view("03_Posterior",(0,4,0.16))
render_view("04_Tres_Cuartos",(3,-4,0.18))

# Topología real: material wireframe sobre la malla importada, sin retopología inventada.
wiremat=bpy.data.materials.new("AUDITORIA_WIREFRAME")
wiremat.use_nodes=True
nodes=wiremat.node_tree.nodes
nodes.clear()
outnode=nodes.new("ShaderNodeOutputMaterial")
mix=nodes.new("ShaderNodeMixShader")
wire=nodes.new("ShaderNodeWireframe")
wire.use_pixel_size=True
wire.inputs["Size"].default_value=0.65
grey=nodes.new("ShaderNodeBsdfDiffuse")
grey.inputs["Color"].default_value=(0.61,0.64,0.68,1)
dark=nodes.new("ShaderNodeBsdfDiffuse")
dark.inputs["Color"].default_value=(0.02,0.025,0.03,1)
ln=wiremat.node_tree.links
ln.new(wire.outputs["Fac"],mix.inputs[0])
ln.new(grey.outputs[0],mix.inputs[1])
ln.new(dark.outputs[0],mix.inputs[2])
ln.new(mix.outputs[0],outnode.inputs["Surface"])
for m in meshes:
    m.data.materials.clear()
    m.data.materials.append(wiremat)
cam.data.ortho_scale=2.2
render_view("05_Topologia",(0,-4,0.16))

# Restaurar TODOS los materiales originales. Evitar incluir auditoria en el GLB.
for m in meshes:
    m.data.materials.clear()
    for mat in original_materials[m.name]:
        if mat:
            m.data.materials.append(mat)
cam.data.ortho_scale=2.48
render_view("06_Manos_y_Rostro",(1.9,-2.4,0.9))
bpy.ops.file.pack_all()

blend_path=os.path.join(out,basename+".blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

bpy.ops.object.select_all(action="DESELECT")
for obj in imported:
    obj.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
glb_path=os.path.join(out,basename+".glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path, export_format="GLB",use_selection=True,
    export_materials="EXPORT",export_yup=True
)
assert os.path.getsize(blend_path)>10000
assert os.path.getsize(glb_path)>10000
with open(glb_path,"rb") as f:
    assert f.read(4)==b"glTF", "Cabecera GLB incorrecta"

with open(os.path.join(out,"El_Cuervo_Datos_Tecnicos.json"),"w",encoding="utf-8") as f:
    json.dump(stats,f,ensure_ascii=False,indent=2)
with open(os.path.join(out,"El_Cuervo_Informe_Tecnico.txt"),"w",encoding="utf-8") as f:
    f.write("SILENT KILLER — EL CUERVO / FASE 1\n")
    f.write("Fuente: Innerscene / MakeHuman (CC0)\n")
    f.write("Altura verificable: %.4f m\n"%height)
    for k,v in stats.items():
        f.write(str(k)+": "+str(v)+"\n")
    f.write("\nSin aprobación artística ni evaluación real de FPS Android.\n")
    f.write("Pose test automática: deformación geométrica no equivale a rig listo para producción.\n")
print("CUERVO_BUILD_COMPLETED",json.dumps(stats,ensure_ascii=False))
