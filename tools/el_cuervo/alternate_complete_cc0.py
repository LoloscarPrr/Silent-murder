"""Silent Killer / El Cuervo: isolated alternative using COMPLETE compatible
CC0 MakeHuman outputs from kblood/CharacterCreator, pinned upstream.
Purpose: compare actual human eyes/hair/garments against broken manual fittings.
No gameplay replacement, no edits to main, no claimed artistic approval.
"""
import bpy
import os
import sys
import json
import struct
from mathutils import Vector

args = sys.argv[sys.argv.index("--")+1:]
def get(key):
    return os.path.abspath(args[args.index(key)+1])
studio, assets, out = get("--studio"), get("--assets"), get("--out")
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=studio)
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    if obj.type in {"MESH", "ARMATURE", "EMPTY"}:
        bpy.data.objects.remove(obj, do_unlink=True)
assert scene.camera is not None

entries = [
    ("body", "base_body.glb"),
    ("hair", "hair_short04.glb"),
    ("shirt", "clothing_shirt.glb"),
    ("jeans", "clothing_jeans.glb"),
    ("boots", "clothing_boots.glb"),
    ("jacket", "clothing_trenchcoat.glb"),
]
stats = {
    "status": "PREVIEW_NOT_APPROVED",
    "source": "kblood/CharacterCreator output CC0",
    "source_repo": "https://github.com/kblood/CharacterCreator",
    "source_revision": "852e48f316b90a0937234886630e4fb4cdfd1f78",
    "body_and_wardrobe_compatible_source": True,
    "main_game_modified": False,
    "animation_review_approved": False,
    "android_fps_tested": False,
    "artistic_review_approved": False,
    "parts": [],
}
parts = {}
for kind, filename in entries:
    before = set(bpy.data.objects)
    path = os.path.join(assets, filename)
    assert os.path.getsize(path) > 100000, path
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    # glTF Blender importer creates an Icosphere auxiliary that is not a
    # glTF mesh node (verified in the original source project). Exclude it.
    to_remove = [o for o in new if o.type == "MESH" and o.name.startswith("Icosphere")]
    new = [o for o in new if o not in to_remove]
    for helper in to_remove:
        bpy.data.objects.remove(helper, do_unlink=True)
    meshes = [o for o in new if o.type == "MESH"]
    armatures = [o for o in new if o.type == "ARMATURE"]
    assert meshes, (kind, filename, [x.name for x in new])
    parts[kind] = {"all": new, "meshes": meshes, "arms": armatures}
    stats["parts"].append({
        "kind": kind, "source": filename,
        "objects": [o.name for o in new],
        "meshes": len(meshes), "armatures": len(armatures),
        "triangles": sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
        "bones": [len(a.data.bones) for a in armatures],
    })
    print("REAL_CC0_PART", kind, stats["parts"][-1], flush=True)

# Preserve the native PBR textures, including iris, brows and skin.
# Only tint the CLOTHING colors to charcoal and black. These input
# garments share the SAME upstream MPFB morph/rest-body architecture.
tints = {
    "shirt": (.055, .056, .062),
    "jeans": (.046, .047, .056),
    "boots": (.042, .041, .042),
    "jacket": (.055, .054, .061),
    "hair": (.28, .23, .20),
}
for kind, tint in tints.items():
    for obj in parts[kind]["meshes"]:
        for j, source_mat in enumerate(list(obj.data.materials)):
            if source_mat is None:
                continue
            mat = source_mat.copy()
            # Mesh-local material: do not recolor body, eyes or face.
            obj.data.materials[j] = mat
            if not mat.use_nodes:
                mat.diffuse_color = (*tint, 1)
                continue
            shader = mat.node_tree.nodes.get("Principled BSDF")
            if not shader:
                continue
            base = shader.inputs["Base Color"]
            links = mat.node_tree.links
            original = next((link.from_socket for link in links if link.to_socket == base), None)
            if original:
                multiply = mat.node_tree.nodes.new("ShaderNodeMixRGB")
                multiply.blend_type = "MULTIPLY"
                multiply.inputs[0].default_value = 1.0
                multiply.inputs[2].default_value = (*tint, 1)
                links.new(original, multiply.inputs[1])
                links.new(multiply.outputs["Color"], base)
            else:
                base.default_value = (*tint, 1)
            shader.inputs["Roughness"].default_value = .76

