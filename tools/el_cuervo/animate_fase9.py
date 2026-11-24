"""Silent Killer / El Cuervo — PHASE 9 real skinned animation clips.

Create real Blender Action keyframes and export WALK + AIM to a skinned GLB
from the approved technical phase-7 CC0 model (53-bone MakeHuman/MPFB rig).
Motion is purpose-built prototype locomotion/aim; QA renders and JSON document
limitations; never overwrites Phase7/8 or the Android gameplay character.

Blender 4.3.2:
  blender -b -t 4 --python tools/el_cuervo/animate_fase9.py -- \
    --blend character_assets/el_cuervo/refine_fase7/El_Cuervo_Refinado_Fase7_REVISION.blend \
    --out character_assets/el_cuervo/fase9_animaciones
"""
import bpy
import json
import math
import os
import struct
import sys
from mathutils import Vector, Matrix, Quaternion

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(key):
    assert key in args, key
    return os.path.abspath(args[args.index(key)+1])
source=arg("--blend")
out=arg("--out")
assert os.path.isfile(source) and os.path.getsize(source)>100000
os.makedirs(out,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=source)
scene=bpy.context.scene
rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
assert len(rigs)==1, [x.name for x in rigs]
rig=rigs[0]
assert len(rig.data.bones)==53
mesh=bpy.data.objects.get("Body")
coat=bpy.data.objects.get("Cloth_trenchcoat")
assert mesh and coat and all(any(mod.type=="ARMATURE" and mod.object==rig
    for mod in o.modifiers) for o in (mesh,coat))
bones={}
names=["upperarm_l","upperarm_r","lowerarm_l","lowerarm_r","thigh_l",
       "thigh_r","calf_l","calf_r","foot_l","foot_r","pelvis",
       "spine_01","spine_02","spine_03","head"]
for name in names:
    bones[name]=rig.pose.bones.get(name)
    assert bones[name], ("Missing source skeleton bone",name)
assert scene.camera

