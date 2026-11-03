"""Silent Killer / El Cuervo — phase 6: controlled refinement of the unbroken
Margaret Toigo CC0 outfit. Never imports or edits the rejected phase 5 suit.
Blender 4.3, invoked in GitHub Actions.

This is a review candidate, not an artist-approved gameplay replacement.
The source human mesh, 163-bone armature, CC0 clothing UVs and real boot meshes
remain editable. Only a new isolated production folder is written.
"""
import bpy
import bmesh
import json
import math
import os
import struct
import sys
from mathutils import Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def argument(name):
    assert name in argv, "Missing " + name
    return os.path.abspath(argv[argv.index(name) + 1])

src = argument("--blend")
out = argument("--out")
assert os.path.isfile(src)
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
rigs = [o for o in scene.objects if o.type == "ARMATURE"]
assert len(rigs) == 1, "Exactly one original rig expected"
rig = rigs[0]
assert len(rig.data.bones) == 163, "Original skeleton may not change"
base = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("base_male_body")]
skin = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("VisibleSkin_")]
suits = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("CC0_toigo_male_suit_3")]
boots = [o for o in scene.objects if o.type == "MESH" and o.name.startswith("Cuervo_Botin_CC0")]
assert base and skin and len(suits) == 1 and boots, "Phase 4 source assets missing"
suit = suits[0]
bpy.context.view_layer.update()

def bounds(objects):
    points = [o.matrix_world @ Vector(p) for o in objects for p in o.bound_box]
    return Vector(tuple(min(p[i] for p in points) for i in range(3))), \
           Vector(tuple(max(p[i] for p in points) for i in range(3)))
low, high = bounds(base)
H = high.z - low.z
assert abs(H - 1.84) < 0.025, H
cx = (low.x + high.x) * .5
cy = (low.y + high.y) * .5

def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)

def smoothstep(a, b, x):
    t = max(0., min(1., (x - a) / max(.00001, (b - a))))
    return t * t * (3 - 2 * t)

def principled(name, color, roughness, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

data = {
    "base": "phase4 verified authentic CC0 suit; not the rejected phase5 garment",
    "source_blend": os.path.basename(src),
    "source_suit_name": suit.name,
    "source_license": "Margaret Toigo / MakeHuman Community suits01 CC0",
    "original_body_modified": False,
    "original_height_m": H,
    "skeleton_bones": len(rig.data.bones),
    "phase5_rejected_assets_used": False,
    "game_main_modified": False,
    "artistic_review_approved": False,
    "animation_review_approved": False,
    "android_fps_measured": False,
}
original_suit_triangles = triangles(suit)

# Sleeve fit: detect genuine garment's OPEN boundary loops near the rig wrist.
# Adjust local existing sleeve vertices only. No arm cylinders, no cutouts.
bm = bmesh.new()
bm.from_mesh(suit.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
boundary = [edge for edge in bm.edges if edge.is_boundary]
edge_set = set(boundary)
seen = set()
loops = []
for edge in boundary:
    if edge in seen:
        continue
    stack = [edge]
    component = []
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        component.append(item)
        for v in item.verts:
            stack.extend(e for e in v.link_edges if e in edge_set and e not in seen)
    points = {v for e in component for v in e.verts}
    if len(points) < 6:
        continue
    center = sum((suit.matrix_world @ v.co for v in points), Vector()) / len(points)
    loops.append((center, len(points)))
bm.free()
data["source_boundary_loops"] = len(loops)

mat_world = suit.matrix_world.copy()
world_inverse = mat_world.inverted()
sleeves = {}
for side in ("L", "R"):
    shoulderbone = rig.pose.bones.get("upperarm01." + side)
    forearm = rig.pose.bones.get("lowerarm01." + side)
    assert shoulderbone and forearm
    shoulder = rig.matrix_world @ shoulderbone.head
    wrist = rig.matrix_world @ forearm.tail
    direction = (wrist - shoulder).normalized()
    candidates = [(center, n) for center, n in loops
                  if 8 <= n <= 400 and
                  abs(center.x - cx) > .29 and
                  (center.x - cx) * (wrist.x - cx) > 0 and
                  (center - wrist).length < .34]
    candidates.sort(key=lambda v: (v[0] - wrist).length)
    report = {"side": side, "wrist": list(wrist), "candidate_rings": len(candidates)}
    if candidates:
        cuff, n = candidates[0]
        # Target cuff 16 mm above wrist, leaving the gloved hand visible.
        target = wrist - direction * .016
        difference = target - cuff
        if difference.length > .095:
            difference *= .095 / difference.length
        # Constrain corrective motion to the actual forearm direction.
        correction = direction * difference.dot(direction)
        start_t = (cuff - shoulder).dot(direction) - .26
        end_t = (cuff - shoulder).dot(direction) - .012
        touched = 0
        for vertex in suit.data.vertices:
            p = mat_world @ vertex.co
            if (p.x - cx) * (wrist.x - cx) <= 0:
                continue
            if (p - wrist).length > .42:
                continue
            t = (p - shoulder).dot(direction)
            weight = smoothstep(start_t, end_t, t)
            if weight < .0001:
                continue
            vertex.co = world_inverse @ (p + correction * weight)
            touched += 1
        report.update({"ring_vertices": n, "cuff_shift_m": correction.length,
                       "altered_vertices": touched})
    else:
        report.update({"warning": "No verified cuff ring: preserved original geometry"})
    sleeves[side] = report
suit.data.update()
data["sleeve_corrections"] = sleeves
data["source_suit_triangles"] = original_suit_triangles
data["after_suit_triangles"] = triangles(suit)
assert triangles(suit) == original_suit_triangles, "Garment topology lost"

# Establish more coherent wardrobe materials while retaining original
# artist-modeled seams, shirt/collar polygons, topology and UV coordinates.
for mat in suit.data.materials:
    if mat is None or not mat.use_nodes:
        continue
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Roughness"].default_value = .79
        bsdf.inputs["Metallic"].default_value = .0
# The phase 4 shirt was ALREADY classified from its original CC0 UV atlas.
oldshirt = bpy.data.materials.get("Cuervo_Camisa_Negra_Grafito")
if oldshirt and oldshirt.use_nodes:
    shader = oldshirt.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (.024, .028, .034, 1)
        shader.inputs["Roughness"].default_value = .91
# Add only restrained microstructure to live Blender materials, never a
# fake replacement garment. This is a studio shader; GLB retains base PBR.
for mat in suit.data.materials:
    if mat is None or not mat.use_nodes or mat == oldshirt:
        continue
    nodes = mat.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    if shader is None:
        continue
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 480.
    noise.inputs["Detail"].default_value = 1.2
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .045
    bump.inputs["Distance"].default_value = .0012
    mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mat.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])

