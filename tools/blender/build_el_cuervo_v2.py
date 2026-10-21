#!/usr/bin/env python3
"""El Cuervo 2.0: a fitted, anatomical, mobile-ready procedural 3D character.

Creates real editable meshes, materials and armature in Blender.
Faces -Y in Blender. Export selected geometry + armature as Godot-ready glTF GLB.
Style is deliberately semi-realistic / stylized, NOT a scanned photoreal human.

blender --background --python tools/blender/build_el_cuervo_v2.py -- --output out/blender
"""
import argparse
import math
import os
import sys
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--output",default="out/blender")
OUT = os.path.abspath(parser.parse_args(args).output)
os.makedirs(OUT,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for material_data in list(bpy.data.materials):
    bpy.data.materials.remove(material_data)

scene = bpy.context.scene
scene.unit_settings.system="METRIC"
scene.unit_settings.scale_length=1
parts=[]
materials={}

def mat(name,color,rough=.75,metal=.0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(*color,1)
        bsdf.inputs["Roughness"].default_value=rough
        bsdf.inputs["Metallic"].default_value=metal
    materials[name]=m
    return m

jacket=mat("01 Graphite technical jacket",(.060,.073,.081))
trousers=mat("02 Midnight slate trousers",(.071,.080,.096))
shirt=mat("03 Deep blue dress shirt",(.107,.140,.171))
plate=mat("04 Discreet armored insert",(.146,.168,.172),.66,.12)
black=mat("05 Black leather gloves and webbing",(.022,.027,.033),.56)
rubber=mat("06 Boot rubber sole",(.028,.032,.037),.93)
skin=mat("07 Natural warm skin",(.51,.352,.273),.91)
shadow=mat("08 Skin shadow and beard",(.215,.136,.116),.92)
hair=mat("09 Dark natural hair",(.028,.026,.027),.8)
eyes=mat("10 Pale eye whites",(.66,.64,.61),.7)
iris=mat("11 Deep brown iris",(.073,.045,.036),.44)
metal=mat("12 Brushed dark gunmetal",(.19,.225,.237),.45,.5)
thread=mat("13 Jacket stitch highlights",(.164,.179,.191))
accent=mat("14 Muted amber indicator",(.62,.43,.21),.55)

def register(ob,name,bone,material):
    ob.name=name
    ob.data.materials.append(material)
    parts.append((ob,bone))
    return ob

def ellipsoid(name,center,scale,material,bone,seg=20,rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=center)
    o=bpy.context.object
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for f in o.data.polygons:
        f.use_smooth=True
    return register(o,name,bone,material)

def box(name,center,size,material,bone,bevel=.012):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel>0:
        mod=o.modifiers.new("Fabric bevel","BEVEL")
        mod.width=bevel
        mod.segments=2
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    mod.keep_sharp=True
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return register(o,name,bone,material)

def loft(name,rings,material,bone,segments=22,cap=True):
    """Consecutive ellipse rings (x,y,z,rx,ry), fitted to anatomical proportions."""
    vertices=[]
    faces=[]
    for x,y,z,rx,ry in rings:
        for i in range(segments):
            t=2*math.pi*i/segments
            vertices.append((x+rx*math.cos(t),y+ry*math.sin(t),z))
    for row in range(len(rings)-1):
        for i in range(segments):
            j=(i+1)%segments
            a=row*segments+i
            b=row*segments+j
            c=(row+1)*segments+j
            d=(row+1)*segments+i
            faces.append((a,b,c,d))
    if cap:
        faces.append(tuple(reversed(tuple(range(segments)))))
        faces.append(tuple((len(rings)-1)*segments+i for i in range(segments)))
    mesh=bpy.data.meshes.new(name+" geometry")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    for f in mesh.polygons:
        f.use_smooth=len(f.vertices)==4
    return register(ob,name,bone,material)

def curve_tube(name,points,radius,material,bone,resolution=4):
    cv=bpy.data.curves.new(name,"CURVE")
    cv.dimensions="3D"
    cv.resolution_u=2
    cv.bevel_depth=radius
    cv.bevel_resolution=resolution
    spline=cv.splines.new("POLY")
    spline.points.add(len(points)-1)
    for control,p in zip(spline.points,points):
        control.co=(*p,1)
    ob=bpy.data.objects.new(name,cv)
    bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target="MESH")
    ob=bpy.context.object
    return register(ob,name,bone,material)

# Anatomical proportion: 1.83m high. Shoulders ~0.53m, natural waist ~0.34m.
loft("Tailored torso silhouette",[
 (0,.025,1.605,.158,.120),(0,.025,1.575,.217,.127),
 (0,.028,1.515,.273,.151),(0,.028,1.380,.263,.158),
 (0,.028,1.225,.206,.142),(0,.018,1.075,.182,.134),
 (0,.014,1.035,.178,.127)],jacket,"Chest")
loft("Narrow fitted pelvis",[(0,.025,1.102,.185,.137),(0,.021,1.005,.201,.143),
 (0,.018,.965,.196,.138)],trousers,"Hips")
loft("Neck skin",[(0,.02,1.67,.084,.082),(0,.02,1.579,.080,.077)],skin,"Neck",20)
loft("Shirt collar",[(0,.021,1.67,.094,.09),(0,.023,1.61,.099,.103)],shirt,"Chest",20)

# Lapel tailoring: symmetrical fine angled dark blue strips on the sternum.
for sign,side in ((-1,"R"),(1,"L")):
    curve_tube("Tailored lapel edge "+side,[
      (sign*.091,-.132,1.575),(sign*.148,-.166,1.47),
      (sign*.100,-.160,1.365),(sign*.039,-.136,1.29)],.009,thread,"Chest")
    curve_tube("Lapel inner seam "+side,[
      (sign*.073,-.141,1.567),(sign*.118,-.162,1.45),
      (sign*.043,-.15,1.35)],.006,shirt,"Chest")
box("Concealed protective insert",(0,-.147,1.345),(.295,.021,.287),plate,"Chest",.014)
curve_tube("Front zipper",[(0,-.166,1.49),(0,-.168,1.11)],.004,black,"Chest")
box("Tie / low profile shirt strip",(0,-.167,1.452),(.025,.013,.205),black,"Chest",.005)

# Chest harness follows the torso, keeping silhouette light rather than bulky.
curve_tube("Discreet diagonal harness",[(-.198,-.165,1.50),
 (-.112,-.183,1.393),(-.020,-.179,1.289),(.093,-.150,1.193)],.020,black,"Chest",5)
box("Harness latch",(.008,-.189,1.295),(.051,.020,.054),metal,"Chest")
box("Belt", (0,-.003,1.045),(.392,.284,.062),black,"Hips",.025)
box("Belt buckle", (0,-.158,1.041),(.061,.021,.043),metal,"Hips",.01)
for x in (-.18,.18):
    box("Tailored belt loop", (x,-.14,1.051),(.023,.015,.090),jacket,"Hips")

# Skull / facial features: jaw narrows toward chin; no featureless balloon head.
loft("Head sculpt / brow cheek jaw",[
  (0,.007,1.865,.097,.098),
  (0,.003,1.839,.129,.127),
  (0,.000,1.792,.135,.132),
  (0,-.006,1.749,.130,.130),
  (0,-.004,1.701,.115,.119),
  (0,.002,1.663,.091,.094),
  (0,.007,1.642,.063,.068)],skin,"Head",28)

# Eye line is on the front (-Y). Brows, eyes and cheek folds are modest.
for sign,side in ((-1,"R"),(1,"L")):
    ellipsoid("Ear "+side,(sign*.131,.012,1.754),(.027,.044,.058),skin,"Head",16,10)
    ellipsoid("Ear inner "+side,(sign*.151,-.011,1.755),(.010,.026,.033),shadow,"Head",12,8)
    ellipsoid("Eye sclera "+side,(sign*.059,-.126,1.778),(.032,.010,.012),eyes,"Head",16,10)
    ellipsoid("Eye iris "+side,(sign*.060,-.135,1.777),(.013,.004,.012),iris,"Head",12,8)
    curve_tube("Upper eyelid "+side,[
       (sign*.025,-.126,1.788),(sign*.060,-.141,1.791),
       (sign*.091,-.124,1.786)],.005,shadow,"Head")
    curve_tube("Defined eyebrow "+side,[
       (sign*.023,-.128,1.813),(sign*.059,-.140,1.818),
       (sign*.099,-.120,1.812)],.008,hair,"Head")
    ellipsoid("Cheek structure "+side,(sign*.082,-.097,1.723),(.050,.025,.034),skin,"Head",14,9)
    curve_tube("Jaw shadow "+side,[
       (sign*.117,-.073,1.718),(sign*.094,-.088,1.674),
       (sign*.045,-.067,1.652)],.003,shadow,"Head")
loft("Nose bridge",[(0,-.130,1.812,.021,.019),
 (0,-.139,1.774,.022,.025),(0,-.154,1.736,.025,.024)],skin,"Head",16)
ellipsoid("Nose tip",(0,-.163,1.725),(.030,.026,.018),skin,"Head",16,9)
for sign in (-1,1):
    ellipsoid("Nostril "+str(sign),(sign*.020,-.177,1.717),(.007,.004,.006),shadow,"Head",10,6)
curve_tube("Lip shadow",[(-.039,-.109,1.686),(0,-.122,1.683),(.039,-.109,1.686)],.003,shadow,"Head")
ellipsoid("Chin detail",(0,-.084,1.663),(.037,.013,.013),skin,"Head",14,8)

# Short, close cropped natural hair with directionality and a few subtle tufts.
loft("Fitted hair cap",[(0,.003,1.888,.067,.078),
 (0,.005,1.865,.114,.119),(0,.013,1.840,.134,.132),
 (0,.024,1.817,.130,.129)],hair,"Head",28)
for i in range(8):
    x=-.103+i*.029
    curve_tube("Hair silhouette strand %02d"%i,[
      (x,.0,1.883),(x*.98,-.095,1.866),(x*.87,-.127,1.836)],
      .005,hair,"Head",3)

# Slim arms hang by the sides; reduced shoulder pads prevent Roblox proportions.
for sign,side in ((1,"L"),(-1,"R")):
    upper="UpperArm."+side
    lower="Forearm."+side
    hand="Hand."+side
    thigh="Thigh."+side
    shin="Shin."+side
    foot="Foot."+side
    x=sign*.305
    loft("Natural jacket upper arm "+side,[
      (x,.028,1.516,.105,.114),(sign*.337,.026,1.436,.103,.114),
      (sign*.357,.012,1.321,.086,.093),(sign*.362,.005,1.250,.080,.085)],jacket,upper,18)
    loft("Fitted forearm "+side,[
      (sign*.364,.008,1.257,.079,.085),(sign*.373,-.007,1.162,.078,.076),
      (sign*.383,-.021,1.063,.060,.063),(sign*.391,-.032,1.018,.058,.061)],shirt,lower,18)
    box("Low-profile elbow reinforcement "+side,(sign*.369,-.079,1.257),(.114,.022,.104),plate,lower,.015)
    curve_tube("Sleeve forearm seam "+side,[
      (sign*.313,-.061,1.208),(sign*.324,-.060,1.145),
      (sign*.334,-.049,1.080)],.006,thread,lower)
    loft("Gloved wrist "+side,[
      (sign*.392,-.036,1.036,.057,.062),
      (sign*.397,-.040,.992,.065,.066)],black,hand,16)
    ellipsoid("Gloved palm "+side,(sign*.398,-.046,.945),(.071,.046,.082),black,hand,16,12)
    # Four distinct gloved fingers and a thumb, each meshes skinned to the hand bone.
    for finger in range(4):
        fx=sign*(.354+finger*.027)
        length=(.077,.092,.083,.068)[finger]
        ellipsoid("Finger "+side+" "+str(finger),(fx,-.068,.878+(.092-length)*.18),
                  (.014,.017,length*.57),black,hand,10,7)
    ellipsoid("Thumb "+side,(sign*.329,-.086,.933),(.025,.025,.046),black,hand,12,8)

    # Narrow-fitted thighs and properly tapered shins to the boots.
    lx=sign*.112
    loft("Fitted trouser thigh "+side,[
      (lx,.016,1.005,.121,.134),
      (sign*.130,.014,.916,.127,.134),
      (sign*.139,.005,.771,.116,.126),
      (sign*.140,.008,.602,.096,.112),
      (sign*.141,.012,.553,.099,.109)],trousers,thigh,20)
    loft("Trouser calf "+side,[
      (sign*.142,.012,.556,.097,.104),
      (sign*.146,.026,.467,.108,.113),
      (sign*.147,.025,.352,.102,.109),
      (sign*.148,.017,.189,.078,.090)],jacket,shin,20)
    curve_tube("Outer leg seam "+side,[
      (sign*.244,-.003,.906),(sign*.243,-.005,.746),
      (sign*.239,-.005,.61)],.004,thread,thigh)
    ellipsoid("Slim tactical boot upper "+side,(sign*.151,-.002,.173),
              (.106,.106,.151),black,foot,16,12)
    ellipsoid("Boot sculpted toe "+side,(sign*.151,-.102,.079),
              (.118,.192,.078),rubber,foot,18,12)
    box("Boot sole "+side,(sign*.151,-.086,.034),(.245,.360,.046),rubber,foot,.017)
    for t in range(3):
        curve_tube("Boot laces "+side+" "+str(t),[
          (sign*.11,-.115,.225-t*.046),
          (sign*.151,-.126,.219-t*.046),
          (sign*.19,-.114,.225-t*.046)],.004,thread,foot)
    ellipsoid("Minimal kneepad "+side,(sign*.141,-.105,.559),
              (.082,.025,.063),plate,shin,16,8)

# Belt mounted holster, secure radio and flexible wiring.
box("Compact concealed pistol holster",(-.235,-.047,.946),(.071,.153,.222),black,"Hips",.022)
box("Radio case",(.235,.014,1.098),(.056,.089,.131),metal,"Hips",.012)
curve_tube("Radio antenna",[(.237,.011,1.166),(.248,.009,1.239)],.004,black,"Hips")
box("Discrete wrist comms",(.397,-.093,1.055),(.111,.018,.055),plate,"Forearm.L",.010)

# 17+ bones. This first pass is skinned with rigid per-part weights.
# Shoulder, knee and elbow meshes meet at joints; later pass: smooth weights and animations.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
rig=bpy.context.object
rig.name="El_Cuervo_2_Rig"
rig.data.name="Cuervo2_Skeleton"
for old in list(rig.data.edit_bones):
    rig.data.edit_bones.remove(old)

def bone(name,head,tail,parent=None):
    b=rig.data.edit_bones.new(name)
    b.head=head
    b.tail=tail
    if parent:
        b.parent=rig.data.edit_bones[parent]
    return b

bone("Hips",(0,0,1.01),(0,0,1.10))
bone("Spine",(0,0,1.10),(0,0,1.34),"Hips")
bone("Chest",(0,0,1.34),(0,0,1.56),"Spine")
bone("Neck",(0,0,1.56),(0,0,1.67),"Chest")
bone("Head",(0,0,1.67),(0,0,1.86),"Neck")
for sign,side in ((1,"L"),(-1,"R")):
    bone("UpperArm."+side,(sign*.264,.015,1.49),(sign*.358,.005,1.25),"Chest")
    bone("Forearm."+side,(sign*.358,.005,1.25),(sign*.391,-.025,1.02),"UpperArm."+side)
    bone("Hand."+side,(sign*.391,-.025,1.02),(sign*.399,-.045,.88),"Forearm."+side)
    bone("Thigh."+side,(sign*.116,0,.99),(sign*.141,0,.56),"Hips")
    bone("Shin."+side,(sign*.141,0,.56),(sign*.148,0,.18),"Thigh."+side)
    bone("Foot."+side,(sign*.148,0,.18),(sign*.148,-.14,.08),"Shin."+side)

bpy.ops.object.mode_set(mode="OBJECT")
rig.show_in_front=False
for obj,bone_name in parts:
    vg=obj.vertex_groups.new(name=bone_name)
    vg.add(list(range(len(obj.data.vertices))),1.0,"REPLACE")
    modifier=obj.modifiers.new("Skeletal deformation","ARMATURE")
    modifier.object=rig
    obj.parent=rig
    obj.matrix_parent_inverse=rig.matrix_world.inverted()

# Camera is only for PNG concept renders; it is excluded from GLB export.
scene.render.engine="BLENDER_WORKBENCH"
scene.render.resolution_x=640
scene.render.resolution_y=920
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.light="STUDIO"
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.display.shading.background_type="WORLD"
scene.world.color=(.048,.060,.073)

bpy.ops.object.camera_add(location=(0,-5,1.20))
camera=bpy.context.object
camera.name="TurntablePreviewCamera"
camera.data.type="ORTHO"
camera.data.ortho_scale=2.35
scene.camera=camera
preview=[
    ("01_Frente",(0,-5,1.43)),
    ("02_TresCuartos",(3.4,-4.0,1.35)),
    ("03_Perfil",(5,0,1.32)),
    ("04_Espalda",(0,5,1.38))
]
for label,location in preview:
    camera.location=location
    vector=Vector((0,0,.98))-camera.location
    camera.rotation_euler=vector.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(OUT,"El_Cuervo_2_"+label+".png")
    bpy.ops.render.render(write_still=True)

# Exclude preview camera from GLB; blend keeps both character and view.
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for part, _ in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active=rig
blend_file=os.path.join(OUT,"El_Cuervo_v2.blend")
glb_file=os.path.join(OUT,"El_Cuervo_v2.glb")
bpy.ops.wm.save_as_mainfile(filepath=blend_file,check_existing=False)
bpy.ops.export_scene.gltf(
  filepath=glb_file,export_format="GLB",use_selection=True,
  export_animations=False,export_yup=True)
print("EL_CUERVO_V2_EXPORT_OK")
print("MESH_PARTS",len(parts),"BONES",len(rig.data.bones),"MATERIALS",len(materials))
