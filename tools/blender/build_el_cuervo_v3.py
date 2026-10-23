#!/usr/bin/env python3
"""El Cuervo 3.0: three original assassin outfit variants, real Blender meshes.

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
parser.add_argument("--output",default="out/blender_v3")
parser.add_argument("--variant",choices=["A","B","C"],required=True)
OPTIONS = parser.parse_args(args)
VARIANT=OPTIONS.variant
OUT = os.path.abspath(OPTIONS.output)
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
    ellipsoid("Ear "+side,(sign*.131,.014,1.754),(.014,.025,.045),skin,"Head",16,10)
    ellipsoid("Ear inner "+side,(sign*.143,-.009,1.754),(.004,.014,.024),shadow,"Head",12,8)
    ellipsoid("Eye sclera "+side,(sign*.059,-.126,1.778),(.032,.010,.012),eyes,"Head",16,10)
    ellipsoid("Eye iris "+side,(sign*.060,-.135,1.777),(.013,.004,.012),iris,"Head",12,8)
    curve_tube("Upper eyelid "+side,[
       (sign*.025,-.126,1.788),(sign*.060,-.141,1.791),
       (sign*.091,-.124,1.786)],.005,shadow,"Head")
    curve_tube("Defined eyebrow "+side,[
       (sign*.023,-.128,1.813),(sign*.059,-.140,1.818),
       (sign*.099,-.120,1.812)],.008,hair,"Head")
    # Cheekbones are already formed by the tapered face mesh; no protruding spheres.
    curve_tube("Jaw shadow "+side,[
       (sign*.117,-.073,1.718),(sign*.094,-.088,1.674),
       (sign*.045,-.067,1.652)],.003,shadow,"Head")
loft("Nose bridge",[(0,-.130,1.812,.021,.019),
 (0,-.139,1.774,.022,.025),(0,-.154,1.736,.025,.024)],skin,"Head",16)
ellipsoid("Nose tip",(0,-.159,1.728),(.023,.017,.014),skin,"Head",16,9)
for sign in (-1,1):
    ellipsoid("Nostril "+str(sign),(sign*.016,-.171,1.716),(.005,.003,.004),shadow,"Head",10,6)
curve_tube("Lip shadow",[(-.039,-.109,1.686),(0,-.122,1.683),(.039,-.109,1.686)],.003,shadow,"Head")
ellipsoid("Chin detail",(0,-.084,1.663),(.037,.013,.013),skin,"Head",14,8)

# Short, close cropped natural hair with directionality and a few subtle tufts.
loft("Fitted hair cap",[(0,.003,1.888,.067,.078),
 (0,.005,1.865,.114,.119),(0,.013,1.840,.134,.132),
 (0,.024,1.817,.130,.129)],hair,"Head",28)
for i in range(8):
    x=-.103+i*.029
    curve_tube("Hair silhouette strand %02d"%i,[
      (x,.0,1.876),(x*.98,-.091,1.863),(x*.87,-.126,1.842)],
      .0028,hair,"Head",3)

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
      (x,.028,1.516,.088,.101),(sign*.337,.026,1.436,.085,.102),
      (sign*.357,.012,1.321,.078,.084),(sign*.362,.005,1.250,.075,.081)],jacket,upper,18)
    loft("Fitted forearm "+side,[
      (sign*.364,.008,1.257,.079,.085),(sign*.373,-.007,1.162,.078,.076),
      (sign*.383,-.021,1.063,.060,.063),(sign*.391,-.032,1.018,.058,.061)],shirt,lower,18)
    box("Low-profile elbow reinforcement "+side,(sign*.369,-.079,1.257),(.083,.012,.082),jacket,lower,.010)
    curve_tube("Sleeve forearm seam "+side,[
      (sign*.313,-.061,1.208),(sign*.324,-.060,1.145),
      (sign*.334,-.049,1.080)],.006,thread,lower)
    loft("Gloved wrist "+side,[
      (sign*.392,-.036,1.036,.057,.062),
      (sign*.397,-.040,.992,.065,.066)],black,hand,16)
    ellipsoid("Gloved palm "+side,(sign*.398,-.046,.945),(.059,.036,.077),black,hand,16,12)
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
              (.099,.149,.064),rubber,foot,18,12)
    box("Boot sole "+side,(sign*.151,-.086,.034),(.210,.300,.035),rubber,foot,.014)
    for t in range(3):
        curve_tube("Boot laces "+side+" "+str(t),[
          (sign*.11,-.115,.225-t*.046),
          (sign*.151,-.126,.219-t*.046),
          (sign*.19,-.114,.225-t*.046)],.004,thread,foot)
    box("Flush knee reinforcement "+side,(sign*.141,-.101,.557),
        (.118,.017,.093),trousers,shin,.013)

# Belt mounted holster, secure radio and flexible wiring.
box("Compact concealed pistol holster",(-.235,-.047,.946),(.071,.153,.222),black,"Hips",.022)
box("Radio case",(.235,.014,1.098),(.056,.089,.131),metal,"Hips",.012)
curve_tube("Radio antenna",[(.237,.011,1.166),(.248,.009,1.239)],.004,black,"Hips")
box("Discrete wrist comms",(.397,-.093,1.055),(.085,.010,.038),black,"Forearm.L",.007)


# This redesign is based on our original fitted body meshes, not the image itself.
# Distinct production styles share a rig but alter tailoring, material and equipment.
def tint(material_obj, rgb, roughness=None):
    material_obj.diffuse_color = (*rgb, 1)
    bsdf = material_obj.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        if roughness is not None:
            bsdf.inputs["Roughness"].default_value = roughness

def discard_matching(*fragments):
    for ob, assigned_bone in parts[:]:
        if any(fragment in ob.name for fragment in fragments):
            parts.remove((ob, assigned_bone))
            bpy.data.objects.remove(ob, do_unlink=True)

def flat_fabric(name, vertices, material_obj, bone_name):
    """Double-sided tailored cloth inset; 3D mesh with thickness, not a 2D picture."""
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata(vertices, [], [tuple(range(len(vertices)))])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    ob = register(obj, name, bone_name, material_obj)
    solid = ob.modifiers.new("Tailored cloth thickness", "SOLIDIFY")
    solid.thickness = 0.018
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier=solid.name)
    return ob

def long_hair(material_obj, side="L"):
    sign=1 if side=="L" else -1
    for idx in range(5):
        cx=sign*(.076 + idx*.013)
        curve_tube("Medium swept hair "+side+" "+str(idx),[
            (cx,-.055,1.875),
            (cx+sign*.019,-.110,1.855),
            (cx+sign*.018,-.124,1.813)],.008,material_obj,"Head")

suit_black=mat("V3 Tailored midnight black",(.024,.028,.034),.79)
dress_shirt=mat("V3 Black dress shirt",(.048,.055,.065),.82)
tie_material=mat("V3 Satin black tie",(.018,.020,.024),.37)
dark_trim=mat("V3 Dark woven collar",(.068,.083,.091),.78)
coat_mat=mat("V3 Layered black wool coat",(.036,.045,.054),.86)
hardware=mat("V3 Low sheen fastenings",(.14,.155,.164),.55,.22)

# Several original prototype tactical parts are absent on the elegant directions.
if VARIANT == "A":
    discard_matching("protective insert", "diagonal harness", "Harness latch",
        "radio", "Radio", "Discrete wrist", "Outer leg seam",
        "Flush knee reinforcement", "Boot laces", "Low-profile elbow", "Elbow")
    tint(jacket,(.025,.031,.039))
    tint(trousers,(.029,.035,.043))
    tint(shirt,(.035,.041,.049))
    tint(plate,(.030,.036,.044))
    tint(rubber,(.028,.028,.032),.42)
    tint(hair,(.023,.022,.023))
    # Tailored lapels, visible tie, and slim jacket instead of an armoured vest.
    flat_fabric("Formal left suit lapel",[
        (-.074,-.159,1.59),(-.216,-.157,1.52),(-.112,-.181,1.335),
        (-.021,-.169,1.247)],suit_black,"Chest")
    flat_fabric("Formal right suit lapel",[
        (.074,-.159,1.59),(.216,-.157,1.52),(.112,-.181,1.335),
        (.021,-.169,1.247)],suit_black,"Chest")
    box("Silk tie knot",(0,-.187,1.555),(.066,.024,.055),tie_material,"Chest",.012)
    flat_fabric("Narrow formal black tie",[
        (-.024,-.184,1.52),(.024,-.184,1.52),(.030,-.183,1.232),
        (0,-.187,1.197),(-.030,-.183,1.232)],tie_material,"Chest")
    for side,sg in (("L",1),("R",-1)):
        box("Jacket side pocket "+side,(sg*.171,-.129,1.165),(.091,.012,.013),hardware,"Chest",.003)
    # Leather city shoes take the place of heavy-looking boots.
    for ob,bn in parts:
        if "Boot" in ob.name:
            ob.data.materials.clear()
            ob.data.materials.append(suit_black)
    for side in ("L","R"):
        long_hair(hair,side)

elif VARIANT == "B":
    tint(jacket,(.034,.044,.052))
    tint(trousers,(.041,.053,.062))
    tint(shirt,(.040,.052,.065))
    tint(plate,(.095,.111,.117))
    # Keep low profile armour and add practical fitted gear, not bulky sci-fi pads.
    flat_fabric("Practical fitted lapel left",[
        (-.075,-.156,1.592),(-.201,-.164,1.505),
        (-.111,-.177,1.353),(-.036,-.170,1.290)],suit_black,"Chest")
    flat_fabric("Practical fitted lapel right",[
        (.075,-.156,1.592),(.201,-.164,1.505),
        (.111,-.177,1.353),(.036,-.170,1.290)],suit_black,"Chest")
    box("Concealed suit chest pocket",(.190,-.134,1.411),(.102,.018,.010),hardware,"Chest",.003)
    box("Compact belt pouch",(.255,-.004,1.012),(.080,.137,.101),black,"Hips",.020)
    box("Thigh holster strap right",(-.165,-.115,.805),(.254,.029,.034),black,"Thigh.R",.008)
    box("Holster fabric plate right",(-.226,-.125,.830),(.083,.044,.165),black,"Thigh.R",.018)
    for side in ("L","R"):
        long_hair(hair,side)

elif VARIANT == "C":
    discard_matching("Concealed protective insert", "diagonal harness",
        "Harness latch", "Radio", "radio", "Discrete wrist",
        "Flush knee reinforcement")
    tint(jacket,(.029,.037,.043))
    tint(trousers,(.038,.045,.053))
    tint(shirt,(.026,.034,.042))
    tint(plate,(.054,.063,.069))
    tint(hair,(.028,.025,.029))
    # Distinct long, split coat silhouette with a raised protective collar.
    # Panels attach to pelvis and thighs; they are not simulated cloth yet.
    flat_fabric("Long coat back",[
        (-.236,.111,1.396),(.236,.111,1.396),
        (.300,.154,.635),(-.300,.154,.635)],coat_mat,"Hips")
    flat_fabric("Long coat front left",[
        (-.260,-.127,1.383),(-.105,-.174,1.395),
        (-.095,-.186,.638),(-.297,-.137,.660)],coat_mat,"Hips")
    flat_fabric("Long coat front right",[
        (.260,-.127,1.383),(.105,-.174,1.395),
        (.095,-.186,.638),(.297,-.137,.660)],coat_mat,"Hips")
    flat_fabric("Long coat side left",[
        (-.263,.016,1.378),(-.264,-.116,1.375),
        (-.315,-.129,.663),(-.305,.066,.650)],coat_mat,"Hips")
    flat_fabric("Long coat side right",[
        (.263,.016,1.378),(.264,-.116,1.375),
        (.315,-.129,.663),(.305,.066,.650)],coat_mat,"Hips")
    loft("High stealth collar",[
        (0,.032,1.685,.108,.095),
        (0,.040,1.635,.140,.122),
        (0,.035,1.597,.146,.131)],coat_mat,"Chest",24)
    loft("High-neck dark inner",[
        (0,.013,1.642,.089,.081),
        (0,.015,1.598,.098,.084)],dark_trim,"Neck",24)
    curve_tube("Coat zipper detail",[
        (0,-.188,1.567),(0,-.177,1.326),(0,-.168,1.100)],.005,hardware,"Chest")
    box("Hidden chest radio",(.21,-.143,1.342),(.066,.020,.106),black,"Chest",.013)
    for side in ("L","R"):
        long_hair(hair,side)
        sg=1 if side=="L" else -1
        ellipsoid("Long rear hair tufts "+side,(
            sg*.102,.115,1.769),(.041,.030,.123),hair,"Head",12,9)


# 17+ bones. This first pass is skinned with rigid per-part weights.
# Shoulder, knee and elbow meshes meet at joints; later pass: smooth weights and animations.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
rig=bpy.context.object
rig.name="El_Cuervo_3_Rig_"+VARIANT
rig.data.name="Cuervo3_Skeleton_"+VARIANT
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
    ("02_TresCuartos",(3.4,-4.0,1.35))
]
for label,location in preview:
    camera.location=location
    vector=Vector((0,0,.98))-camera.location
    camera.rotation_euler=vector.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(OUT,"El_Cuervo_3_"+VARIANT+"_"+label+".png")
    bpy.ops.render.render(write_still=True)

# Exclude preview camera from GLB; blend keeps both character and view.
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for part, _ in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active=rig
blend_file=os.path.join(OUT,"El_Cuervo_3_"+VARIANT+".blend")
glb_file=os.path.join(OUT,"El_Cuervo_3_"+VARIANT+".glb")
bpy.ops.wm.save_as_mainfile(filepath=blend_file,check_existing=False)
bpy.ops.export_scene.gltf(
  filepath=glb_file,export_format="GLB",use_selection=True,
  export_animations=False,export_yup=True)
print("EL_CUERVO_V3_EXPORT_OK",VARIANT)
print("MESH_PARTS",len(parts),"BONES",len(rig.data.bones),"MATERIALS",len(materials))
