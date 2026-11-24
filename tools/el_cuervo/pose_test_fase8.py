"""Silent Killer / El Cuervo — Fase 8 genuine rig deformation QA.

Opens the actual Phase-7 BLEND file; makes a measurable, repeatable movement test:
front + profile A-pose, upper arms lowered, elbows bent. Renders exact evaluated
CC0 skinned mesh in Blender (no AI image). Restores source pose after every test.
No changes to playable game, source Phase7 asset or branch main.
"""
import bpy
import json
import math
import os
import sys
import struct
from mathutils import Vector, Matrix

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
def argument(key):
    assert key in argv, key
    return os.path.abspath(argv[argv.index(key)+1])
src=argument("--blend")
out=argument("--out")
os.makedirs(out,exist_ok=True)
assert os.path.getsize(src)>200000
bpy.ops.wm.open_mainfile(filepath=src)
scene=bpy.context.scene
rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
assert len(rigs)==1
rig=rigs[0]
assert len(rig.data.bones)==53
body=bpy.data.objects.get("Body")
coat=bpy.data.objects.get("Cloth_trenchcoat")
hands=[rig.pose.bones.get("hand_l"),rig.pose.bones.get("hand_r")]
arms=[rig.pose.bones.get("upperarm_l"),rig.pose.bones.get("upperarm_r")]
forearms=[rig.pose.bones.get("lowerarm_l"),rig.pose.bones.get("lowerarm_r")]
assert body and coat and all(arms) and all(forearms) and all(hands)
assert all(any(m.type=="ARMATURE" and m.object==rig for m in o.modifiers) for o in [body,coat])
assert scene.camera

