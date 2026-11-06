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
        if difference.length > .135:
            difference *= .135 / difference.length
        # Correct the full three-dimensional cuff/wrist offset. Restricting
        # the motion to the bone axis preserved the camera-space gap in v6.
        correction = difference * .85
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
        report.update({"ring_vertices": n, "cuff_center_before": list(cuff),
                       "target_wrist_center": list(target),
                       "cuff_shift_world": list(correction),
                       "cuff_shift_m": correction.length,
                       "altered_vertices": touched})
    else:
        report.update({"warning": "No verified cuff ring: preserved original geometry"})
    sleeves[side] = report
suit.data.update()
data["sleeve_corrections"] = sleeves
# Restrained shoulder refinement, with a compact weight function that
# fades at sleeve and chest seams. No uncontrolled vertex translation.
shoulder_touches = 0
for vertex in suit.data.vertices:
    point = mat_world @ vertex.co
    ax = abs(point.x - cx)
    height = point.z - low.z
    shoulder_blend = (smoothstep(1.35, 1.46, height) *
                      (1 - smoothstep(1.58, 1.66, height)) *
                      smoothstep(.25, .34, ax) *
                      (1 - smoothstep(.61, .73, ax)))
    if shoulder_blend < .001:
        continue
    point.x = cx + (point.x - cx) * (1 - .050 * shoulder_blend)
    point.z -= .010 * shoulder_blend
    vertex.co = world_inverse @ point
    shoulder_touches += 1
suit.data.update()
data["shoulder_vertices_smoothed"] = shoulder_touches

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

# One continuous anatomy-derived hand AND forearm per side. The previous
# visible-skin-only mesh stopped at the wrist and looked like severed hands;
# completing the original forearms is necessary to bridge into the jacket.
complexion = principled("Cuervo_Piel_Natural_Mate", (.42, .302, .249), .91)
gloves = principled("Cuervo_Guantes_Cuero_Negro", (.019, .021, .025), .68)
removed_skin_hand_faces = 0
for obj in skin:
    mesh_bm = bmesh.new()
    mesh_bm.from_mesh(obj.data)
    mat = obj.matrix_world
    doomed = []
    for face in mesh_bm.faces:
        coords = [mat @ v.co for v in face.verts]
        if all(abs(p.x - cx) > .27 and
               low.z + .72 < p.z < low.z + 1.62 for p in coords):
            doomed.append(face)
    removed_skin_hand_faces += len(doomed)
    if doomed:
        bmesh.ops.delete(mesh_bm, geom=doomed, context="FACES")
        bmesh.ops.delete(mesh_bm,
                         geom=[v for v in mesh_bm.verts if not v.link_faces],
                         context="VERTS")
    mesh_bm.to_mesh(obj.data)
    mesh_bm.free()
    obj.data.update()
    obj.data.materials.clear()
    obj.data.materials.append(complexion)
data["hidden_short_wrist_mesh_faces"] = removed_skin_hand_faces

# This clone keeps continuous source arms, palms and fingers + exactly
# their original armature weights. The cut edge stays under the real sleeve.
head_source = max(base, key=lambda item: len(item.data.polygons))
hands = head_source.copy()
hands.data = head_source.data.copy()
hands.name = "ElCuervo_Guantes_AntebrazosContinuos"
scene.collection.objects.link(hands)
hands.hide_render = False
hands.hide_set(False)
hands.matrix_world = head_source.matrix_world.copy()
hands_bm = bmesh.new()
hands_bm.from_mesh(hands.data)
hands_matrix = hands.matrix_world.copy()
doomed = []
for face in hands_bm.faces:
    coords = [hands_matrix @ v.co for v in face.verts]
    if not all(abs(p.x - cx) > .27 and
               low.z + .71 < p.z < low.z + 1.63 for p in coords):
        doomed.append(face)
bmesh.ops.delete(hands_bm, geom=doomed, context="FACES")
bmesh.ops.delete(hands_bm,
                 geom=[v for v in hands_bm.verts if not v.link_faces],
                 context="VERTS")
