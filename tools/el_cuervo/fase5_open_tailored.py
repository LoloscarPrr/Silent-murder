"""SILENT KILLER / EL CUERVO — FASE 5: open tailored blazer, separate fitted shirt
and anatomy-based sleeve shaping on REAL Margaret Toigo CC0 suit mesh.
Input: already verified Phase4 .blend. No primitives used for clothing.
Requires Blender 4.3. Distinct WIP, no game modifications.

blender -b --python tools/el_cuervo/fase5_open_tailored.py -- \
 --blend character_assets/el_cuervo/fase4/El_Cuervo_Refinado_Fase4_WIP.blend \
 --out character_assets/el_cuervo/fase5
"""
import bpy, bmesh, os, sys, math, json, struct
from mathutils import Vector
from mathutils.kdtree import KDTree
def arg(name):
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    assert name in a, "Missing "+name
    return a[a.index(name)+1]
src=os.path.abspath(arg("--blend"));out=os.path.abspath(arg("--out"))
assert os.path.isfile(src),"Fase4 verified BLEND absent"
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
scene=bpy.context.scene
armatures=[o for o in scene.objects if o.type=="ARMATURE"]
assert len(armatures)==1,"Original rig must not be replaced"
rig=armatures[0]
full=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("base_male_body")]
skin=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("VisibleSkin_")]
suits=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("CC0_toigo_male_suit_3")]
boots=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("Cuervo_Botin_CC0")]
assert full and skin and len(suits)==1 and boots,([x.name for x in full],[x.name for x in skin],suits,boots)
suit=suits[0]
def bb(objects):
    coords=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return Vector(tuple(min(p[k] for p in coords) for k in range(3))),Vector(tuple(max(p[k] for p in coords) for k in range(3)))
lo,hi=bb(full)
H=hi.z-lo.z
assert abs(H-1.84)<.02,H
cx=(lo.x+hi.x)*.5
cy=(lo.y+hi.y)*.5
def tris(ob):return sum(len(p.vertices)-2 for p in ob.data.polygons)
def smooth(a,b,x):
    v=max(0.,min(1.,(x-a)/(b-a)))
    return v*v*(3-2*v)
def band(x,l0,l1,r0,r1):
    return smooth(l0,l1,x)*(1-smooth(r0,r1,x))
report={"source_blend":os.path.basename(src),"original_CC0_suit":suit.name,
        "suit_source_license":"Margaret Toigo MakeHuman Community suits01 CC0",
        "rig_bones":len(rig.data.bones),"height_m":H,
        "previous_suit_tris":tris(suit)}
# Identify independent REAL garment pattern islands by mesh connectivity. 
# Unlike previous cylindrical modeling, change the original hand-modeled garment.
bm=bmesh.new();bm.from_mesh(suit.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
visited=set()
components=[]
matrix=suit.matrix_world.copy()
inverse=matrix.inverted()
for first in bm.faces:
    if first in visited:continue
    stack=[first];group=[]
    while stack:
        f=stack.pop()
        if f in visited:continue
        visited.add(f);group.append(f)
        for v in f.verts:
            stack.extend(q for q in v.link_faces if q not in visited)
    verts=set(v for f in group for v in f.verts)
    world=[matrix@v.co for v in verts]
    mn=Vector(tuple(min(p[k] for p in world) for k in range(3)))
    mx=Vector(tuple(max(p[k] for p in world) for k in range(3)))
    components.append({"faces":group,"verts":verts,"count":len(group),
      "x":(mn.x+mx.x)*.5,"y":(mn.y+mx.y)*.5,"z":(mn.z+mx.z)*.5,
      "bounds_min":mn,"bounds_max":mx})
# Source garment is ONE 4k-face connected coat (front/back/sleeves).
# Its authored shirt and trousers are separate islands, while the jacket
# panels are NOT separate components. Tailor them regionally by geometric
# position; do not mistake material boundaries for disconnected meshes.
main=max(components,key=lambda c:c["count"])
assert main["count"]>3000,("Source coat topology unexpected",main["count"])
report["original_coat_component_faces"]=main["count"]
report["source_component_count"]=len(components)
report["source_top_component_face_counts"]=sorted((c["count"] for c in components),reverse=True)[:10]

# The source jacket is a single connected CC0 artist-modeled garment.
# Do NOT translate central vertices (that creates a balloon/elastic front).
# Instead physically open its *front fabric* by removing a tapered wedge of
# front-facing authored jacket faces. The real, skinned shirt remains beneath.
main=max(components,key=lambda c:c["count"])
assert main["count"]>3000,("Expected authored CC0 jacket front/back",main["count"])
report["original_coat_component_faces"]=main["count"]
report["source_component_count"]=len(components)
# Avoid removing the underlying artist-made collar or trousers: only
# faces in the large jacket component.
cutfaces=[]
cut_left=cut_right=0
for face in main["faces"]:
    p=[matrix@v.co for v in face.verts]
    avg=sum(p,Vector())/len(p)
    height=avg.z-lo.z
    if not (1.00<height<1.51):
        continue
    # Source back wall is Y-positive. The true exterior jacket chest is
    # front-facing negative-Y, measured independently from the real GLB.
    if avg.y>=cy-.058:
        continue
    gap_half=.035+.135*(1-smooth(1.30,1.52,height))
    if abs(avg.x-cx)<gap_half:
        cutfaces.append(face)
        if avg.x<cx:cut_left+=1
        else:cut_right+=1
assert cut_left>80 and cut_right>80,("Front coat wedge not found",cut_left,cut_right)
bmesh.ops.delete(bm,geom=cutfaces,context="FACES")
report["authored_front_panels_opened"]=True
report["real_coat_faces_physically_removed"]=len(cutfaces)
report["front_cut_faces_left"]=cut_left
report["front_cut_faces_right"]=cut_right
report["open_blazer_waist_gap_width_design_m"]=.34
# Remove floating old centerline buttons. Buttons were modeled for a closed
# garment and cannot be attached in the new open-front silhouette.
buttonfaces=[]
for c in components:
    if c is main:continue
    if c["count"]<120 and abs(c["x"]-cx)<.07 and c["y"]<cy-.05 and \
      lo.z+1.02<c["z"]<lo.z+1.49:
        buttonfaces.extend(f for f in c["faces"] if f.is_valid)
if buttonfaces:
    bmesh.ops.delete(bm,geom=buttonfaces,context="FACES")
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.is_valid and not v.link_faces],context="VERTS")
report["closed_jacket_button_faces_removed"]=len(buttonfaces)

