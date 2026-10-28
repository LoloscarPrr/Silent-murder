"""EL CUERVO — Fase 5 alterna. Garment is genuine MakeHuman system
male_elegantsuit01 (CC0), not a deformed patch of Margaret Toigo suit.
Keeps the same approved humanoid MakeHuman mesh, bones, and real CC0 boots.
Authored garments only; no primitive-based fake jacket or manual coat cutting.
Blender 4.3:
 --blend <phase4.blend> --obj <system male_elegantsuit01.obj> --texture <diffuse.png> --out <output>
"""
import bpy,os,sys,struct,json,math
from mathutils import Vector,Matrix,Quaternion
from mathutils.kdtree import KDTree
def arg(key):
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    assert key in args,key
    return os.path.abspath(args[args.index(key)+1])
src=arg("--blend");out=arg("--out");source=arg("--obj");texture=arg("--texture")
assert all(os.path.isfile(p) for p in (src,source,texture))
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
scene=bpy.context.scene
rigs=[o for o in scene.objects if o.type=="ARMATURE"]
assert len(rigs)==1
rig=rigs[0]
full=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("base_male_body")]
skin=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("VisibleSkin_")]
boots=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("Cuervo_Botin_CC0")]
old=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("CC0_toigo_male_suit_3")]
assert full and skin and boots and old
bpy.context.view_layer.update()
def bounds(objs):
    pts=[o.matrix_world@Vector(c) for o in objs for c in o.bound_box]
    return Vector(tuple(min(p[k] for p in pts) for k in range(3))),Vector(tuple(max(p[k] for p in pts) for k in range(3)))
lo,hi=bounds(full)
H=hi.z-lo.z
assert abs(H-1.84)<.02
body_center=(lo+hi)*.5
def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
for o in old:bpy.data.objects.remove(o,do_unlink=True)
# Import ARTIST-modeled CC0 standard fitted suit; not from other chat's
# damaged jacket. Import retains authored seam, cuffs, jacket, pants, UVs.
prior=set(scene.objects)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.obj_import(filepath=source,forward_axis="NEGATIVE_Z",up_axis="Y")
garments=[o for o in scene.objects if o not in prior and o.type=="MESH"]
assert garments,[o.name for o in scene.objects]
src_tris=sum(tris(o) for o in garments)
assert 3000<src_tris<100000,(src_tris,"Not a genuine detailed suit")
mn,mx=bounds(garments);dim=mx-mn
assert .1<min(dim) and max(dim)<100,(mn,mx)
# UNIFORM rescale (previous disastrous garment used non-uniform x based
# on fully outstretched arm-span, which inflated shoulders).
dest_bottom=lo.z+.09
dest_top=lo.z+H*.945
factor=(dest_top-dest_bottom)/dim.z
assert .04<factor<2,("Unexpected OBJ unit scale",factor,dim)
center=(mn+mx)*.5
model=Matrix.Translation(Vector((body_center.x,body_center.y,dest_bottom))) @ \
      Matrix.Diagonal(Vector((factor,factor,factor,1))) @ \
      Matrix.Translation(Vector((-center.x,-center.y,-mn.z)))
for i,o in enumerate(garments):
    o.matrix_world=model@o.matrix_world
    o.name="Cuervo_Traje_MakeHumanElegante_CC0_"+str(i+1)
    for p in o.data.polygons:p.use_smooth=True
bpy.context.view_layer.update()

# The standard elegant suit has an excessively high standard shirt collar
# on this particular 1.84m head. Move ONLY upper/central collar vertices
# below the original human chin, while preserving shoulders and coat.
# Anatomical repair is based on 3D garment coordinates, not an image edit.
neck_vertices=0
for cloth in garments:
    M=cloth.matrix_world.copy()
    inv=M.inverted()
    for v in cloth.data.vertices:
        p=M@v.co
        z=p.z-lo.z
        ax=abs(p.x-body_center.x)
        if z<1.48 or ax>.235:continue
        closeness=1-min(1,max(0,(ax-.15)/.085))
        heightweight=max(0,min(1,(z-1.48)/.17))
        heightweight=heightweight*heightweight*(3-2*heightweight)
        adjust=.142*heightweight*closeness
        if adjust>.005:
            p.z-=adjust
            v.co=inv@p
            neck_vertices+=1
    cloth.data.update()
