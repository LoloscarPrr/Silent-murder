"""Silent Killer / El Cuervo: Fase 4. Refine genuine CC0 suit, add genuine CC0
male ankle boots, keep MakeHuman skeleton. Real Blender mesh output only.
WIP technical preview, not an artist-approved final player model.
Blender 4.3:
  blender -b --python tools/el_cuervo/fase4_refine.py -- --blend <approved_fase3_suit.blend> --shoes <official_shoes01_CC0.zip> --out <output>
"""
import bpy,bmesh,os,sys,json,zipfile,hashlib,math,struct,statistics
from mathutils import Vector, Matrix, Quaternion
from mathutils.kdtree import KDTree

def arg(name):
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    assert name in args, "missing argument "+name
    return args[args.index(name)+1]

input_blend=os.path.abspath(arg("--blend"))
shoes_zip=os.path.abspath(arg("--shoes"))
out=os.path.abspath(arg("--out"))
assert os.path.isfile(input_blend) and zipfile.is_zipfile(shoes_zip)
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=input_blend)
scene=bpy.context.scene
armatures=[o for o in scene.objects if o.type=="ARMATURE"]
assert len(armatures)==1,armatures
arm=armatures[0]
clothes=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("CC0_toigo_male_suit_3_")]
assert len(clothes)==1,[o.name for o in scene.objects if o.type=="MESH"]
suit=clothes[0]
body_full=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("base_male_body")]
body_visible=[o for o in scene.objects if o.type=="MESH" and o.name.startswith("VisibleSkin_")]
assert body_full and body_visible,(body_full,body_visible)
bpy.context.view_layer.update()

def bounds(objects):
    coords=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return Vector(tuple(min(p[k] for p in coords) for k in range(3))),Vector(tuple(max(p[k] for p in coords) for k in range(3)))

lo,hi=bounds(body_full)
H=hi.z-lo.z
assert abs(H-1.84)<.017,(lo,hi,H)
cx=(lo.x+hi.x)*.5
cy=(lo.y+hi.y)*.5

def smoothstep(edge0,edge1,x):
    p=max(0.,min(1.,(x-edge0)/(edge1-edge0)))
    return p*p*(3-2*p)
def bell(x,l0,l1,r0,r1):
    return smoothstep(l0,l1,x)*(1-smoothstep(r0,r1,x))
def tris(ob):return sum(len(p.vertices)-2 for p in ob.data.polygons)

stats={"source_blend":os.path.basename(input_blend),
       "source_suit_mesh_triangles":tris(suit),
       "source_human_triangles":sum(tris(o) for o in body_full),
       "source_makehuman_male_height_m":round(H,5),
       "source_original_CC0_suit":"Margaret Toigo, suits01",
       "source_original_CC0_shoes":"MakeHuman Community shoes01; toigo_ankle_boots_male",
       "comparison_to_user_feedback":["hombros anchos","mangas gruesas","cintura boxy",
         "camisa palida","sin calzado","A-pose poco natural"]}

# Edit existing artist-authored suit vertices. Never replace human anatomy with primitives.
original_matrix=suit.matrix_world.copy()
inverse=original_matrix.inverted()
total_shoulder=total_waist=0.
for vert in suit.data.vertices:
    p=original_matrix@vert.co
    ax=abs(p.x-cx)
    zz=p.z-lo.z
    # Narrow only torso shoulder/cap seam; taper to 0 near hand cuffs.
    shoulder_zone=bell(zz,1.24,1.38,1.56,1.68)*bell(ax,.20,.28,.52,.72)
    waist_zone=bell(zz,.75,.94,1.20,1.34)*bell(ax,.12,.19,.35,.48)
    shrink=.11*shoulder_zone+.065*waist_zone
    p.x=cx+(p.x-cx)*(1.0-shrink)
    if shoulder_zone>.4:total_shoulder+=1
    if waist_zone>.4:total_waist+=1
    vert.co=inverse@p