# Realistic restrained skin tone for bare face, tailored black gloves for
# skin-derived HAND meshes, without fabricating oversized replacement hands.
complexion = principled("Cuervo_Piel_Natural_Mate", (.42, .302, .249), .91)
gloves = principled("Cuervo_Guantes_Cuero_Negro", (.019, .021, .025), .68)
gloved_faces = 0
bare_faces = 0
for obj in skin:
    obj.data.materials.clear()
    obj.data.materials.append(complexion)
    obj.data.materials.append(gloves)
    for poly in obj.data.polygons:
        p = sum((obj.matrix_world @ obj.data.vertices[vi].co
                 for vi in poly.vertices), Vector()) / len(poly.vertices)
        on_hand = abs(p.x - cx) > .30 and low.z + .86 < p.z < low.z + 1.29
        poly.material_index = 1 if on_hand else 0
        gloved_faces += int(on_hand)
        bare_faces += int(not on_hand)
data["genuine_hand_glove_faces"] = gloved_faces
data["remaining_skin_faces"] = bare_faces

# Hair cap conforms exactly to the existing CC0 human scalp. Keep the
# character's own facial anatomy. Copy a small section of original skin,
# rather than adding a sphere or a planar false hairstyle.
head_source = max(base, key=lambda item: len(item.data.polygons))
hair = head_source.copy()
hair.data = head_source.data.copy()
hair.name = "ElCuervo_CabelloCorto_EscalpOriginal"
scene.collection.objects.link(hair)
hair.hide_render = False
hair.hide_set(False)
hair.matrix_world = head_source.matrix_world.copy()
m = hair.matrix_world.copy()
hair_mesh = bmesh.new()
hair_mesh.from_mesh(hair.data)
removed = []
for face in hair_mesh.faces:
    pts = [m @ v.co for v in face.verts]
    # Short close-cut hairstyle: higher hairline in front, lower at nape.
    keep = all((p.z - low.z > 1.762) or
               ((p.z - low.z > 1.713) and (p.y > cy + .047))
               for p in pts)
    if not keep:
        removed.append(face)
bmesh.ops.delete(hair_mesh, geom=removed, context="FACES")
bmesh.ops.delete(hair_mesh,
                 geom=[v for v in hair_mesh.verts if not v.link_faces],
                 context="VERTS")