# Each glTF morph arrived with a FULL weight of 1.0 in Blender, even though
# upstream engine normally initializes each weight to neutral 0.0. Applying
# ALL of these shape keys simultaneously enormously inflated jacket and body.
# Reset every non-Basis morph to 0 without removing any key from export.
stats["morph_weights_nonzero_before"] = []
stats["morph_count_reset"] = 0
for part in parts.values():
    for obj in part["meshes"]:
        keys = obj.data.shape_keys
        if keys is None:
            continue
        for block in keys.key_blocks:
            if block == keys.key_blocks[0]:
                continue
            if abs(block.value) > .00001:
                stats["morph_weights_nonzero_before"].append({
                    "mesh": obj.name, "key": block.name, "weight": block.value
                })
            block.value = 0.0
            stats["morph_count_reset"] += 1
stats["all_morph_targets_neutralized"] = True
assert stats["morph_count_reset"] >= 50, "Expected source body/facial morphs"
print("CC0_NEUTRALIZED_MORPHS", stats["morph_count_reset"],
      "nonzero", len(stats["morph_weights_nonzero_before"]), flush=True)

all_meshes = [o for p in parts.values() for o in p["meshes"]]
all_rigs = [o for p in parts.values() for o in p["arms"]]
main_rig = max(all_rigs, key=lambda a: len(a.data.bones)) if all_rigs else None
assert main_rig and len(main_rig.data.bones) >= 30, "Rigged base required"
stats["main_skeleton_bones"] = len(main_rig.data.bones)
stats["all_armatures_found"] = len(all_rigs)

# These imported garments may contain their own partial glTF skin rigs.
# Reuse the main body rig only where source rig names and bind positions
# match. Never silently force unrelated bones onto another armature.
# All six source GLBs were authored for the same 53-bone MPFB rig.
# Blender appends .001/.002 numeric suffixes to duplicate imported joint names.
# Match canonical original bone names AND rest positions before rig consolidation.
import re
def canonical(name):
    return re.sub(r"\.\d{3}$", "", name)
main_bone_map = {canonical(bone.name): bone for bone in main_rig.data.bones}
merged_rigs = []
rig_diagnostics = []
for rig in list(all_rigs):
    if rig == main_rig:
        continue
    match = {canonical(bone.name): bone for bone in rig.data.bones}
    shared = set(main_bone_map) & set(match)
    diag = {"armature": rig.name, "source_bone_samples": list(match)[:8],
            "bone_overlap": len(shared), "total_bones":len(match)}
    if len(shared) < max(4, int(len(match)*.90)):
        diag["merge_status"] = "rejected_bone_names_not_equivalent"
        rig_diagnostics.append(diag)
        continue
    differences = []
    for name in shared:
        a = rig.matrix_world @ match[name].head_local
        b = main_rig.matrix_world @ main_bone_map[name].head_local
        differences.append((a-b).length)
    diag["max_rest_offset_m"] = max(differences)
    diag["mean_rest_offset_m"] = sum(differences)/len(differences)
    if max(differences) > .025:
        diag["merge_status"] = "rejected_rest_pose_mismatch"
        rig_diagnostics.append(diag)
        continue
    affected = [o for o in all_meshes if any(
        mod.type == "ARMATURE" and mod.object == rig for mod in o.modifiers)]
    for mesh in affected:
        # Re-map original names before replacing the skin modifier.
        for group in mesh.vertex_groups:
            name = canonical(group.name)
            if name in main_bone_map and group.name != main_bone_map[name].name:
                group.name = main_bone_map[name].name
        world = mesh.matrix_world.copy()
        if mesh.parent == rig:
            mesh.parent = None
            mesh.matrix_world = world
        for modifier in mesh.modifiers:
            if modifier.type == "ARMATURE" and modifier.object == rig:
                modifier.object = main_rig
    if not any(any(mod.type=="ARMATURE" and mod.object == rig
                   for mod in m.modifiers) for m in all_meshes) and not any(
                    m.parent==rig for m in all_meshes):
        old_name = rig.name
        bpy.data.objects.remove(rig, do_unlink=True)
        merged_rigs.append(old_name)
        diag["merge_status"] = "merged_to_primary_53_bone_rig"
    else:
        diag["merge_status"] = "retargeted_but_existing_dependency"
    rig_diagnostics.append(diag)
stats["merged_armatures"] = merged_rigs
stats["rig_compatibility_report"] = rig_diagnostics
stats["rig_count_after"] = len([o for o in bpy.data.objects if o.type=="ARMATURE"])
print("CC0_RIG_COMPATIBILITY", json.dumps(rig_diagnostics), flush=True)

# This is a fixed cinematic protagonist, not a customizable MakeHuman avatar.
# Bake current neutral body by discarding hundreds of unrelated shape keys,
# preserving only eye-blink and eye-gaze keys for future facial animation.
dynamic_eye_keys = {"blink_left","blink_right","look_left","look_right",
                    "look_up","look_down"}