suit.data.update()
assert total_shoulder>50 and total_waist>40,(total_shoulder,total_waist)
for poly in suit.data.polygons:
    poly.use_smooth=True
stats["edited_suit_vertices_shoulder"]=total_shoulder
stats["edited_suit_vertices_waist"]=total_waist
stats["suit_shoulder_shrink_max"]=.11
stats["suit_waist_shrink_max"]=.065

# Main CC0 suit atlas has pale shirt + grey jacket, authored together.
# Darken the fabric's EXISTING material multiplier (not the face/skin),
# so shirt appears charcoal and jacket matte black.
materials=[mat for mat in suit.data.materials if mat]
assert materials,"Missing original suit materials"
applied=False
for mat in materials:
    if not mat.use_nodes:continue
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Roughness"].default_value=.87
        bsdf.inputs["Metallic"].default_value=0
    for node in mat.node_tree.nodes:
        if node.type=="MIX_RGB" and node.blend_type=="MULTIPLY":
            node.inputs[2].default_value=(.095,.105,.122,1)
            applied=True
    if not applied and bsdf:
        bsdf.inputs["Base Color"].default_value=(.07,.077,.092,1)
stats["suit_material_darkening_applied"]=applied
stats["outfit_intent"]="matte black jacket and distinctly darker graphite shirt; authored UV atlas retained"

# Classify ORIGINAL CC0 garment faces using their authored UV atlas.
# The shirt/collar region is bright in the atlas and at the upper central
# torso in 3D. Assign those EXISTING faces a separate dark shirt material,
# rather than creating a fake planar shirt or flattening the original texture.
import numpy as np
shirt_faces=0
shirt= bpy.data.materials.new("Cuervo_Camisa_Negra_Grafito")
shirt.use_nodes=True
bs=shirt.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.029,.033,.041,1.0)
bs.inputs["Roughness"].default_value=.88
bs.inputs["Metallic"].default_value=0.0
suit.data.materials.append(shirt)
shirt_slot=len(suit.data.materials)-1
teximg=next((n.image for m in materials if m.use_nodes
             for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image),None)
assert teximg is not None,"Original CC0 suit UV image not found"
uvlayer=suit.data.uv_layers.active
assert uvlayer is not None,"Suits source has no UV atlas"
ww,hh=teximg.size
texarr=np.asarray(teximg.pixels[:],dtype=np.float32).reshape((hh,ww,4))
for poly in suit.data.polygons:
    coords=[suit.matrix_world@suit.data.vertices[i].co for i in poly.vertices]
    worldp=sum(coords,Vector())/len(coords)
    if worldp.z<lo.z+1.28 or abs(worldp.x-cx)>.25:continue
    lightness=[]
    for loop_index in poly.loop_indices:
        uv=uvlayer.data[loop_index].uv
        ix=max(0,min(ww-1,int(uv.x*(ww-1))))
        iy=max(0,min(hh-1,int(uv.y*(hh-1))))
        rgb=texarr[iy,ix,:3]
        lightness.append(float(np.mean(rgb)))
    if lightness and statistics.median(lightness)>.30:
        poly.material_index=shirt_slot
        shirt_faces+=1
del texarr
assert 50<shirt_faces<4500,("shirt atlas classification unreliable",shirt_faces)
stats["shirt_faces_recolored_using_original_UV"]=shirt_faces
print("DARK_SHIRT_REAL_FACES",shirt_faces,flush=True)


# Shoes source: same MakeHuman CC0 author as original suit, true OBJ meshes.
target="toigo_ankle_boots_male"
with zipfile.ZipFile(shoes_zip) as z:
    names=z.namelist()
    options=[name for name in names if name.lower().endswith(".obj") and
             target in name.lower() and "/__macosx/" not in name.lower()]
    assert len(options)==1,("Missing unique authentic male ankle boots OBJ",options)
    source_name=options[0]
    prefix=os.path.dirname(source_name)+"/"
    os.makedirs("/tmp/cuervo_shoes04",exist_ok=True)
    for entry in names:
        if not entry.startswith(prefix): continue
        dest=os.path.abspath(os.path.join("/tmp/cuervo_shoes04",entry))
        assert os.path.commonpath(("/tmp/cuervo_shoes04",dest))=="/tmp/cuervo_shoes04"
        z.extract(entry,"/tmp/cuervo_shoes04")