hair_mesh.to_mesh(hair.data)
hair_mesh.free()
hair.data.update()
assert 200 < triangles(hair) < 40000, "Scalp topology invalid"
# Lift hair mesh slightly off the anatomically correct scalp, with natural
# short-hair variation measured in mm, preserving existing hairline.
for v in hair.data.vertices:
    p = hair.matrix_world @ v.co
    h = smoothstep(1.72, 1.82, p.z - low.z)
    thickness = .004 + .011 * h
    v.co += v.normal * thickness
hair.data.update()
hair.data.materials.clear()
hair.data.materials.append(principled(
    "Cuervo_Cabello_CastanoOscuro", (.037, .026, .021), .87))
assert any(md.type == "ARMATURE" for md in hair.modifiers), \
    "Hair must retain the original 163-bone skinning"
data["scalp_source"] = head_source.name
data["hair_triangles"] = triangles(hair)
data["hair_is_sculpt_from_original_anatomy"] = True

for b in base:
    b.hide_render = True

# Produce real Blender renders for review. These diagnose the actual GLB
# geometry and pose changes; they are not AI renders or concept art.
camera = scene.camera
assert camera
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 780
scene.render.resolution_y = 1040
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
focus = Vector((cx, cy, low.z + H * .52))

def render(name, offset, point=None, scale=2.27):
    at = focus if point is None else point
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    camera.location = at + Vector(offset)
    camera.rotation_euler = (at - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath) > 5000

render("01_Frontal_Apose", (0, -4.3, .13))
render("02_TresCuartos_Apose", (2.8, -3.7, .14))
render("03_Espalda_Apose", (0, 4.3, .13))
render("04_Rostro_Cuello", (1.15, -3.9, .14),
       Vector((cx, cy, low.z + H * .83)), .74)
render("05_Mano_Manga", (1.4, -3.8, .10),
       Vector((cx + .38, cy, low.z + H * .59)), .65)

previous = {}
for side, angle in (("L", -.50), ("R", .50)):
    bone = rig.pose.bones.get("upperarm01." + side)
    assert bone
    previous[side] = (bone.rotation_mode,
                      bone.rotation_euler.copy(), bone.rotation_quaternion.copy())
    bone.rotation_mode = "QUATERNION"
    bone.rotation_quaternion = Quaternion(Vector((0, 0, 1)), angle) @ \
                               bone.rotation_quaternion
bpy.context.view_layer.update()
render("06_Frontal_BrazosBajos", (0, -4.3, .13))
render("07_TresCuartos_BrazosBajos", (2.8, -3.7, .14))
for side in ("L", "R"):
    bone = rig.pose.bones["upperarm01." + side]
    mode, euler, quaternion = previous[side]
    bone.rotation_quaternion = quaternion
    bone.rotation_mode = mode
    bone.rotation_euler = euler
bpy.context.view_layer.update()

# Export reimportable character asset, without original source body or camera.
bpy.ops.file.pack_all()
blend = os.path.join(out, "El_Cuervo_Refinado_Fase6_REVISION.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
assert os.path.getsize(blend) > 10000
bpy.ops.object.select_all(action="DESELECT")
to_export = [rig, suit, hair] + skin + boots
for obj in to_export:
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
glb = os.path.join(out, "El_Cuervo_Refinado_Fase6_REVISION.glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB",
                          use_selection=True, export_materials="EXPORT",
                          export_yup=True)
with open(glb, "rb") as f:
    magic, version, length = struct.unpack("<4sII", f.read(12))
    assert magic == b"glTF" and version == 2 and length == os.path.getsize(glb)
    jsize, jtype = struct.unpack("<I4s", f.read(8))
    assert jtype == b"JSON"
    g = json.loads(f.read(jsize).decode("utf8"))
names = [n.get("name") for n in g["nodes"] if "mesh" in n]
assert suit.name in names and hair.name in names
assert any(n.startswith("Cuervo_Botin_CC0") for n in names)
assert len(g.get("skins", [])) >= 1
assert all("skin" in node for node in g["nodes"] if "mesh" in node)
data["exported_mesh_nodes"] = names
data["visible_triangles"] = sum(triangles(o) for o in to_export if o.type == "MESH")
data["blender_file"] = os.path.basename(blend)
data["glb_file"] = os.path.basename(glb)
data["blender_reimport_verified"] = False
data["godot43_import_verified"] = False
data["warnings"] = [
    "Review facial hairline and sleeve alignment in genuine renders",
    "Scalp and gloves use native mesh; no geometry primitives added",
    "No Android framerate measurement and no gameplay animation approval",
    "No change to current game build or main branch",
]
with open(os.path.join(out, "AUDITORIA_FASE6.json"), "w", encoding="utf8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("EL_CUERVO_FASE6_REAL_ASSET_CREATED", json.dumps(data, ensure_ascii=False), flush=True)
