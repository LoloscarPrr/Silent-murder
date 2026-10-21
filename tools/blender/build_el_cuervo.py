#!/usr/bin/env python3
"""Silent Killer asset pipeline: create a Blender-editable first-pass EL CUERVO.

Usage:
  blender --background --python tools/blender/build_el_cuervo.py -- --output out/blender

Outputs: El_Cuervo_v0_1.blend, El_Cuervo_v0_1.glb
These are real 3D meshes and an armature, NOT a 2D concept or final art.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

def args_after_separator():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="out/blender")
    return parser.parse_args(args)

OUT = os.path.abspath(args_after_separator().output)
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for data in bpy.data.materials:
    bpy.data.materials.remove(data)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

def material(name, color, metallic=0.0, roughness=0.78):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Metallic"].default_value = metallic
        shader.inputs["Roughness"].default_value = roughness
    return mat

suit = material("Tailored graphite suit", (0.066, 0.077, 0.087))
vest = material("Low profile ceramic armour", (0.117, 0.145, 0.154))
sleeve = material("Matte navy fabric", (0.092, 0.111, 0.129))
glove = material("Black tactical leather", (0.023, 0.029, 0.035))
boots = material("Dark composite boots", (0.032, 0.040, 0.045))
skin = material("Face neutral", (0.46, 0.315, 0.235))
hair = material("Short black hair", (0.020, 0.022, 0.025))
metal = material("Brushed steel accent", (0.34, 0.38, 0.40), 0.5)

# Blender uses Z up and the actor faces -Y. The glTF exporter transforms
# axes automatically for Godot's Y-up system.
def bevel_cube(name, location, size, mat, bone, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = ob.modifiers.new("Soft garment corners", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        if hasattr(mod, "affect"):
            mod.affect = "EDGES"
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.data.materials.append(mat)
    parts.append((ob, bone))
    return ob

def ellipsoid(name, location, radii, mat, bone, segments=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(mat)
    parts.append((ob, bone))
    return ob

parts = []
# Z coordinates: boots 0.10, knees 0.56, waist 1.0, shoulders 1.48, head 1.76
bevel_cube("Pelvis / suit trousers", (0, 0, 0.99), (.38, .245, .24), suit, "Hips", .07)
bevel_cube("Chest / tailored suit", (0, .015, 1.31), (.53, .265, .53), suit, "Chest", .10)
bevel_cube("Lightweight armour plate", (0, -.151, 1.34), (.40, .065, .40), vest, "Chest", .04)
bevel_cube("Collar", (0, 0, 1.59), (.30, .25, .105), sleeve, "Chest", .035)
bevel_cube("Diagonal tactical strap", (.095, -.198, 1.35), (.075, .027, .41), glove, "Chest", .015)
bevel_cube("Belt", (0, -.008, 1.045), (.44, .29, .085), glove, "Hips", .024)
bevel_cube("Belt clasp", (0, -.17, 1.05), (.11, .022, .057), metal, "Hips", .014)

ellipsoid("Head / face", (0, -.022, 1.738), (.149, .128, .182), skin, "Head")
ellipsoid("Short cropped hair", (0, .015, 1.842), (.155, .137, .095), hair, "Head")
bevel_cube("Neck undersuit", (0, .012, 1.616), (.143, .147, .10), sleeve, "Neck", .035)
# No visible eyes or facial texture in this first pass: face art comes later.

for side, x in (("L", .185), ("R", -.185)):
    sign = 1 if side == "L" else -1
    thigh = "Thigh." + side
    shin = "Shin." + side
    foot = "Foot." + side
    arm = "UpperArm." + side
    forearm = "Forearm." + side
    hand = "Hand." + side
    ellipsoid("Tailored thigh " + side, (x, 0, .79), (.132, .125, .315), suit, thigh)
    ellipsoid("Trousers shin " + side, (x, .015, .365), (.114, .106, .260), sleeve, shin)
    bevel_cube("Boot " + side, (x, -.053, .135), (.235, .35, .22), boots, foot, .05)
    ellipsoid("Sleeve upper " + side, (sign*.350, .006, 1.367), (.118, .114, .259), suit, arm)
    ellipsoid("Sleeve forearm " + side, (sign*.407, -.013, 1.095), (.096, .094, .205), sleeve, forearm)
    ellipsoid("Glove " + side, (sign*.414, -.05, .916), (.097, .087, .110), glove, hand)
    bevel_cube("Elbow insert " + side, (sign*.402, -.106, 1.194), (.143, .043, .115), vest, forearm, .022)
    # Shoulder armour and subtle holster, without futuristic oversized gear.
    ellipsoid("Shoulder armour " + side, (sign*.306, -.048, 1.485), (.156, .127, .087), vest, arm)
bevel_cube("Hidden holster / right hip", (-.255, -.080, .93), (.09, .20, .25), glove, "Hips", .025)

# Stand-up armature with per-part deform bone weights.
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
rig = bpy.context.object
rig.name = "El_Cuervo_Rig"
arm = rig.data
arm.name = "El_Cuervo_Skeleton"
for bone in list(arm.edit_bones):
    arm.edit_bones.remove(bone)

def bone(name, head, tail, parent=None):
    ob = arm.edit_bones.new(name)
    ob.head = head
    ob.tail = tail
    if parent:
        ob.parent = arm.edit_bones[parent]
        ob.use_connect = False
    return ob

bone("Hips", (0,0,.97), (0,0,1.09))
bone("Spine", (0,0,1.09), (0,0,1.34), "Hips")
bone("Chest", (0,0,1.34), (0,0,1.55), "Spine")
bone("Neck", (0,0,1.55), (0,0,1.64), "Chest")
bone("Head", (0,0,1.64), (0,0,1.88), "Neck")
for side, sign in (("L",1),("R",-1)):
    bone("UpperArm."+side, (sign*.278,0,1.485), (sign*.399,0,1.245), "Chest")
    bone("Forearm."+side, (sign*.399,0,1.245), (sign*.409,0,1.032), "UpperArm."+side)
    bone("Hand."+side, (sign*.409,0,1.032), (sign*.412,0,.88), "Forearm."+side)
    bone("Thigh."+side, (sign*.186,0,.995), (sign*.186,0,.59), "Hips")
    bone("Shin."+side, (sign*.186,0,.59), (sign*.186,0,.19), "Thigh."+side)
    bone("Foot."+side, (sign*.186,0,.19), (sign*.186,-.135,.09), "Shin."+side)

bpy.ops.object.mode_set(mode="OBJECT")
rig.show_in_front = True

for part, name in parts:
    group = part.vertex_groups.new(name=name)
    group.add(list(range(len(part.data.vertices))), 1.0, "REPLACE")
    mod = part.modifiers.new("Skin from armature", "ARMATURE")
    mod.object = rig
    part.parent = rig
    part.matrix_parent_inverse = rig.matrix_world.inverted()

# Export only the character and rig; save an editable Blender file as well.
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for part, _ in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = rig
blend_file = os.path.join(OUT, "El_Cuervo_v0_1.blend")
glb_file = os.path.join(OUT, "El_Cuervo_v0_1.glb")
bpy.ops.wm.save_as_mainfile(filepath=blend_file, check_existing=False)
bpy.ops.export_scene.gltf(
    filepath=glb_file,
    export_format="GLB",
    use_selection=True,
    export_animations=False,
    export_yup=True
)
print("SILENT_KILLER_BLENDER_EXPORT_OK")
print("BLEND", blend_file)
print("GLB", glb_file)
print("MESH_PARTS", len(parts))
print("BONES", len(arm.bones))