obj_path=os.path.join("/tmp/cuervo_shoes04",source_name)
assert os.path.getsize(obj_path)>1000,obj_path
before=set(scene.objects)
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.obj_import(filepath=obj_path,forward_axis="NEGATIVE_Z",up_axis="Y")
shoes=[o for o in scene.objects if o not in before and o.type=="MESH"]
assert shoes,"Shoe pack lacks geometric OBJ"
shoe_before_tris=sum(tris(o) for o in shoes)
assert 1000<shoe_before_tris<150000,(shoe_before_tris,source_name)

# Determine foot region from ORIGINAL CC0 human (not from trouser).
feet=[]
for source in body_full:
    mat=source.matrix_world
    for v in source.data.vertices:
        p=mat@v.co
        if p.z<lo.z+.175:
            feet.append(p)
assert len(feet)>1000,len(feet)
feet_min=Vector(tuple(min(p[k] for p in feet) for k in range(3)))
feet_max=Vector(tuple(max(p[k] for p in feet) for k in range(3)))
smn,smx=bounds(shoes)
sd=smx-smn
assert min(sd)>0 and max(sd)<100,sd
shoe_pair_width=(feet_max.x-feet_min.x)+.055
shoe_pair_depth=(feet_max.y-feet_min.y)+.065
shoe_pair_height=.195
sx=shoe_pair_width/sd.x
sy=shoe_pair_depth/sd.y
sz=shoe_pair_height/sd.z
# Keep genuine authored topology, adapt overall proportions only.
transform=(Matrix.Translation(Vector(((feet_min.x+feet_max.x)*.5,
        (feet_min.y+feet_max.y)*.5,lo.z+.006)))@
        Matrix.Diagonal(Vector((sx,sy,sz,1)))@
        Matrix.Translation(Vector((-(smn.x+smx.x)*.5,
        -(smn.y+smx.y)*.5,-smn.z))))
for shoe in shoes:
    shoe.matrix_world=transform@shoe.matrix_world
    shoe.name="Cuervo_Botin_CC0_"+str(shoes.index(shoe)+1)
    for face in shoe.data.polygons:face.use_smooth=True
bpy.context.view_layer.update()

bootmat=bpy.data.materials.new("Cuervo_Cuero_Botin_Negro_Mate")
bootmat.use_nodes=True
boots_shader=bootmat.node_tree.nodes.get("Principled BSDF")
boots_shader.inputs["Base Color"].default_value=(.018,.020,.024,1)
boots_shader.inputs["Roughness"].default_value=.53
boots_shader.inputs["Metallic"].default_value=.025
for shoe in shoes:
    shoe.data.materials.clear()
    shoe.data.materials.append(bootmat)

# Transfer weights from actual CC0 human vertices (boot tips use nearest foot weights).
count=sum(len(o.data.vertices) for o in body_full)
tree=KDTree(count)
lookup=[]
for source in body_full:
    for v in source.data.vertices:
        j=len(lookup)
        tree.insert(source.matrix_world@v.co,j)
        lookup.append((source,v.index))
tree.balance()
weights_report=[]
for shoe in shoes:
    groups={name:shoe.vertex_groups.new(name=name) for name in sorted({g.name for o in body_full for g in o.vertex_groups})}
    weighted=0
    for vertex in shoe.data.vertices:
        _,j,d=tree.find(shoe.matrix_world@vertex.co)
        source,vi=lookup[j]
        copied=False
        for elem in source.data.vertices[vi].groups:
            gname=source.vertex_groups[elem.group].name
            if elem.weight>.00001:
                groups[gname].add([vertex.index],elem.weight,"REPLACE")
                copied=True
        if copied:weighted+=1
    assert weighted==len(shoe.data.vertices),(shoe.name,weighted,len(shoe.data.vertices))
    modifier=shoe.modifiers.new("BotinRigCC0","ARMATURE")
    modifier.object=arm
    weights_report.append(dict(name=shoe.name,vertices=len(shoe.data.vertices),
                triangles=tris(shoe),weighted_vertices=weighted))