def bounds(obj):
    v=[obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return Vector(tuple(min(a[i] for a in v) for i in range(3))),Vector(tuple(max(a[i] for a in v) for i in range(3)))
lo,hi=bounds(body)
height=hi.z-lo.z
assert 1.8<height<1.9
cx=(hi.x+lo.x)/2
cy=(hi.y+lo.y)/2
focus=Vector((cx,cy,lo.z+height*.51))
camera=scene.camera
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=14
scene.cycles.use_denoising=True
scene.render.resolution_x=720
scene.render.resolution_y=940
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False

report={
 "status":"KINEMATIC_QA_RENDER_PENDING_ARTISTIC_REVIEW",
 "source_real_blend":os.path.basename(src),
 "original_phase7_modified":False,
 "game_main_modified":False,
 "height_m":height,
 "rig_count":len(rigs),
 "rig_bones":len(rig.data.bones),
 "coat_original_polygons":len(coat.data.polygons),
 "pose_angles_deg":{},
 "pose_bone_names":{},
 "body_deformation_measured":False,
 "coat_deformation_measured":False,
 "artistic_approved":False,
 "animations_integrated":False,
 "android_fps_tested":False,
}

def render(name,offset,aim=focus,scale=None):
    camera.data.type="ORTHO"
    camera.data.ortho_scale=height*1.24 if scale is None else scale
    camera.location=aim+Vector(offset)
    camera.rotation_euler=(aim-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>5000
    # True Blender render reduced for the user's low-bandwidth Android chat.
    # No second render; load that exact PNG, resize, write tiny JPEG locally.
    rendered=bpy.data.images.load(scene.render.filepath,check_existing=False)
    rendered.scale(350,456)
    scene.render.image_settings.file_format="JPEG"
    scene.render.image_settings.quality=55
    rendered.save_render(os.path.join(out,name+"_CHAT.jpg"),scene=scene)
    scene.render.image_settings.file_format="PNG"
    bpy.data.images.remove(rendered)
    assert os.path.getsize(os.path.join(out,name+"_CHAT.jpg"))>3000
    return name+".png"

def sampled_world_vertices(obj,skip=14):
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ mesh.vertices[i].co.copy() for i in range(0,len(mesh.vertices),skip)]
    finally:
        evaluated.to_mesh_clear()

def displacement_stats(before,after):
    assert len(before)==len(after)
    distances=[(v-w).length for v,w in zip(before,after)]
    distances.sort()
    return {"sampled":len(distances),"median_m":distances[len(distances)//2],
            "p95_m":distances[int((len(distances)-1)*.95)],
            "max_m":distances[-1]}

def world_direction(bone):
    return (rig.matrix_world.to_3x3() @ (bone.tail-bone.head)).normalized()

def set_world_bone_direction(pb,target_world):
    """Set Blender pose matrix to rotate an existing bone about its HEAD.
    Explicitly convert world target into armature coordinates; no assumption
    about bone roll or whether the skeleton faces -Y or +Y.
    """
    original=pb.matrix.copy()
    head=pb.head.copy()
    current=(pb.tail-pb.head).normalized()
    target=(rig.matrix_world.to_3x3().inverted() @ target_world).normalized()
    rotation=current.rotation_difference(target)
    transformed=(Matrix.Translation(head)
                 @ rotation.to_matrix().to_4x4()
                 @ Matrix.Translation(-head) @ original)
    pb.matrix=transformed
    bpy.context.view_layer.update()
    reached=world_direction(pb)
    delta=math.degrees(reached.angle(target_world.normalized()))
    assert delta<4, ("pose direction was not reached",pb.name,delta)
    return delta

def original_rest():
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()

original_rest()
base_body=sampled_world_vertices(body)
base_coat=sampled_world_vertices(coat)
report["renders"]=[
    render("01_Frente_BrazosAbiertos",(0,-4.1,.12)),
    render("02_Perfil_BrazosAbiertos",(4.2,0,.12)),
]

# The default source has upper arms at an A-pose. Rotate the REAL upper-arm
# bones, allowing the original full-weight skinning to drive cloth and hands.
for arm in arms:
    # IMPORTANT: original MPFB armature's LEFT projects to positive Blender X.
    # Derive side from actual bone axis; suffix "_l" is not world -X.
    side=1 if world_direction(arm).x>0 else -1
    target_world=Vector((side*.18,0,-.984))
    report["pose_angles_deg"][arm.name]=math.degrees(world_direction(arm).angle(target_world))
    report["pose_bone_names"][arm.name]={"original_world":list(world_direction(arm)),
                                        "target_world":list(target_world)}
    report["pose_bone_names"][arm.name]["angular_error_deg"] = set_world_bone_direction(arm,target_world)

# Lower forearms also point forward in the original A-pose.
# Bend them into the anatomical rest direction so hands hang alongside hips.
for forearm in forearms:
    side=1 if forearm.name.endswith("_l") else -1
    target_world=Vector((side*.13,-.035,-.991))
    report["pose_bone_names"][forearm.name+"_lowered"]={
        "target_world":list(target_world),
        "angular_error_deg":set_world_bone_direction(forearm,target_world)
    }
down_pose_forearms={f.name:f.matrix.copy() for f in forearms}
bpy.context.view_layer.update()
down_body=sampled_world_vertices(body)
down_coat=sampled_world_vertices(coat)
report["body_deformation"]=displacement_stats(base_body,down_body)
report["coat_deformation"]=displacement_stats(base_coat,down_coat)
assert report["body_deformation"]["max_m"]>.045, "Arms did not deform body skin"
assert report["coat_deformation"]["max_m"]>.025, "Garment did not respond to pose"
report["body_deformation_measured"]=True
report["coat_deformation_measured"]=True
report["renders"] += [
    render("03_Frente_BrazosAbajo",(0,-4.1,.12)),
    render("04_TresCuartos_BrazosAbajo",(2.9,-3.7,.12)),
    render("05_Perfil_BrazosAbajo",(4.2,0,.12)),
]
# Elbows bent deliberately to expose possible cloth crossings at cuffs and
# torso. Rotate each lowerarm only after upper arms reached the low pose.
for forearm in forearms:
    side=1 if forearm.name.endswith("_l") else -1
    current=world_direction(forearm)
    new_target=Vector((side*.17,-.63,-.76))
    report["pose_bone_names"][forearm.name]={
        "original_world_after_upperarm":list(current),
        "target_world":list(new_target),
        "angular_error_deg":set_world_bone_direction(forearm,new_target)
    }
report["renders"] += [
    render("06_Frente_CodosFlexionados",(0,-4.1,.12)),
    render("07_TresCuartos_CodosFlexionados",(2.9,-3.7,.12)),
]
report["bent_coat_deformation"]=displacement_stats(base_coat,sampled_world_vertices(coat))
# Preserve an actual evaluated GLB in arms-down inspection pose, but keep
# production gameplay candidate unchanged. Pose not approved until visual QA.
for pb in forearms:
    pb.matrix=down_pose_forearms[pb.name]
bpy.context.view_layer.update()
report["restored_anatomical_forearms_for_down_glb"]=True
bpy.ops.object.select_all(action="DESELECT")
objects=[obj for obj in bpy.data.objects if obj.type=="MESH" or obj==rig]
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
outglb=os.path.join(out,"El_Cuervo_Fase8_Inspeccion_BrazosAbajo.glb")
bpy.ops.export_scene.gltf(filepath=outglb,export_format="GLB",
                          use_selection=True,export_yup=True)
with open(outglb,"rb") as f:
    magic,version,size=struct.unpack("<4sII",f.read(12))
    assert magic==b"glTF" and version==2 and size==os.path.getsize(outglb)
report["inspection_glb"]=os.path.basename(outglb)
report["inspection_glb_bytes"]=os.path.getsize(outglb)
original_rest()
report["source_pose_restored"]=True
report["known_limits"]=[
    "Only static bone poses: no complete locomotion, aiming or action animations tested",
    "Cloth can intersect when animated; inspect PNG frontal/profile/bent elbow views",
    "No simulation of cloth dynamics or Android device performance",
    "This is an isolated QA artifact and does not replace the playable character",
]
with open(os.path.join(out,"AUDITORIA_MOVIMIENTO_FASE8.json"),"w",encoding="utf8") as f:
    json.dump(report,f,indent=2,ensure_ascii=False)
print("EL_CUERVO_RIG_QA_COMPLETE",json.dumps(report,ensure_ascii=False),flush=True)