# Narrow sewn sleeves around the original animated arm axis, retaining the
# real CC0 sleeve edges and original skinning. No primitive-based sleeves.
sleeve_changed=0
sleeve_by_side={"L":0,"R":0}
def nearest_seg(p,a,b):
    d=b-a
    return a+max(0,min(1,(p-a).dot(d)/max(1e-9,d.length_squared)))*d
for side in ("L","R"):
    upper=rig.pose.bones.get("upperarm01."+side)
    fore=rig.pose.bones.get("lowerarm01."+side)
    assert upper and fore,side
    shoulder=rig.matrix_world@upper.head
    elbow=rig.matrix_world@upper.tail
    wrist=rig.matrix_world@fore.tail
    sgn=1 if shoulder.x>cx else -1
    for v in main["verts"]:
        if not v.is_valid:continue
        p=matrix@v.co
        zz=p.z-lo.z
        ax=abs(p.x-cx)
        if ((p.x-cx)*sgn<0 or ax<.33 or not(1.06<zz<1.59)):
            continue
        q=min((nearest_seg(p,shoulder,elbow),nearest_seg(p,elbow,wrist)),
              key=lambda q:(p-q).length_squared)
        radial=p-q
        if radial.length>.19:continue
        weight=.12*band(zz,1.06,1.19,1.46,1.56)
        if weight<.01:continue
        v.co=inverse@(p-weight*radial)
        sleeve_changed+=1
        sleeve_by_side[side]+=1
assert sleeve_changed>100,("No sleeve geometry refined",sleeve_by_side)
report["real_sleeve_vertices_refined"]=sleeve_changed
report["sleeve_vertices_by_side"]=sleeve_by_side

bm.to_mesh(suit.data); bm.free()
suit.data.update()
assert cut_left>80 and cut_right>80 and sleeve_changed>100,(cut_left,cut_right,sleeve_changed)
report["garment_original_triangles_after_tailoring"]=tris(suit)

# Independent realistic black shirt on exact wearer torso topology (CC0 skinned
# human surface), then slightly displaced above the base skin. No primitives.
main=max(full,key=lambda o:len(o.data.polygons))
shirt=main.copy()
shirt.data=main.data.copy()
shirt.name="Cuervo_Camisa_Independiente_CuerpoAnatomico"
scene.collection.objects.link(shirt)
shirt.hide_render=False
shirt.hide_set(False)
mb=bmesh.new();mb.from_mesh(shirt.data)
mat=shirt.matrix_world.copy()
def inside(v):
    p=mat@v.co
    return lo.z+1.02<=p.z<=lo.z+1.585 and abs(p.x-cx)<.35
to_delete=[face for face in mb.faces if not all(inside(v) for v in face.verts)]
bmesh.ops.delete(mb,geom=to_delete,context="FACES")
bmesh.ops.delete(mb,geom=[v for v in mb.verts if not v.link_faces],context="VERTS")
mb.to_mesh(shirt.data);mb.free();shirt.data.update()
assert tris(shirt)>400,("Insufficient real anatomical shirt faces",tris(shirt))
# Gentle offset along actual skin normals gives the shirt independent 3D shape.
for v in shirt.data.vertices:
    v.co+=v.normal*.010