stats["morphs_removed_for_android"] = 0
stats["morphs_kept_for_eyes"] = 0
for obj in all_meshes:
    if not obj.data.shape_keys:
        continue
    retain = dynamic_eye_keys if obj.name in {"Body","Eyes","Eyelashes","Eyebrows"} else set()
    for key in reversed(list(obj.data.shape_keys.key_blocks)[1:]):
        if key.name in retain:
            stats["morphs_kept_for_eyes"] += 1
        else:
            obj.shape_key_remove(key)
            stats["morphs_removed_for_android"] += 1
stats["lod_optimization_policy"] = "fixed avatar, preserve blink/look only"
print("CC0_REMOVED_UNUSED_MORPHS", stats["morphs_removed_for_android"], flush=True)

def bounding(objects):
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return lo, hi
lo, hi = bounding(parts["body"]["meshes"])
height = hi.z-lo.z
assert .9 < height < 2.5, "Unexpected model coordinate system " + str(height)
stats["source_body_height_m"] = height
# Correct the protagonist height to the existing 1.84m El Cuervo blueprint.
# Uniformly scale each top-level imported object so arms, skin, clothes, hair
# and original skinning rest positions remain in correct proportions.
from mathutils import Matrix
scale = 1.84 / height
for ob in list(bpy.data.objects):
    if ob.type not in {"ARMATURE", "MESH"} or ob.parent is not None:
        continue
    ob.matrix_world = Matrix.Scale(scale, 4) @ ob.matrix_world
bpy.context.view_layer.update()
lo, hi = bounding(parts["body"]["meshes"])
height = hi.z-lo.z
assert abs(height-1.84) < .02, "Uniform human scaling unsuccessful"
stats["body_height_m"] = height
stats["uniform_scale_factor"] = scale
cx = (lo.x+hi.x)*.5
cy = (lo.y+hi.y)*.5

# Real studio setup inherited from existing Silent Killer Blender stage.
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 18
scene.cycles.use_denoising = True
scene.render.resolution_x = 780
scene.render.resolution_y = 1040
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
target = Vector((cx, cy, lo.z+height*.51))
cam = scene.camera
def render(name, offset, focal=target, scale=None):
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = (height*1.24 if scale is None else scale)
    cam.location = focal + Vector(offset)
    cam.rotation_euler = (focal-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>6000
render("01_Fullbody_Frontal", (0,-4,.15))
render("02_Fullbody_TresCuartos", (2.8,-3.7,.15))
render("03_Fullbody_Espalda", (0,4,.1))
render("04_Cabello_Cara", (1.0,-4,.08),
       Vector((cx,cy,lo.z+height*.82)),height*.53)
render("05_Punos_Manga", (1.5,-3.8,.1),
       Vector((cx+.40,cy,lo.z+height*.56)),height*.44)

bpy.ops.file.pack_all()
blend = os.path.join(out, "El_Cuervo_Candidato_Profesional_CC0.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.object.select_all(action="DESELECT")
export_items = [o for o in bpy.data.objects if o.type == "ARMATURE" or (o.type == "MESH" and o in all_meshes)]
for item in export_items:
    item.select_set(True)
bpy.context.view_layer.objects.active = main_rig
glb = os.path.join(out, "El_Cuervo_Candidato_Profesional_CC0.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB",
                          use_selection=True, export_yup=True,
                          export_materials="EXPORT")
with open(glb,"rb") as f:
    magic, version, length = struct.unpack("<4sII", f.read(12))
    assert magic==b"glTF" and version==2 and length==os.path.getsize(glb)
    n, kind=struct.unpack("<I4s", f.read(8))
    assert kind==b"JSON"
    g=json.loads(f.read(n).decode("utf8"))
stats["glb_mesh_nodes"] = [n.get("name") for n in g["nodes"] if "mesh" in n]
stats["blender_file"] = os.path.basename(blend)
stats["glb_file"] = os.path.basename(glb)
stats["glb_size_bytes"] = os.path.getsize(glb)
stats["total_triangles"] = sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in all_meshes)
stats["blender_reimport_verified"] = False
stats["godot43_import_verified"] = False
with open(os.path.join(out,"AUDITORIA_ALTERNATIVA.json"),"w",encoding="utf8") as f:
    json.dump(stats,f,indent=2,ensure_ascii=False)
print("CUERVO_ALTERNATIVE_PRODUCED", json.dumps(stats,ensure_ascii=False),flush=True)