assert neck_vertices>70,("Tailored collar not found",neck_vertices)
print("CC0_SUIT_COLLAR_REAL_VERTEX_REPAIR",neck_vertices,flush=True)

# Textile PBR using actual MakeHuman texture and UV, multiplied dark enough
# to turn formal shirt graphite and jacket matte black; original UVs retained.
img=bpy.data.images.load(texture,check_existing=True)
assert min(img.size)>=128,img.size
mat=bpy.data.materials.new("Cuervo_Traje_Negro_Original_CC0")
mat.diffuse_color=(.036,.038,.044,1)
mat.use_nodes=True
nodes=mat.node_tree.nodes
links=mat.node_tree.links
base=nodes.get("Principled BSDF")
base.inputs["Roughness"].default_value=.88
base.inputs["Metallic"].default_value=.0
tex=nodes.new("ShaderNodeTexImage")
tex.image=img
mix=nodes.new("ShaderNodeMixRGB")
mix.blend_type="MULTIPLY"
mix.inputs[0].default_value=1
mix.inputs[2].default_value=(.25,.26,.29,1)
links.new(tex.outputs["Color"],mix.inputs[1])
links.new(mix.outputs["Color"],base.inputs["Base Color"])
graphite=bpy.data.materials.new("Cuervo_Camisa_Interior_Grafito")
graphite.use_nodes=True
cbs=graphite.node_tree.nodes.get("Principled BSDF")
cbs.inputs["Base Color"].default_value=(.029,.031,.039,1)
cbs.inputs["Roughness"].default_value=.93
cbs.inputs["Metallic"].default_value=0
shirt_faces=0
for o in garments:
    assert o.data.uv_layers.active is not None,("no UV in original CC0 suit",o.name)
    o.data.materials.clear()
    o.data.materials.append(mat)
    o.data.materials.append(graphite)
    # Assign central collar and tie geometry graphite; no bright striped tie
    # at mouth level. The authentic UVs remain in the main jacket.
    for face in o.data.polygons:
        positions=[o.matrix_world@o.data.vertices[i].co for i in face.vertices]
        c=sum(positions,Vector())/len(positions)
        if (abs(c.x-body_center.x)<.155 and
                lo.z+1.39<c.z<lo.z+1.69 and
                c.y<body_center.y+.07):
            face.material_index=1
            shirt_faces+=1
assert shirt_faces>100,shirt_faces
print("CC0_SHIRT_GRAPHITE_FACE_MATERIAL",shirt_faces,flush=True)

# Skin original CC0 suit to the ORIGINAL 163-bone human. This is a transfer
# starting point, not a professional manual rig guarantee.
points=[]
tree=KDTree(sum(len(o.data.vertices) for o in full))
for o in full:
    for v in o.data.vertices:
        j=len(points)
        tree.insert(o.matrix_world@v.co,j)
        points.append((o,v.index))
tree.balance()
original_groups=sorted({g.name for o in full for g in o.vertex_groups})
skin_stats=[]
for item in garments:
    buckets={name:item.vertex_groups.new(name=name) for name in original_groups}
    skinned=0
    for v in item.data.vertices:
        _,idx,dist=tree.find(item.matrix_world@v.co)
        p,vi=points[idx]
        copied=False
        for wg in p.data.vertices[vi].groups:
            name=p.vertex_groups[wg.group].name
            if wg.weight>.00001 and name in buckets:
                buckets[name].add([v.index],wg.weight,"REPLACE")
                copied=True
        skinned+=int(copied)
    assert skinned>=len(item.data.vertices)*.98,(item.name,skinned,len(item.data.vertices))
    md=item.modifiers.new("Armature_ElCuervo_Original","ARMATURE")
    md.object=rig
    skin_stats.append({"mesh":item.name,"vertices":len(item.data.vertices),
                       "skinned_vertices":skinned,"triangles":tris(item)})
