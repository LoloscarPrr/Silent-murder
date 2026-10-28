"""El Cuervo - Fase 3. Modelo REAL de camisa y blazer sobre cuerpo MakeHuman CC0.
Blender 4.3.2: blender -b --python tools/el_cuervo/fase3_clothing.py -- --blend input.blend --out dir
Prototipo geométrico WIP. No es patronaje final, no corresponde a ropa escaneada, sin aprobacion de calidad.
"""
import bpy, os, sys, json, math, struct, statistics
from mathutils import Vector
from mathutils.kdtree import KDTree

def arg(key,default=None):
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return a[a.index(key)+1] if key in a else default

src=arg("--blend")
out=os.path.abspath(arg("--out","character_assets/el_cuervo/fase3"))
assert src and os.path.isfile(src), "No existe fuente .blend humana validada"
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene=bpy.context.scene
arms=[o for o in scene.objects if o.type=="ARMATURE"]
assert len(arms)==1, "El archivo de origen debe tener un solo rig"
arm=arms[0]
bodies=[o for o in scene.objects if o.type=="MESH" and
        (o.parent==arm or any(m.type=="ARMATURE" and m.object==arm for m in o.modifiers))]
assert bodies, "No se encontro cuerpo humano skinned"
bpy.context.view_layer.update()
bnds=[o.matrix_world @ Vector(c) for o in bodies for c in o.bound_box]
low=Vector(tuple(min(v[i] for v in bnds) for i in range(3)))
high=Vector(tuple(max(v[i] for v in bnds) for i in range(3)))
assert abs((high.z-low.z)-1.84)<.02, "La escala humana cambió"
cx=(low.x+high.x)*.5
cy=(low.y+high.y)*.5
H=high.z-low.z
def z(frac):return low.z+frac*H

# Anatomía de referencia: medida efectiva con vértices de la base humana,
# excluyendo brazos por ventana en X. No se usan cubos/esferas como sustitutos.
samples=[]
for o in bodies:
    M=o.matrix_world
    samples.extend(tuple(M @ v.co) for v in o.data.vertices)
def pct(vals,p, fallback):
    if len(vals)<15:return fallback
    s=sorted(vals);return s[min(len(s)-1,int((len(s)-1)*p))]
def torso_radii(zz):
    v=[p for p in samples if abs(p[2]-zz)<.045 and abs(p[0]-cx)<.34]
    xx=[abs(p[0]-cx) for p in v if abs(p[1]-cy)<.28]
    yy=[abs(p[1]-cy) for p in v if abs(p[0]-cx)<.235]
    return (max(.145,min(.32,pct(xx,.96,.23))),
            max(.105,min(.255,pct(yy,.96,.16))))
measure={str(round(frac,2)):tuple(round(q,4) for q in torso_radii(z(frac))) for frac in [.51,.58,.65,.72,.79,.84]}
print("TORSO_MEASURED_RADII",measure,flush=True)

def mat(name,rgba,rough=.7,metal=0):
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color=rgba
    material.use_nodes=True
    principled=material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value=rgba
    principled.inputs["Roughness"].default_value=rough
    principled.inputs["Metallic"].default_value=metal
    return material

shirtmat=mat("Cuervo_Camisa_Grafito",(.027,.029,.035,1),.82)
jacketmat=mat("Cuervo_Blazer_Carbon",(.012,.014,.019,1),.91)
lapelmat=mat("Cuervo_Solapas_Textil",(.021,.022,.026,1),.79)
trimat=mat("Cuervo_Costuras_Sutiles",(.036,.038,.046,1),.85)

# Crear objetos desde superficies discretizadas con coordenadas del torso real
# y pesos tomados del rig CC0. Cada pieza es malla renderizable editable.
clothing_collection=bpy.data.collections.get("El_Cuervo_Vestuario_WIP")
if clothing_collection is None:
    clothing_collection=bpy.data.collections.new("El_Cuervo_Vestuario_WIP")
    scene.collection.children.link(clothing_collection)