stats["shoe_original_obj"]=source_name
stats["shoe_original_triangles"]=shoe_before_tris
stats["shoe_fitted_bounds"]={"min":list(bounds(shoes)[0]),"max":list(bounds(shoes)[1])}
stats["shoe_weights_report"]=weights_report

# Prevent bare feet intersecting leather. Full original human meshes intact,
# only optional visible-skin export copies are masked under the shoes.
for visible in body_visible:
    geo=bmesh.new();geo.from_mesh(visible.data)
    doomed=[f for f in geo.faces if all((visible.matrix_world@v.co).z<lo.z+.165 for v in f.verts)]
    if doomed:
        bmesh.ops.delete(geo,geom=doomed,context="FACES")
        bmesh.ops.delete(geo,geom=[v for v in geo.verts if not v.link_faces],context="VERTS")
    geo.to_mesh(visible.data);geo.free();visible.data.update()
stats["visible_skin_faces_after_shoes"]=sum(tris(x) for x in body_visible)
# Original source body is hidden in BLEND, never export it.
for original in body_full:original.hide_render=True

# Diagnostic neutral A pose, plus arm-lowered pose. No permanent pose applied to GLB.
def pose_sample(max_angle=.55):
    trial=[]
    old={}
    for side in ["L","R"]:
        key="upperarm01."+side
        pb=arm.pose.bones.get(key)
        assert pb,key
        old[key]=(pb.rotation_mode,pb.rotation_quaternion.copy(),pb.rotation_euler.copy())
        pb.rotation_mode="QUATERNION"
        initial=pb.rotation_quaternion.copy()
        forearm=arm.pose.bones.get("lowerarm01."+side)
        assert forearm,"Missing forearm to validate the actual wrist"
        best=None
        for axis in ["X","Y","Z"]:
            av={"X":Vector((1,0,0)),"Y":Vector((0,1,0)),"Z":Vector((0,0,1))}[axis]
            for k in [-.80,-.65,-.50,-.35,-.20,-.10,.0,.10,.20,.35,.50,.65,.80]:
                pb.rotation_quaternion=Quaternion(av,k)@initial
                bpy.context.view_layer.update()
                shoulder=arm.matrix_world@pb.head
                wrist=arm.matrix_world@forearm.tail
                elbow=arm.matrix_world@pb.tail
                spread=abs(wrist.x-cx)
                drop=shoulder.z-wrist.z
                # Optimize the WHOLE limb, not merely the elbow. The last
                # implementation mistakenly preferred T-pose, because
                # it checked elbow X alone and ignored the wrist height.
                error=abs(spread-.32)*4.0+abs(drop-.52)*4.0+abs(wrist.y-cy)*.7+abs(k)*.05
                if drop<.28:error+=2.0
                if best is None or error<best[0]:
                    best=(error,axis,k,tuple(elbow),tuple(wrist),drop,spread)
        assert best
        pb.rotation_quaternion=Quaternion({"X":Vector((1,0,0)),"Y":Vector((0,1,0)),"Z":Vector((0,0,1))}[best[1]],best[2])@initial
        bpy.context.view_layer.update()
        wrist=arm.matrix_world@forearm.tail
        shoulder=arm.matrix_world@pb.head
        assert (shoulder.z-wrist.z)>.27,("arm still horizontal",side,best)
        trial.append({"bone":key,"axis":best[1],"radians":best[2],
                      "score":round(best[0],5),"elbow_world":best[3],
                      "wrist_world":best[4],"wrist_drop_m":round(best[5],4),
                      "wrist_spread_from_center_m":round(best[6],4)})
    return trial,old