for o in full:o.hide_render=True
# Real studio renders of candidate garment, no AI image generation.
cam=scene.camera
assert cam,"Studio camera absent"
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=13
scene.cycles.use_denoising=True
scene.render.resolution_x=720
scene.render.resolution_y=990
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
look=Vector((body_center.x,body_center.y,lo.z+H*.52))
def render(name,offset,point=look,scale=2.25):
    point=Vector(point)
    cam.data.type="ORTHO"
    cam.data.ortho_scale=scale
    cam.location=point+Vector(offset)
    cam.rotation_euler=(point-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>4000
render("01_Sastre_CC0_Frente_Apose",(0,-4.3,.15))
render("02_Sastre_CC0_TresCuartos_Apose",(2.8,-3.8,.14))
render("03_Sastre_CC0_Detalle",(1.2,-3.7,.09),
       Vector((body_center.x,body_center.y,lo.z+H*.74)),1.10)
# Posed view is a diagnostic; GLB is saved in original A-pose.
oldpose={}
for side,angle in (("L",-.5),("R",.5)):
    bone=rig.pose.bones.get("upperarm01."+side)
    assert bone
    oldpose[side]=(bone.rotation_mode,bone.rotation_euler.copy(),bone.rotation_quaternion.copy())
    bone.rotation_mode="QUATERNION"
    bone.rotation_quaternion=Quaternion(Vector((0,0,1)),angle)@bone.rotation_quaternion
bpy.context.view_layer.update()
render("04_Sastre_CC0_Frente_BrazosAbajo",(0,-4.3,.15))
render("05_Sastre_CC0_TresCuartos_BrazosAbajo",(2.8,-3.8,.14))
for side in ("L","R"):
    bone=rig.pose.bones["upperarm01."+side]
    mode,eu,q=oldpose[side]
    bone.rotation_quaternion=q
    bone.rotation_mode=mode
    bone.rotation_euler=eu
bpy.context.view_layer.update()
render("06_Sastre_CC0_Espalda",(0,4.3,.12))
bpy.ops.file.pack_all()
blend=os.path.join(out,"El_Cuervo_Sastre_CC0_NuevaBase_WIP.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
assert os.path.getsize(blend)>10000
bpy.ops.object.select_all(action="DESELECT")
for ob in [rig]+garments+skin+boots:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
glb=os.path.join(out,"El_Cuervo_Sastre_CC0_NuevaBase_WIP.glb")
bpy.ops.export_scene.gltf(filepath=glb,export_format="GLB",
                          use_selection=True,export_materials="EXPORT",export_yup=True)
with open(glb,"rb") as f:
    magic,version,size=struct.unpack("<4sII",f.read(12))
    assert magic==b"glTF" and version==2 and size==os.path.getsize(glb)
    length,kind=struct.unpack("<I4s",f.read(8))
    assert kind==b"JSON"
    g=json.loads(f.read(length).decode("utf8"))
nodes=[n.get("name") for n in g["nodes"] if "mesh" in n]
assert any(n.startswith("Cuervo_Traje_MakeHumanElegante_CC0_") for n in nodes),nodes
assert any(n.startswith("Cuervo_Botin_CC0") for n in nodes),nodes
assert len(g.get("skins",[]))>=1
result={"status":"WIP_NEW_CC0_SUIT_NOT_ART_APPROVED",
        "source_asset":"MakeHuman official male_elegantsuit01 CC0",
        "source_asset_url":"https://free.downloads.tuxfamily.net/makehuman/assets/1.1/base/clothes/male_elegantsuit01/",
        "source_mesh_triangles":src_tris,
        "source_dimensions":list(dim),
        "uniform_scale_factor":factor,
        "male_body_original_height_m":H,
        "male_body_original_unmodified":True,
        "rig_bones":len(rig.data.bones),
        "neckline_vertices_laid_down":neck_vertices,
        "shirt_faces_reassigned_to_graphite":shirt_faces,
        "parts":skin_stats,
        "exported_nodes":nodes,
        "blender_file":os.path.basename(blend),
        "glb_file":os.path.basename(glb),
        "visual_review_approved":False,
        "animation_approved":False,
        "android_fps_tested":False,
        "main_game_modified":False,
        "warnings":["Fitting + skin weights automatically estimated, not manual sculpting",
                    "No guarantee of no intersections until visual QA",
                    "CC0 MakeHuman original body retained; boots retained from earlier suit"]}
with open(os.path.join(out,"AUDITORIA_SASTRE_CC0.json"),"w",encoding="utf8") as f:
    json.dump(result,f,indent=2,ensure_ascii=False)
print("AUTHENTIC_EL_CUERVO_NEW_ELEGANT_SUIT_CANDIDATE",json.dumps(result,ensure_ascii=False),flush=True)