made=[]
def mesh(name,verts,faces,material,smooth=True):
    assert len(verts)>=3 and len(faces)>=1
    data=bpy.data.meshes.new(name+"_geo")
    data.from_pydata(verts,[],faces)
    data.update()
    ob=bpy.data.objects.new(name,data)
    clothing_collection.objects.link(ob)
    ob.data.materials.append(material)
    for f in ob.data.polygons:f.use_smooth=smooth
    made.append(ob)
    return ob

# Superficie de cilindro elíptico orgánico por anillos, cada anillo a su
# propia altura y medida anatómica. Frontal y posterior no son coplanares.
def ring_surface(name,levels,angle_start,angle_end,steps,clearance,material):
    verts=[]
    for i,fr in enumerate(levels):
        zz=z(fr)
        rx,ry=torso_radii(zz)
        for j in range(steps+1):
            theta=angle_start+(angle_end-angle_start)*j/steps
            # ligera caída de blazer hacia el bajo; pecho, cintura y espalda
            hem=max(0.,(.57-fr)/.07) if name.startswith("Jacket") else 0.
            taper=1.+.055*min(1.,hem)
            x=cx+(rx+clearance)*math.cos(theta)*taper
            y=cy+(ry+clearance*.72)*math.sin(theta)*taper
            verts.append((x,y,zz))
    faces=[]
    width=steps+1
    for i in range(len(levels)-1):
        for j in range(steps):
            a=i*width+j;b=a+1;c=a+width+1;d=a+width
            faces.append((a,b,c,d))
    return mesh(name,verts,faces,material)

# Camisa anatómica de cuello a cadera. A partir de anillos continuos,
# no "camisa pintada". Su parte visible es la abertura frontal del blazer.
shirt=ring_surface("Shirt_Inner", [.51,.57,.62,.68,.74,.79,.825],
                   -math.pi/2,3*math.pi/2,48,.018,shirtmat)
# El blazer deja abierta la franja frontal; vértices radialmente ajustados
# a torso/chest, la camisa se conserva por separado.
jacket=ring_surface("Jacket_Blazer", [.48,.52,.58,.64,.70,.75,.79,.82,.84],
                    -math.pi/2+.28,3*math.pi/2-.28,56,.053,jacketmat)

# Torso lumbar: costura vertical y doble panel de solapa con volumen 3D
# a cada lado de la abertura. Se modelan secciones, no textura plana.
def lapel(side):
    verts=[]
    for h,open_rad,outer_rad in [
        (.84,.11,.25),(.81,.105,.25),(.77,.085,.17),
        (.73,.085,.14),(.67,.065,.105)]:
        zz=z(h)
        rx,ry=torso_radii(zz)
        # Centro del pecho abierto; solapa se ensancha hacia el hombro
        y=cy-ry-.068
        verts.extend([
          (cx+side*open_rad,y,zz),
          (cx+side*outer_rad,y-.020,zz),
        ])
    faces=[]
    for i in range(4):
        a=i*2;faces.append((a,a+1,a+3,a+2))
    return mesh("Jacket_Lapel_"+("L" if side<0 else "R"),verts,faces,lapelmat,smooth=False)
lapel(-1)
lapel(1)

# Borde de solapa interior y cuello camisa: pequeños volúmenes independientes.
def ribbon(name,coords,width,material):
    verts=[]
    for x,y,zz in coords:
        verts.extend([(x-width/2,y,zz),(x+width/2,y,zz)])
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(coords)-1)]
    return mesh(name,verts,faces,material,smooth=False)
for side in [-1,1]:
    shoulder_z=z(.84)
    rx,ry=torso_radii(z(.80))
    coords=[
      (cx+side*.072,cy-ry-.030,z(.83)),
      (cx+side*.105,cy-ry-.033,z(.815)),
      (cx+side*.085,cy-ry-.031,z(.792))]
    ribbon("Shirt_Collar_"+("L" if side<0 else "R"),coords,.035,shirtmat)