hands_bm.to_mesh(hands.data)
hands_bm.free()
hands.data.update()
assert 400 < triangles(hands) < 60000, "Hands/forearms failed extraction"
hands.data.materials.clear()
hands.data.materials.append(gloves)
assert any(mod.type == "ARMATURE" for mod in hands.modifiers)
data["continuous_original_hand_triangles"] = triangles(hands)

# Hair from a single anatomically-continuous scalp patch, not individually
# culled triangles. BMesh planar bisect adds clean cuts along existing faces;
# the previous all-vertex face mask left visible triangular bald patches.
hair = head_source.copy()
hair.data = head_source.data.copy()
hair.name = "ElCuervo_CabelloCorto_EscalpOriginal"
scene.collection.objects.link(hair)
hair.hide_render = False
hair.hide_set(False)
hair.matrix_world = head_source.matrix_world.copy()
hair_mesh = bmesh.new()
hair_mesh.from_mesh(hair.data)
hair_matrix = hair.matrix_world.copy()
# Geometry is evaluated in WORLD coordinates; bisect plane must be local.
local_plane_origin = hair_matrix.inverted() @ Vector((cx, cy, low.z + 1.742))
local_plane_normal = hair_matrix.to_3x3().transposed() @ Vector((0, .37, 1))
local_plane_normal.normalize()
bmesh.ops.bisect_plane(
    hair_mesh,
    geom=list(hair_mesh.verts) + list(hair_mesh.edges) + list(hair_mesh.faces),
    plane_co=local_plane_origin,
    plane_no=local_plane_normal,
    dist=.00001,
    clear_inner=True,
    clear_outer=False,
)
# The original MakeHuman scalp has overlapping internal patches.
# Replace those faces with the watertight CONVEX HULL of the real scalp
# vertex coordinates, not with geometric primitives or synthetic hair cards.
# This removes old self-intersecting hair triangles and missing-face holes.
bmesh.ops.delete(hair_mesh, geom=list(hair_mesh.faces), context="FACES_ONLY")
hull = bmesh.ops.convex_hull(
    hair_mesh, input=list(hair_mesh.verts), use_existing_faces=False)
bmesh.ops.delete(
    hair_mesh,
    geom=[v for v in hair_mesh.verts if not v.link_faces],
    context="VERTS",
)
assert sum(1 for f in hair_mesh.faces) > 100, "Scalp hull lost its surface"
hair_mesh.to_mesh(hair.data)
hair_mesh.free()
hair.data.update()
assert 200 < triangles(hair) < 40000, "Contiguous scalp extraction failed"
for v in hair.data.vertices:
    p = hair.matrix_world @ v.co
    top = smoothstep(1.72, 1.82, p.z - low.z)
    # 4-15 mm above the real scalp. No independent floating 'helmet' mesh.
    v.co += v.normal * (.004 + .011 * top)
hair.data.update()
hair.data.materials.clear()
hair.data.materials.append(principled(
    "Cuervo_CabelloCorto_CastanoOscuro", (.039, .029, .026), .88))
assert any(md.type == "ARMATURE" for md in hair.modifiers)
data["scalp_source"] = head_source.name
data["hair_triangles"] = triangles(hair)
data["hair_bisect_continuous"] = True
data["scalp_self_intersection_repair"] = "convex hull of actual CC0 head vertices"
data["face_from_original_mesh"] = True

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
to_export = [rig, suit, hair, hands] + skin + boots
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
    "Hair and full hand/forearm continuity rely on CC0 source anatomy",
    "No Android framerate measurement and no gameplay animation approval",
    "No change to current game build or main branch",
]
with open(os.path.join(out, "AUDITORIA_FASE6.json"), "w", encoding="utf8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("EL_CUERVO_FASE6_REAL_ASSET_CREATED", json.dumps(data, ensure_ascii=False), flush=True)
