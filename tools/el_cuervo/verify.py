"""Auditoria automática independiente Blender 4.3 de los dos archivos producidos."""
import bpy,os,sys,json,struct
from mathutils import Vector
def arg(flag):
    a=sys.argv[sys.argv.index("--")+1:]
    return a[a.index(flag)+1]
out=arg("--out")
p=os.path.join(out,"El_Cuervo_Base_Humana_v1")
glb=p+".glb"
blend=p+".blend"
assert os.path.isfile(blend) and os.path.isfile(glb)
with open(glb,"rb") as f:
    h=f.read(12)
magic,version,length=struct.unpack("<4sII",h)
assert magic==b"glTF" and version==2 and length==os.path.getsize(glb)
bpy.ops.wm.open_mainfile(filepath=blend)
bm=[o for o in bpy.data.objects if o.type=="MESH" and o.name.startswith("AUDITORIA")==False]
ba=[o for o in bpy.data.objects if o.type=="ARMATURE"]
assert bm and ba
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
arms=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
assert meshes and arms
bpy.context.view_layer.update()
for o in meshes:
    corners=[o.matrix_world @ Vector(p) for p in o.bound_box]
    print("VERIFY_MESH",o.name,"verts",len(o.data.vertices),"height",max(q.z for q in corners)-min(q.z for q in corners),"min_z",min(q.z for q in corners),"max_z",max(q.z for q in corners),"parent",o.parent.name if o.parent else None,flush=True)
print("VERIFY_ALL_OBJECTS",[(o.name,o.type) for o in bpy.context.scene.objects],flush=True)
pts=[o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
minz=min(p.z for p in pts); maxz=max(p.z for p in pts)
height=maxz-minz
assert abs(height-1.84)<0.015, "La exportacion cambio la escala: "+str(height)
v=sum(len(o.data.vertices) for o in meshes)
t=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
nb=sum(len(a.data.bones) for a in arms)
assert v>1000 and t>2000 and nb>0
d={"blend_opened":True,"glb_binary_structure_valid":True,"glb_reimported_in_blender":True,"glb_height_m":height,"glb_triangles":t,"glb_vertices":v,"glb_bones":nb,"glb_materials":len(set(m.name for o in meshes for m in o.data.materials if m)),"godot_4_3_import_verified":False,"artistic_human_review_approved":False}
with open(os.path.join(out,"El_Cuervo_Verificacion.json"),"w") as f:json.dump(d,f,indent=2)
print("CUERVO_VERIFICATION_COMPLETED",json.dumps(d))
