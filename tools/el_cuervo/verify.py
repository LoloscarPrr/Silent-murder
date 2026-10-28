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
with open(glb,"rb") as q:
    q.seek(12)
    jsonlen,kind=struct.unpack("<I4s",q.read(8))
    assert kind==b"JSON"
    raw_json=json.loads(q.read(jsonlen).decode("utf-8"))
print("VERIFY_GLB_JSON_NODES",[(x.get("name"),x.get("mesh")) for x in raw_json.get("nodes",[])],flush=True)
print("VERIFY_GLB_JSON_SCENES",raw_json.get("scenes"),flush=True)
bpy.ops.wm.open_mainfile(filepath=blend)
bm=[o for o in bpy.data.objects if o.type=="MESH" and o.name.startswith("AUDITORIA")==False]
ba=[o for o in bpy.data.objects if o.type=="ARMATURE"]
assert bm and ba
bpy.ops.wm.read_factory_settings(use_empty=True)
print("VERIFY_AFTER_FACTORY_RESET",[(o.name,o.type) for o in bpy.context.scene.objects],flush=True)
bpy.ops.import_scene.gltf(filepath=glb)
# El JSON glTF define la escena exportada. Blender puede crear helpers al importar;
# esos objetos no son parte del GLB si no tienen un nodo de malla glTF.
source_mesh_nodes=[n for n in raw_json.get("nodes",[]) if "mesh" in n]
assert len(source_mesh_nodes)>=1
expected_mesh_names={n["name"] for n in source_mesh_nodes}
assert not any("icosphere" in s.lower() for s in expected_mesh_names), "GLB exportado incluye una Icosphere, no permitido"
assert len(raw_json.get("scenes",[]))>=1 and len(raw_json["scenes"][0]["nodes"])>=1
all_imported_meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
meshes=[o for o in all_imported_meshes if o.name in expected_mesh_names]
import_side_effects=[o.name for o in all_imported_meshes if o.name not in expected_mesh_names]
print("VERIFY_UNREFERENCED_IMPORT_OBJECTS",import_side_effects,flush=True)
assert {o.name for o in meshes}==expected_mesh_names, "No coinciden los nodos de malla reales del GLB con los importados"
assert all(n.get("skin") is not None for n in source_mesh_nodes), "Mallas sin skinning en el GLB exportado"
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
d={"blend_opened":True,"glb_binary_structure_valid":True,"glb_reimported_in_blender":True,"glb_height_m":height,"glb_mesh_nodes":[n["name"] for n in source_mesh_nodes],"blender_import_extra_objects":import_side_effects,"glb_triangles":t,"glb_vertices":v,"glb_bones":nb,"glb_materials":len(set(m.name for o in meshes for m in o.data.materials if m)),"godot_4_3_import_verified":False,"artistic_human_review_approved":False}
with open(os.path.join(out,"El_Cuervo_Verificacion.json"),"w") as f:json.dump(d,f,indent=2)
print("CUERVO_VERIFICATION_COMPLETED",json.dumps(d))