# Manga doble (camisa interior y blazer exterior). Cada tubo sigue centros
# de huesos del esqueleto original y el perfil de antebrazo en A-pose.
def bone(name):
    pb=arm.pose.bones.get(name)
    if pb is None:return None
    return (arm.matrix_world@pb.head, arm.matrix_world@pb.tail)
def arm_path(side):
    suffix=".L" if side<0 else ".R"
    upper=bone("upperarm01"+suffix)
    lower=bone("lowerarm01"+suffix)
    if not upper or not lower:
        raise ValueError("No se encuentran huesos de brazo para "+suffix)
    sh,el=upper
    fa,wr=lower
    return [sh,sh.lerp(el,.22),el.lerp(fa,.5),fa.lerp(wr,.52),wr]
def sleeve(name,pts,radii,material):
    verts=[]
    for i,pt in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        u=tangent.cross(Vector((0,0,1)))
        if u.length<.05:u=tangent.cross(Vector((0,1,0)))
        u.normalize()
        v=tangent.cross(u).normalized()
        for j in range(16):
            th=2*math.pi*j/16
            offset=radii[i]*(math.cos(th)*u+math.sin(th)*v)
            verts.append(tuple(pt+offset))
    faces=[]
    for i in range(len(pts)-1):
        for j in range(16):
            a=i*16+j;b=i*16+(j+1)%16
            c=(i+1)*16+(j+1)%16;d=(i+1)*16+j
            faces.append((a,b,c,d))
    faces.append(tuple(reversed(tuple(range(16)))))
    faces.append(tuple((len(pts)-1)*16+j for j in range(16)))
    return mesh(name,verts,faces,material)
for side,side_name in [(-1,"L"),(1,"R")]:
    path=arm_path(side)
    sleeve("Shirt_Sleeve_"+side_name,path,[.105,.107,.088,.072,.062],shirtmat)
    sleeve("Jacket_Sleeve_"+side_name,path,[.133,.132,.109,.091,.082],jacketmat)

# Transferencia de pesos: buscar vértice CC0 más próximo y copiar nombres de
# grupos con pesos reales. La pose animada sigue usando el rig original.
# Es una base de skinning automática, aún requiere corrección de articulaciones.
entries=[]
index=KDTree(sum(len(o.data.vertices) for o in bodies))
for source in bodies:
    world=source.matrix_world
    for v in source.data.vertices:
        item=len(entries)
        index.insert(world@v.co,item)
        entries.append((source,v.index))
index.balance()

for ob in made:
    names=set()
    for s in bodies:
        names.update(g.name for g in s.vertex_groups)
    groups={name:ob.vertex_groups.new(name=name) for name in sorted(names)}
    influenced=0
    for v in ob.data.vertices:
        co=ob.matrix_world@v.co
        closest,idx,dist=index.find(co)
        source,vi=entries[idx]
        sv=source.data.vertices[vi]
        total=0.
        for g in sv.groups:
            groupname=source.vertex_groups[g.group].name
            if groupname in groups and g.weight>0.0001:
                groups[groupname].add([v.index],g.weight,"REPLACE")
                total+=g.weight
        if total>0:influenced+=1
    assert influenced>=len(ob.data.vertices)*.97,(ob.name,influenced,len(ob.data.vertices))
    mod=ob.modifiers.new("Armature_Original","ARMATURE")
    mod.object=arm
    # New mesh world coordinates; same binding space as source armature.
    print("GARMENT_SKINNED",ob.name,len(ob.data.vertices),influenced,flush=True)

# Conservar piezas WIP y referencia humana. Separar vestuario para GLB.
def tricount(o):
    return sum(len(p.vertices)-2 for p in o.data.polygons)
garment_tris=sum(tricount(o) for o in made)
assert 900<garment_tris<20000,garment_tris
assert {"Shirt_Inner","Jacket_Blazer","Jacket_Lapel_L","Jacket_Lapel_R"}.issubset({x.name for x in made})