shirt.data.update()
shirt.data.materials.clear()
textile=bpy.data.materials.new("Cuervo_Camisa_Negra_Independiente")
textile.diffuse_color=(.018,.022,.027,1)
textile.use_nodes=True
bs=textile.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.018,.021,.027,1)
bs.inputs["Roughness"].default_value=.93
bs.inputs["Metallic"].default_value=0
shirt.data.materials.append(textile)
assert any(m.type=="ARMATURE" for m in shirt.modifiers),"Shirt lost source rig"
report["independent_shirt_triangles"]=tris(shirt)
report["independent_shirt_vertex_groups"]=len(shirt.vertex_groups)
# Shirt CC0 original upper chest components and lapels from suit kept, but
# recolor any remaining pale collar without recoloring lapel edges.
shirtmat=bpy.data.materials.get("Cuervo_Camisa_Negra_Grafito")
if shirtmat:
    for i,poly in enumerate(suit.data.polygons):
        if poly.material_index>=len(suit.data.materials):continue
        if len(poly.vertices)<3:continue
        p=sum((suit.matrix_world@suit.data.vertices[j].co for j in poly.vertices),Vector())/len(poly.vertices)
        if (lo.z+1.535<p.z<lo.z+1.68 and abs(p.x-cx)<.155 and p.y<cy+.03):
            poly.material_index=list(suit.data.materials).index(shirtmat)
report["independent_shirt_surface_method"]="genuine rigged anatomical torso topology, edited and coated with matte textile material"

# Fitted suit and new shirt in neutral armature pose. Generate meaningful
# "before and after" camera views, plus naturalish arm-lowered viewpoint.
for ob in full:ob.hide_render=True
cam=scene.camera
assert cam
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=14
scene.cycles.use_denoising=True
scene.render.resolution_x=760
scene.render.resolution_y=1040
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
focus=Vector((cx,cy,lo.z+H*.51))
def render(name,offset,target=focus,scale=2.28):
    target=Vector(target)
    cam.data.type="ORTHO"
    cam.data.ortho_scale=scale
    cam.location=target+Vector(offset)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>4000,name
render("01_Open_Blazer_Frontal_Apose",(0,-4,.13))
render("02_Open_Blazer_TresCuartos_Apose",(2.8,-3.8,.17))
render("03_Open_Blazer_Detalle_Camisa",(1,-4,.08),
       Vector((cx,cy,lo.z+H*.73)),1.18)
render("04_Open_Blazer_Espalda",(0,4,.13))
# Rotate both upper arm bones from source neutral pose. Skin weights move
# clothes and hands; store temporary test rotation, don't bake pose to GLB.
old={}
for side,ang in (("L",-.50),("R",.50)):
    pb=rig.pose.bones["upperarm01."+side]
    old[side]=(pb.rotation_mode,pb.rotation_quaternion.copy(),pb.rotation_euler.copy())
    pb.rotation_mode="QUATERNION"
    from mathutils import Quaternion
    pb.rotation_quaternion=Quaternion(Vector((0,0,1)),ang)@pb.rotation_quaternion
bpy.context.view_layer.update()
render("05_Open_Blazer_Frontal_BrazosBajos",(0,-4,.13))
render("06_Open_Blazer_TresCuartos_BrazosBajos",(2.8,-3.8,.17))
for side in ("L","R"):
    pb=rig.pose.bones["upperarm01."+side]
    mode,q,e=old[side]
    pb.rotation_quaternion=q;pb.rotation_mode=mode;pb.rotation_euler=e
bpy.context.view_layer.update()

bpy.ops.file.pack_all()
blend=os.path.join(out,"El_Cuervo_Blazer_Abierto_Fase5_WIP.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
assert os.path.getsize(blend)>10000

bpy.ops.object.select_all(action="DESELECT")
for ob in [rig,suit,shirt]+skin+boots:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
glb=os.path.join(out,"El_Cuervo_Blazer_Abierto_Fase5_WIP.glb")
bpy.ops.export_scene.gltf(filepath=glb,export_format="GLB",use_selection=True,
                          export_materials="EXPORT",export_yup=True)
with open(glb,"rb") as f:
    magic,version,size=struct.unpack("<4sII",f.read(12))
    assert magic==b"glTF" and version==2 and size==os.path.getsize(glb)
    n,typ=struct.unpack("<I4s",f.read(8));assert typ==b"JSON"
    gltf=json.loads(f.read(n).decode("utf8"))
nodes=[o.get("name","") for o in gltf["nodes"] if "mesh" in o]
assert suit.name in nodes and shirt.name in nodes,nodes
assert any(n.startswith("Cuervo_Botin_CC0") for n in nodes),nodes
assert all("skin" in node for node in gltf["nodes"] if "mesh" in node),nodes
report.update(dict(exported_mesh_nodes=nodes,original_body_preserved=True,
            game_modified=False,artistic_approved=False,motion_approved=False,
            android_fps_tested=False,blend=os.path.basename(blend),
            glb=os.path.basename(glb),
            final_blazer_triangles=tris(suit),
            final_visible_triangles=sum(tris(x) for x in [suit,shirt]+skin+boots),
            warnings=["Blazer open WIP based on true CC0 tailored garment panels",
             "Body torso used for real mesh shirt; clothing still needs manual retopology and pose QA",
             "No GPU or Android benchmark. Do not merge to main."]))
with open(os.path.join(out,"Fase5_Auditoria.json"),"w",encoding="utf8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)
print("CUERVO_FASE5_AUTHENTIC_OPEN_TAILORED_READY",json.dumps(report,ensure_ascii=False),flush=True)