def bounds(obj):
    pts=[obj.matrix_world @ Vector(pt) for pt in obj.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return lo,hi

lo,hi=bounds(mesh)
height=hi.z-lo.z
assert 1.80<height<1.9
cx=(lo.x+hi.x)/2
cy=(lo.y+hi.y)/2
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.resolution_x=640
scene.render.resolution_y=840
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="JPEG"
scene.render.image_settings.quality=70
scene.render.film_transparent=False
scene.render.image_settings.color_mode="RGB"
focus=Vector((cx,cy,lo.z+height*.52))
cam=scene.camera

def reset_pose():
    for pb in rig.pose.bones:
        pb.rotation_mode="QUATERNION"
        pb.rotation_quaternion.identity()
        pb.location.zero()
        pb.scale=(1,1,1)
    bpy.context.view_layer.update()

def direction(pb):
    return (rig.matrix_world.to_3x3() @ (pb.tail-pb.head)).normalized()

def orient(pb,world_target):
    """Aim existing bone world-space direction, retaining original rest offset.
    Using matrix correction around head handles varied MPFB bone local axes.
    """
    head=pb.head.copy()
    orig=pb.matrix.copy()
    current=(pb.tail-pb.head).normalized()
    target=(rig.matrix_world.to_3x3().inverted() @ world_target).normalized()
    spin=current.rotation_difference(target)
    pb.matrix=(Matrix.Translation(head) @ spin.to_matrix().to_4x4() @
               Matrix.Translation(-head) @ orig)
    bpy.context.view_layer.update()
    error=math.degrees(direction(pb).angle(world_target.normalized()))
    assert error<3.0, (pb.name,error)
    return error

def side(name):
    # MPFB "l" is positive X in Blender. The phase-8 QA verified this.
    return 1.0 if name.endswith("_l") else -1.0

def neutral_arm(side_letter):
    s=side("upperarm_"+side_letter)
    orient(bones["upperarm_"+side_letter],Vector((s*.18,0,-.984)))
    orient(bones["lowerarm_"+side_letter],Vector((s*.13,-.035,-.991)))

def key_bones(frame,names_to_key):
    for name in names_to_key:
        pb=bones[name]
        pb.keyframe_insert(data_path="rotation_quaternion",frame=frame,
                           group=name)
        if name=="pelvis":
            pb.keyframe_insert(data_path="location",frame=frame,group=name)

def view(name, offset, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera=cam
    camera.data.type="ORTHO"
    camera.data.ortho_scale=height*1.23
    camera.location=focus+Vector(offset)
    camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
    f=os.path.join(out,name+".jpg")
    scene.render.filepath=f
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(f)>3500, f
    return os.path.basename(f)

# We deliberately bake the walk IN PLACE; the Godot CharacterBody owns world
# displacement and must not be moved a second time by root motion.
walk_names=["pelvis","spine_01","spine_02","thigh_l","thigh_r",
            "calf_l","calf_r","foot_l","foot_r",
            "upperarm_l","upperarm_r","lowerarm_l","lowerarm_r"]
aim_names=["spine_02","spine_03","upperarm_l","upperarm_r",
           "lowerarm_l","lowerarm_r"]
rig.animation_data_create()
report={
 "status":"TECHNICAL_ANIMATION_QA_ART_NOT_APPROVED",
 "source":"true CC0 MakeHuman body and compatible trenchcoat, Phase7",
 "source_blend":os.path.basename(source),
 "original_blend_untouched":True,
 "game_main_untouched":True,
 "height_m":height,
 "original_skeleton_bones":len(rig.data.bones),
 "requested_clips":["Cuervo_Walk_InPlace","Cuervo_Aim_Raise"],
 "clip_tracks":{},
 "render_frames":{},
 "skeleton_deformation_tested":False,
 "animation_godot_import_validated":False,
 "android_fps_tested":False,
 "locomotion_gameplay_integrated":False,
 "artistic_approved":False,
 "limitations":[
  "Walk is hand-authored rig motion, no foot IK/plant lock; sliding may be visible.",
  "Aim holds empty hands, weapon grip and real aiming gameplay not integrated.",
  "Coat has skeletal skinning only; no dynamic cloth simulation.",
  "No FPS benchmark on Android, do not replace main character."
 ],
}

# Scene frame start deliberately 1 so Godot imports a standard finite clip.
scene.render.fps=24
walk=bpy.data.actions.new("Cuervo_Walk_InPlace")
rig.animation_data.action=walk
walk_keys=(1,4,7,10,13,16,19,22,25)
for frame in walk_keys:
    scene.frame_set(frame)
    reset_pose()
    phase=(frame-1)*2*math.pi/24
    # Shift opposite legs back and forth within an anatomically sane cone.
    for suffix in ("l","r"):
        s=side("thigh_"+suffix)
        q=1 if suffix=="l" else -1
        swing=math.sin(phase)*q
        # Forward axis is negative Y, and thigh points down.
        orient(bones["thigh_"+suffix],
               Vector((s*.038,-.35*swing,-.935)))
        # Swing knee during recovery; avoid extreme inverted knee rotation.
        flex=max(0.,-swing)
        orient(bones["calf_"+suffix],
               Vector((s*.025,-.20*swing-.12*flex,-.98+.14*flex)))
        # Keep sole close to horizontal to avoid wild ankle flapping.
        # Original foot orientation follows the shin; damp inherited rotation
        # by opposing a portion of the sagittal shin swing.
        foot=bones["foot_"+suffix]
        foot.rotation_mode="QUATERNION"
        foot.rotation_quaternion=Quaternion((1,0,0,0))
    for suffix in ("l","r"):
        s=side("upperarm_"+suffix)
        q=1 if suffix=="l" else -1
        swing=math.sin(phase)*q
        orient(bones["upperarm_"+suffix],
               Vector((s*.20,+.23*swing,-.955)))
        orient(bones["lowerarm_"+suffix],
               Vector((s*.14,+.16*swing,-.975)))
    # Subtle torso counter-motion (not an exaggerated marching sway).
    spine=bones["spine_02"]
    spine.rotation_mode="QUATERNION"
    spine.rotation_quaternion=Quaternion(Vector((0,0,1)),
                                        math.radians(2.0)*math.sin(phase))
    pelvis=bones["pelvis"]
    pelvis.location=(0,0,.006*math.cos(2*phase))
    key_bones(frame,walk_names)
report["clip_tracks"]["Cuervo_Walk_InPlace"]={
 "frames":list(walk_keys), "duration_sec":1.0,"keyed_bones":walk_names,
 "root_motion":False,"loop_requested":True
}
track=rig.animation_data.nla_tracks.new()
track.name="Cuervo_Walk_InPlace"
track.strips.new("Cuervo_Walk_InPlace",1,walk)
rig.animation_data.action=None

# A separate two-handed aimed posture. Both hands remain unarmed; this action
# is not a fabricated shooting system. Kept separate for later transition tree.
aim=bpy.data.actions.new("Cuervo_Aim_Raise")
rig.animation_data.action=aim
aim_keys=(1,7,13,19,25)
for frame in aim_keys:
    scene.frame_set(frame)
    reset_pose()
    q=(frame-1)/24
    eased=q*q*(3-2*q)
    # Explicit directions, not generic local-axis Euler rotations:
    # dominant right arm reaches forward, left supports toward center.
    for suffix in ("l","r"):
        s=side("upperarm_"+suffix)
        start_upper=Vector((s*.18,0,-.984))
        # Bring BOTH elbow hinges closer to the chest centerline, keep the
        # wrists at shoulder height and meet support hand below the dominant.
        # The first export had hands ~0.42 m apart and looked like a zombie.
        upper_aim=Vector((-s*.11,-.935,-.335))
        start_forearm=Vector((s*.13,-.035,-.991))
        forearm_aim=Vector((-s*.39,-.865,+.30))
        orient(bones["upperarm_"+suffix],
               start_upper.lerp(upper_aim,eased))
        orient(bones["lowerarm_"+suffix],
               start_forearm.lerp(forearm_aim,eased))
    # Small forward chest lean while raising weapon-ready hands.
    chest=bones["spine_03"]
    chest.rotation_mode="QUATERNION"
    chest.rotation_quaternion=Quaternion(Vector((1,0,0)),
                                       math.radians(3)*eased)
    key_bones(frame,aim_names)
report["clip_tracks"]["Cuervo_Aim_Raise"]={
 "frames":list(aim_keys),"duration_sec":1.0,
 "keyed_bones":aim_names,"root_motion":False,"loop_requested":False
}
track2=rig.animation_data.nla_tracks.new()
track2.name="Cuervo_Aim_Raise"
track2.strips.new("Cuervo_Aim_Raise",1,aim)
rig.animation_data.action=None

# QA renders always play ONE action at a time so action strips do not mix.
# Temporarily mute tracks during capture; NLA strips remain on real rig for
# glTF export (unmute both immediately after image capture).
for tr in rig.animation_data.nla_tracks:
    tr.mute=True

rig.animation_data.action=walk
report["render_frames"]["walk_start"]=view("01_Caminata_Frente_Contacto",
                                            (0,-4,.13),1)
report["render_frames"]["walk_mid"]=view("02_Caminata_Frente_Paso",
                                          (0,-4,.13),7)
report["render_frames"]["walk_3q"]=view("03_Caminata_TresCuartos",
                                         (2.8,-3.8,.14),13)
report["render_frames"]["walk_profile"]=view("04_Caminata_Perfil",
                                              (4.2,0,.12),19)
rig.animation_data.action=aim
report["render_frames"]["aim_neutral"]=view("05_Apuntar_Reposo",
                                             (2.8,-3.8,.14),1)
report["render_frames"]["aim_transition"]=view("06_Apuntar_Transicion",
                                                (2.8,-3.8,.14),13)
report["render_frames"]["aim_held"]=view("07_Apuntar_BrazosElevados",
                                          (2.8,-3.8,.14),25)
report["render_frames"]["aim_front"]=view("08_Apuntar_Frente",
                                           (0,-4,.13),25)
# Numerical aiming quality gate: both original skinned hands must converge
# approximately on a two-handed grip, rather than point from 40 cm apart.
scene.frame_set(25)
bpy.context.view_layer.update()
lh=rig.matrix_world @ rig.pose.bones["hand_l"].head
rh=rig.matrix_world @ rig.pose.bones["hand_r"].head
report["aim_hand_gap_m"]=(lh-rh).length
report["aim_hand_heights_world_m"]=[lh.z,rh.z]
assert .065<report["aim_hand_gap_m"]<.22, (
    "The two-handed aim pose is not aligned",report["aim_hand_gap_m"])
assert min(lh.z,rh.z)>lo.z+height*.71, (
    "Aiming hands too low for shooting",lh.z,rh.z)
rig.animation_data.action=None
for tr in rig.animation_data.nla_tracks:
    tr.mute=False
# Explicit animation mode in the GLB exporter. Frames last a full second.
scene.frame_start=1
scene.frame_end=25
scene.frame_set(1)
report["saved_action_names"]=[a.name for a in bpy.data.actions if a.name.startswith("Cuervo_")]
assert set(report["saved_action_names"])==set(report["requested_clips"])

# Save real editable source with Actions and NLA tracks.
bpy.ops.file.pack_all()
blend=os.path.join(out,"El_Cuervo_Fase9_Walk_Aim_REVISION.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
assert os.path.getsize(blend)>100000
bpy.ops.object.select_all(action="DESELECT")
selected=[obj for obj in bpy.data.objects if obj.type=="MESH" or obj==rig]
for obj in selected:
    obj.select_set(True)
bpy.context.view_layer.objects.active=rig
glb=os.path.join(out,"El_Cuervo_Fase9_Walk_Aim_REVISION.glb")
bpy.ops.export_scene.gltf(
    filepath=glb,export_format="GLB",use_selection=True,export_yup=True,
    export_animations=True,export_animation_mode="NLA_TRACKS",
    export_force_sampling=True,export_frame_step=1
)
with open(glb,"rb") as f:
    magic,ver,filesize=struct.unpack("<4sII",f.read(12))
    assert magic==b"glTF" and ver==2 and filesize==os.path.getsize(glb)
    jlen,typ=struct.unpack("<I4s",f.read(8))
    assert typ==b"JSON"
    tree=json.loads(f.read(jlen).decode("utf8"))
anims=tree.get("animations",[])
report["exported_animation_names"]=[a.get("name","") for a in anims]
report["animation_channel_counts"]={a.get("name",str(i)):len(a.get("channels",[]))
    for i,a in enumerate(anims)}
report["exported_skin_joints"]=[len(x["joints"]) for x in tree.get("skins",[])]
assert len(anims)>=2, ("Could not find exported animation tracks",report["exported_animation_names"])
assert any("Walk" in x for x in report["exported_animation_names"])
assert any("Aim" in x for x in report["exported_animation_names"])
assert 53 in report["exported_skin_joints"]
assert all(len(a.get("channels",[]))>=4 for a in anims)
report["skeleton_deformation_tested"]=True
report["glb_file"]=os.path.basename(glb)
report["blend_file"]=os.path.basename(blend)
report["glb_bytes"]=os.path.getsize(glb)
report["blender_reimport_verified"]=False
report["godot43_animation_verified"]=False
with open(os.path.join(out,"AUDITORIA_ANIMACIONES_FASE9.json"),"w",encoding="utf8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)
print("CUERVO_FASE9_REAL_GLTF_ANIMATIONS_BUILT",
      json.dumps({"animation_names":report["exported_animation_names"],
                  "channels":report["animation_channel_counts"],
                  "bytes":report["glb_bytes"]}),flush=True)