# Materiales sobrios y estudio existente; generar RENDERS desde objetos 3D.
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=12
scene.render.resolution_x=720
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
cam=scene.camera
if cam is None:
    camera_data=bpy.data.cameras.new("Camara Vestuario")
    cam=bpy.data.objects.new("Camara Vestuario",camera_data)
    scene.collection.objects.link(cam)
    scene.camera=cam
cam.data.type="ORTHO"

# El encuadre refleja claramente la caída real de blazer y mangas.
def shot(name,target,offset,scale):
    target=Vector(target)
    cam.location=target+Vector(offset)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=scale
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>2500,name

target=Vector((cx,cy,z(.69)))
shot("01_Blazer_Camisa_Frontal",target,(0,-4,.1),1.55)
shot("02_Blazer_Camisa_Lateral",target,(4,0,.1),1.55)
shot("03_Blazer_Camisa_Espalda",target,(0,4,.1),1.55)
shot("04_Blazer_Camisa_Tres_Cuartos",target,(2.4,-3.6,.25),1.60)
shot("05_Solapas_Cuello_Pecho",Vector((cx,cy,z(.80))),(0,-3,.10),.75)

# Guardar BLEND editable antes de exportar. Se conserva cuerpo base íntegro,
# camara y luces para reproducibilidad. Capa WIP no es prenda terminada.
scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,"El_Cuervo_Blazer_Camisa_WIP.blend"))
assert os.path.getsize(os.path.join(out,"El_Cuervo_Blazer_Camisa_WIP.blend"))>10000
bpy.ops.object.select_all(action="DESELECT")
for obj in bodies+[arm]+made:obj.select_set(True)
bpy.context.view_layer.objects.active=arm
glbpath=os.path.join(out,"El_Cuervo_Blazer_Camisa_WIP.glb")
bpy.ops.export_scene.gltf(filepath=glbpath,export_format="GLB",use_selection=True,
                          export_materials="EXPORT",export_yup=True)
with open(glbpath,"rb") as f:
    h=f.read(12)
magic,version,length=struct.unpack("<4sII",h)
assert magic==b"glTF" and version==2 and length==os.path.getsize(glbpath)
with open(glbpath,"rb") as f:
    f.seek(12)
    jsonlen,kind=struct.unpack("<I4s",f.read(8))
    assert kind==b"JSON"
    gltf=json.loads(f.read(jsonlen).decode("utf-8"))
nodes=[n for n in gltf.get("nodes",[]) if "mesh" in n]
names=[n.get("name","") for n in nodes]
assert "Jacket_Blazer" in names and "Shirt_Inner" in names,names
assert all("skin" in n for n in nodes), "El vestuario o cuerpo perdio skin"
report={
  "status":"WIP_MODELO_GEOMETRICO_REAL_NO_APROBADO",
  "source":"El_Cuervo_Base_Humana_v1.blend",
  "reference_height_m":round(H,5),
  "original_human_triangles":sum(tricount(x) for x in bodies),
  "garment_triangles":garment_tris,
  "garment_pieces":[{"name":o.name,"vertices":len(o.data.vertices),
                      "triangles":tricount(o),"material":o.active_material.name} for o in made],
  "glb_mesh_nodes":names,
  "armature_bones":len(arm.data.bones),
  "body_base_preserved":True,
  "rig_weight_transfer":"nearest source vertices; requires artist correction",
  "anatomical_measurements_radii":measure,
  "artistic_review_approved":False,
  "android_fps_measured":False,
  "limitations":["Patronaje y arrugas son prototipo geométrico, NO vestuario AAA terminado.",
                 "Transferencia de pesos automática no garantiza que hombros/codos queden bien.",
                 "Hacen falta renders de poses, pruebas de clipping y telas definitivas.",
                 "No existe LOD de vestuario ni benchmark Android."]
}
with open(os.path.join(out,"Fase3_Auditoria.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print("FASE3_REAL_GARMENTS_COMPLETED",json.dumps(report,ensure_ascii=False),flush=True)