cam=scene.camera
assert cam
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=14
scene.cycles.use_denoising=True
scene.render.resolution_x=720
scene.render.resolution_y=1000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
target=Vector((cx,cy,lo.z+H*.52))
def render(name,offset,focus=target,scale=2.30):
    cam.data.type="ORTHO"
    cam.data.ortho_scale=scale
    point=Vector(focus)
    cam.location=point+Vector(offset)
    cam.rotation_euler=(point-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>4000,name

render("01_Frontal_Apose",(0,-4,.12))
render("02_Tres_Cuartos_Apose",(2.8,-3.9,.14))
render("03_Posterior_Apose",(0,4,.10))
render("04_Chaqueta_Camisa", (1,-3.6,.09),
       focus=Vector((cx,cy,lo.z+H*.73)),scale=1.18)
render("05_Calzado", (1.4,-2.8,.05),
       focus=Vector((cx,cy,lo.z+.14)),scale=.57)
poses,old=pose_sample()
render("06_Frontal_Brazos_Bajos",(0,-4,.12))
render("07_Tres_Cuartos_Brazos_Bajos",(2.8,-3.9,.15))
stats["posed_arm_down_trials"]=poses
for key,(mode,q,e) in old.items():
    pb=arm.pose.bones[key];pb.rotation_quaternion=q;pb.rotation_mode=mode;pb.rotation_euler=e
bpy.context.view_layer.update()

# Produce editable file keeping all geometry, including hidden original anatomy.
bpy.ops.file.pack_all()
blend_file=os.path.join(out,"El_Cuervo_Refinado_Fase4_WIP.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_file)
assert os.path.getsize(blend_file)>10000

bpy.ops.object.select_all(action="DESELECT")
for obj in body_visible+clothes+shoes+[arm]:obj.select_set(True)
bpy.context.view_layer.objects.active=arm
glb_file=os.path.join(out,"El_Cuervo_Refinado_Fase4_WIP.glb")
bpy.ops.export_scene.gltf(filepath=glb_file,export_format="GLB",use_selection=True,
                          export_materials="EXPORT",export_yup=True)
with open(glb_file,"rb") as f:
    magic,version,size=struct.unpack("<4sII",f.read(12))
    assert magic==b"glTF" and version==2 and size==os.path.getsize(glb_file)
    chunklen,typ=struct.unpack("<I4s",f.read(8))
    assert typ==b"JSON"
    gltf=json.loads(f.read(chunklen).decode("utf-8"))
names=[n.get("name") for n in gltf.get("nodes",[]) if "mesh" in n]
assert suit.name in names and any(x.startswith("Cuervo_Botin_CC0") for x in names),names
assert len(gltf.get("skins",[]))>0
stats["exported_mesh_nodes"]=names
stats["shoe_source_license"]="CC0 per MakeHuman Community shoes01 pack"
stats["blender_file"]=os.path.basename(blend_file)
stats["godot_glb_file"]=os.path.basename(glb_file)
stats["suit_triangles"]=tris(suit)
stats["shoes_triangles"]=sum(tris(o) for o in shoes)
stats["total_visible_triangles_blender"]=stats["suit_triangles"]+stats["shoes_triangles"]+stats["visible_skin_faces_after_shoes"]
stats["artistic_approval"]=False
stats["cloth_clipping_qa_done"]=False
stats["android_fps_measured"]=False
stats["game_changed"]=False
stats["note"]="Real CC0 tailored clothing and CC0 boot mesh. Skinning and sleeve poses preliminary."
with open(os.path.join(out,"Fase4_Auditoria.json"),"w",encoding="utf8") as f:
    json.dump(stats,f,ensure_ascii=False,indent=2)
print("CUERVO_FASE4_COMPLETED",json.dumps(stats,ensure_ascii=False),flush=True)
