"""El Cuervo | Fase 3 bis. Genuine Margaret Toigo CC0 suit meshes, not primitives.
Blender 4.3: blender -b --python ... -- --blend verified.blend --zip suits01_cc0.zip --out folder
Candidates are separate WIP studies. No automatic artistic approval; no game integration.
"""
import bpy,bmesh,sys,os,json,zipfile,struct,hashlib,math
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
def arg(name):
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return a[a.index(name)+1]
src=os.path.abspath(arg("--blend")); archive=os.path.abspath(arg("--zip"))
out=os.path.abspath(arg("--out"))
assert os.path.isfile(src) and zipfile.is_zipfile(archive)
os.makedirs(out,exist_ok=True)
unpack="/tmp/cuervo_cc0_suits01"
os.makedirs(unpack,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        dest=os.path.abspath(os.path.join(unpack,member.filename))
        assert os.path.commonpath((unpack,dest))==unpack
    z.extractall(unpack)
bpy.ops.wm.open_mainfile(filepath=src)
scene=bpy.context.scene
arms=[o for o in scene.objects if o.type=="ARMATURE"]
assert len(arms)==1,"Only one original human rig expected"
arm=arms[0]
body=[o for o in scene.objects if o.type=="MESH" and (o.parent==arm or
    any(m.type=="ARMATURE" and m.object==arm for m in o.modifiers))]
assert body
bpy.context.view_layer.update()
def bounds(objects):
    points=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
    return Vector([min(p[k] for p in points) for k in range(3)]),Vector([max(p[k] for p in points) for k in range(3)])
low,high=bounds(body)
height=high.z-low.z
assert abs(height-1.84)<.016,height
center=(low+high)*.5
groups=set(g.name for o in body for g in o.vertex_groups)
assert len(groups)>50
samples=[]
tree=KDTree(sum(len(o.data.vertices) for o in body))
for ob in body:
    for v in ob.data.vertices:
        i=len(samples)
        tree.insert(ob.matrix_world@v.co,i)
        samples.append((ob,v.index))
tree.balance()
def count_triangles(o):return sum(len(face.vertices)-2 for face in o.data.polygons)
def fit(objects):
    mn,mx=bounds(objects)
    dim=mx-mn
    # MakeHuman source OBJ uses Y-up; Blender OBJ importer converts to Z-up.
    assert 0.05<dim.x<100 and 0.05<dim.y<100 and 0.05<dim.z<100,dim
    bottom=low.z+.085
    top=low.z+height*.95
    sz=(top-bottom)/dim.z
    sx=max(.76*sz,min(1.30*sz,(high.x-low.x+.090)/dim.x))
    sy=max(.76*sz,min(1.30*sz,(high.y-low.y+.070)/dim.y))
    mid=(mn+mx)*.5
    transform=(Matrix.Translation(Vector((center.x,center.y,bottom))) @
               Matrix.Diagonal(Vector((sx,sy,sz,1))) @
               Matrix.Translation(Vector((-mid.x,-mid.y,-mn.z))))
    for ob in objects:ob.matrix_world=transform@ob.matrix_world
    bpy.context.view_layer.update()
    nlo,nhi=bounds(objects)
    return dict(source_dimensions=list(dim),scale=[sx,sy,sz],fitted_min=list(nlo),fitted_max=list(nhi))

def improve_fit(obj):
    """Non-destructively refine an existing ARTIST-AUTHORED suit mesh, not generate tubes.
    MakeHuman clothing sleeves rest slightly higher/wider than this particular rig.
    A graded 13-degree sleeve rotation plus collar lowering realigns the garment.
    Manual animation QA is still required.
    """
    mw=obj.matrix_world.copy(); inv=mw.inverted()
    sh_z=low.z+height*.80
    sh_x=.29
    for v in obj.data.vertices:
        pos=mw@v.co
        orig=pos.copy()
        zrel=pos.z-low.z
        if zrel>1.50:
            u=max(0,min(1,(zrel-1.50)/.22))
            pos.z-=.100*(u*u*(3-2*u))
        ax=abs(pos.x-center.x)
        zrel=pos.z-low.z
        if ax>.30 and .90<zrel<1.66:
            t=max(0,min(1,(ax-.30)/.16))
            t=t*t*(3-2*t)
            side=1 if pos.x>=center.x else -1
            dx=ax-sh_x
            dz=pos.z-sh_z
            a=.23
            rx=sh_x+dx*math.cos(a)+dz*math.sin(a)
            rz=sh_z-dx*math.sin(a)+dz*math.cos(a)
            pos.x=center.x+side*((1-t)*ax+t*rx)
            pos.z=(1-t)*pos.z+t*rz
        v.co=inv@pos
    obj.data.update()
    bpy.context.view_layer.update()


def remove_tie_component(obj):
    """Remove isolated tie geometry from the suit3 source; retain modelled shirt.
    Only accepts a narrow, central, detached mesh island in the upper chest.
    This is real topology editing; not a primitive replacement or a texture fake.
    """
    b=bmesh.new()
    b.from_mesh(obj.data)
    visited=set()
    deletes=[]
    matches=[]
    for first in b.faces:
        if first in visited: continue
        group=[]
        stack=[first]
        while stack:
            face=stack.pop()
            if face in visited:continue
            visited.add(face)
            group.append(face)
            for v in face.verts:
                for neighbor in v.link_faces:
                    if neighbor not in visited:stack.append(neighbor)
        if len(group)<200:continue
        points=[obj.matrix_world@v.co for face in group for v in face.verts]
        left=min(p.x for p in points);right=max(p.x for p in points)
        bot=min(p.z for p in points);top=max(p.z for p in points)
        if right-left<.15 and 1.30<bot<1.56 and top<1.75 and len(group)>280:
            deletes.extend(group)
            matches.append(dict(faces=len(group),bounds=[left,right,bot,top]))
    assert len(matches)==1,("Expected exactly one detached tie island",matches)
    bmesh.ops.delete(b,geom=deletes,context="FACES")
    bmesh.ops.delete(b,geom=[v for v in b.verts if not v.link_faces],context="VERTS")
    b.to_mesh(obj.data)
    b.free()
    obj.data.update()
    print("DETACHED_TIE_REMOVED",matches,flush=True)
    return matches

def make_visible_skin():
    """Keep head, distal hands and feet from the real MakeHuman body.
    Preserve the FULL untouched reference body, hidden in BLEND; do not
    let unclothed torso/legs poke through a single-sided cloth shell.
    """
    visible=[]
    for original in body:
        copy=original.copy()
        copy.data=original.data.copy()
        copy.name="VisibleSkin_"+original.name
        scene.collection.objects.link(copy)
        meshbm=bmesh.new()
        meshbm.from_mesh(copy.data)
        def exposed(vertex):
            world=copy.matrix_world@vertex.co
            zz=world.z-low.z
            xx=abs(world.x-center.x)
            return zz>1.52 or (xx>.49 and .68<zz<1.51) or zz<.13
        deleted=[face for face in meshbm.faces if not all(exposed(v) for v in face.verts)]
        bmesh.ops.delete(meshbm,geom=deleted,context="FACES")
        bmesh.ops.delete(meshbm,geom=[v for v in meshbm.verts if not v.link_faces],context="VERTS")
        meshbm.to_mesh(copy.data)
        meshbm.free()
        copy.data.update()
        visible.append(copy)
        original.hide_render=True
    bpy.context.view_layer.update()
    assert sum(count_triangles(x) for x in visible)>1000
    return visible

def colored_texture(ob,sourcefile,suit):
    # OBJ packs use MakeHuman MHMat atlases, usually not MTL. Load their actual UV texture.
    dirname=os.path.dirname(sourcefile)
    images=[f for f in os.listdir(dirname) if f.lower().endswith(".png") and
            not any(x in f.lower() for x in ("norm","spec","bump","thumb"))]
    imagefile=next((x for x in images if "diff" in x.lower()),images[0] if images else None)
    material=bpy.data.materials.new("Cuervo_Real_Fabric_CC0_"+suit)
    material.use_nodes=True
    nodes=material.node_tree.nodes
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value=.82
    if imagefile:
        tex=nodes.new("ShaderNodeTexImage")
        tex.image=bpy.data.images.load(os.path.join(dirname,imagefile),check_existing=True)
        shade=nodes.new("ShaderNodeMixRGB")
        shade.blend_type="MULTIPLY"
        shade.inputs[0].default_value=1
        shade.inputs[2].default_value=(.27,.28,.31,1)
        material.node_tree.links.new(tex.outputs["Color"],shade.inputs[1])
        material.node_tree.links.new(shade.outputs["Color"],bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value=(.03,.035,.045,1)
    ob.data.materials.clear()
    ob.data.materials.append(material)
    return imagefile
def skin_weights(ob):
    vgroups={name:ob.vertex_groups.new(name=name) for name in sorted(groups)}
    bound=0
    for vertex in ob.data.vertices:
        nearest,index,d=tree.find(ob.matrix_world@vertex.co)
        source,vi=samples[index]
        sv=source.data.vertices[vi]
        copied=False
        for value in sv.groups:
            name=source.vertex_groups[value.group].name
            if name in vgroups and value.weight>.0001:
                vgroups[name].add([vertex.index],value.weight,"REPLACE")
                copied=True
        bound+=int(copied)
    assert bound==len(ob.data.vertices),(ob.name,bound,len(ob.data.vertices))
    modifier=ob.modifiers.new("CC0_Suit_Skin_WIP","ARMATURE")
    modifier.object=arm
def preview(name,position,target,scale):
    cam=scene.camera
    assert cam
    target=Vector(target)
    cam.location=target+Vector(position)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO"
    cam.data.ortho_scale=scale
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>4000,name
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=10
scene.cycles.use_denoising=True
scene.render.resolution_x=672
scene.render.resolution_y=880
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
assets=[]
for root,dirs,files in os.walk(unpack):
    if os.path.basename(root).lower().startswith("toigo_male"):
        for file in files:
            if file.lower().endswith(".obj"):
                assets.append((os.path.basename(root).lower(),os.path.join(root,file)))
wanted=("toigo_male_suit_3","toigo_male_suit_tie_and_jacket")
picked=[(name,next(path for kind,path in assets if kind==name)) for name in wanted
        if any(kind==name for kind,path in assets)]
assert len(picked)==2,("Expected original authored male suits missing",assets)
reports=[]
for label,filepath in picked:
    existing=set(scene.objects)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.obj_import(filepath=filepath,forward_axis="NEGATIVE_Z",up_axis="Y")
    imported=[o for o in scene.objects if o not in existing]
    meshes=[o for o in imported if o.type=="MESH"]
    assert meshes,label
    ntris=sum(count_triangles(o) for o in meshes)
    assert ntris>2000 and ntris<250000,(label,ntris)
    f=fit(meshes)
    for mesh in meshes: improve_fit(mesh)
    removed_ties=[]
    if label=="toigo_male_suit_3":
        for mesh in meshes:
            removed_ties+=remove_tie_component(mesh)
    visible=make_visible_skin()
    textures=[]
    for j,obj in enumerate(meshes):
        obj.name="CC0_"+label+"_"+str(j)
        textures.append(colored_texture(obj,filepath,label))
        skin_weights(obj)
    focus=(center.x,center.y,low.z+height*.52)
    preview(label+"_01_Frontal",(0,-4.5,.18),focus,2.27)
    preview(label+"_02_Tres_Cuartos",(3,-4,.16),focus,2.27)
    preview(label+"_03_Espalda",(0,4.5,.16),focus,2.27)
    preview(label+"_04_Detalle_Blazer",(1,-4,.08),
            (center.x,center.y,low.z+height*.74),1.12)
    bpy.ops.file.pack_all()
    blend=os.path.join(out,"El_Cuervo_"+label+"_TRAJE_REAL_WIP.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in visible+meshes+[arm]:obj.select_set(True)
    bpy.context.view_layer.objects.active=arm
    glb=os.path.join(out,"El_Cuervo_"+label+"_TRAJE_REAL_WIP.glb")
    bpy.ops.export_scene.gltf(filepath=glb,export_format="GLB",use_selection=True,
                              export_materials="EXPORT",export_yup=True)
    with open(glb,"rb") as stream:
        magic,version,size=struct.unpack("<4sII",stream.read(12))
        assert magic==b"glTF" and version==2 and size==os.path.getsize(glb)
    reports.append(dict(name=label,original_obj=os.path.relpath(filepath,unpack),
       original_mesh_triangles=ntris,mesh_count=len(meshes),
       original_uv_atlas=textures,fitted_bounds=f,
       armature_bones=len(arm.data.bones),body_base_preserved=True,
       masked_hidden_skin=True,clothing_arm_and_collar_fit_adjusted=True,
       removed_tie_mesh_islands=removed_ties,
       body_visible_triangles=sum(count_triangles(x) for x in visible),
       skinning_method="nearest-source-vertex trial, visually unapproved",
       artistic_approval=False,android_fps_tested=False,
       blend=os.path.basename(blend),glb=os.path.basename(glb)))
    for obj in imported+visible:
        bpy.data.objects.remove(obj,do_unlink=True)
    for original in body: original.hide_render=False
    bpy.context.view_layer.update()
with open(archive,"rb") as f:sha=hashlib.sha256(f.read()).hexdigest()
report=dict(source="MakeHuman Community CC0, suits01, Margaret Toigo",
    source_url="https://static.makehumancommunity.org/assets/assetpacks/suits01.html",
    archive_url="https://files2.makehumancommunity.org/asset_packs/suits01/suits01_cc0.zip",
    sha256=sha,candidates=reports,artistic_approval=False,
    Android_performance_approved=False,game_or_APK_modified=False,
    warning="Genuine authored garment OBJ, fitted approximately. WIP; requires anatomy and motion QC.")
with open(os.path.join(out,"AUDITORIA_TRAJES_REALES.json"),"w",encoding="utf8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print("EL_CUERVO_CC0_SUIT_MESHES_COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
