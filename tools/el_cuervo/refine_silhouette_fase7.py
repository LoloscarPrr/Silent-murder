"""SILENT KILLER — EL CUERVO / PHASE 7
Refine the genuine MakeHuman/MPFB compatible CC0 character already verified in
Blender and Godot. Do NOT rebuild the broken Phase 4/5 tailored garments.
Isolated production candidate: tighter knee-length coat, matte tactical gloves,
cleaner shoulder/waist silhouette, preserved face and single 53-bone skeleton.

Blender 4.3:
 --blend character_assets/el_cuervo/complete_candidate/El_Cuervo_Candidato_Profesional_CC0.blend
 --out character_assets/el_cuervo/refine_fase7

Outputs true .blend/.glb and six actual Blender renders. No edits to main/game.
"""
import bpy
import bmesh
import os
import sys
import json
import struct
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name):
    assert name in argv, "Missing " + name
    return os.path.abspath(argv[argv.index(name) + 1])
source = arg("--blend")
out = arg("--out")
assert os.path.isfile(source)
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=source)
scene = bpy.context.scene

human = bpy.data.objects.get("Body")
coat = bpy.data.objects.get("Cloth_trenchcoat")
shirt = bpy.data.objects.get("Cloth_shirt")
hair = bpy.data.objects.get("Hair_short04")
assert all(o and o.type == "MESH" for o in (human, coat, shirt, hair))
rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
assert len(rigs) == 1, ("Expected one production rig", [o.name for o in rigs])
rig = rigs[0]
assert len(rig.data.bones) == 53
assert all(any(m.type == "ARMATURE" and m.object == rig
               for m in obj.modifiers) for obj in (human, coat, shirt))

def world_bounds(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    mx = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    return mn, mx

def tris(obj):
    return sum(len(poly.vertices) - 2 for poly in obj.data.polygons)

low, high = world_bounds(human)
height = high.z - low.z
assert 1.80 < height < 1.88, ("Human scale mismatch", height)
cx = (low.x + high.x) / 2.0
cy = (low.y + high.y) / 2.0
hem_z = low.z + height * .305    # knee length rather than ankle-length robe
waist_z = low.z + height * .568

def smooth(a,b,x):
    t = max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3-2*t)

report = {
    "status": "ARTISTIC_REVIEW_PENDING",
    "source_blend": os.path.basename(source),
    "source_assets": "MakeHuman CC0 / CharacterCreator by kblood",
    "license_citation": "See upstream MakeHuman system assets CC0 and repository licenses",
    "game_main_modified": False,
    "character_height_m": height,
    "rig_bones": len(rig.data.bones),
    "original_outfit_triangles": tris(coat),
    "base_human_triangles": tris(human),
    "hair_triangles": tris(hair),
    "original_eye_mesh_kept": bpy.data.objects.get("Eyes") is not None,
    "original_compatible_skinning_kept": True,
    "artistic_approval": False,
    "android_fps_measured": False,
    "gameplay_animations_tested": False,
}

# Tailor the actual high-quality, authored CC0 coat.
# No cylinder geometry and no generic scissor hole around the collar.
mat = coat.matrix_world.copy()
inv = mat.inverted()
edited = 0
for vertex in coat.data.vertices:
    p = mat @ vertex.co
    h = p.z
    # Cinch the front waist without compressing sleeves or shoulder tops.
    waist_band = (smooth(waist_z-.17, waist_z-.035, h) *
                  (1.-smooth(waist_z+.085, waist_z+.26, h)))
    ax = abs(p.x-cx)
    torso_mask = 1.-smooth(.32,.52,ax)
    # Below the waist, taper the hanging coat panels gradually.
    hem_factor = 1.-smooth(hem_z,waist_z-.04,h)
    if h < waist_z:
        factor = 1.0 - .17 * hem_factor
    else:
        factor = 1.0
    factor *= (1.0 - .052 * waist_band * torso_mask)
    if abs(factor - 1) > .0001:
        p.x = cx + (p.x - cx) * factor
        vertex.co = inv @ p
        edited += 1
coat.data.update()
report["coat_vertices_tailored"] = edited
assert edited > 150, "Tailoring has not affected the real garment"

# Crop ONLY the coat, not other meshes. This creates a functional coat instead
# of the previous ankle-length fabric tube. Source UVs and vertex weights stay.
bm = bmesh.new()
bm.from_mesh(coat.data)
geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
local_co = inv @ Vector((cx,cy,hem_z))
normal_local = mat.to_3x3().transposed() @ Vector((0,0,1))
normal_local.normalize()
before_faces = len(bm.faces)
bmesh.ops.bisect_plane(bm, geom=geom, dist=.00001, plane_co=local_co,
                       plane_no=normal_local, clear_inner=True, clear_outer=False)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces],
                 context="VERTS")
after_faces = len(bm.faces)
assert after_faces > 800 and after_faces < before_faces, \
       ("Coat trimming did not happen", before_faces, after_faces)
bm.to_mesh(coat.data)
bm.free()
coat.data.update()
report.update(coat_faces_before=before_faces,coat_faces_after=after_faces,
              coat_triangles_after=tris(coat),cut_hem_height_m=hem_z)
# No geometry was cut from actual body, skull, hair, shoes or hands.

# Matte black, restrained finish. The original textured Blender material
# stays in place; this adjusts its existing multiplier rather than inventing
# a plastic-looking replacement.
for obj in (coat, shirt):
    for material in obj.data.materials:
        if material is None or not material.use_nodes:
            continue
        shader = material.node_tree.nodes.get("Principled BSDF")
        if shader:
            shader.inputs["Roughness"].default_value = .87 if obj==coat else .91
            shader.inputs["Metallic"].default_value = 0.0
        for node in material.node_tree.nodes:
            if node.type == "MIX_RGB" and node.blend_type == "MULTIPLY":
                node.inputs[2].default_value = (.041,.045,.052,1) if obj==coat \
                    else (.075,.081,.094,1)

# Convert real original body hand surface into discreet leather gloves via
# per-face materials, retaining exactly the body's original 53-bone weights.
# Face/neck remain untouched, not a separate pair of primitive hands.
glove = bpy.data.materials.new("ElCuervo_GuantesNegros_RubberizedLeather")
glove.use_nodes = True
glove.diffuse_color = (.014,.016,.019,1)
glove_shader = glove.node_tree.nodes.get("Principled BSDF")
glove_shader.inputs["Base Color"].default_value = (.014,.016,.019,1)
glove_shader.inputs["Roughness"].default_value = .72
glove_shader.inputs["Metallic"].default_value = .02
human.data.materials.append(glove)
glove_slot = len(human.data.materials)-1
hand_bones = [rig.data.bones.get("hand_l"),rig.data.bones.get("hand_r")]
if not all(hand_bones):
    hand_bones = [b for b in rig.data.bones if b.name.lower().startswith(("hand_","wrist_"))][:2]
assert len(hand_bones) == 2, [b.name for b in rig.data.bones][-25:]
wrist_centers = [rig.matrix_world @ b.head_local for b in hand_bones]
colored = 0
for face in human.data.polygons:
    center = sum((human.matrix_world @ human.data.vertices[i].co
                  for i in face.vertices), Vector())/len(face.vertices)
    near_wrist = min((center-w).length for w in wrist_centers) < height * .155
    # Require lateral hand area to avoid coloring neck or torso.
    far_side = abs(center.x-cx) > height*.206
    if near_wrist and far_side:
        face.material_index = glove_slot
        colored += 1
report["body_faces_recolored_glove"] = colored
report["hand_bone_names"] = [b.name for b in hand_bones]
assert colored > 50, ("Failed to place gloves",colored)

# Render exact meshes, with no AI-generated concept art. We use a more
# cinematic but neutral studio background and direct character framing.
cam = scene.camera
assert cam is not None
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 20
scene.cycles.use_denoising = True
scene.render.resolution_x = 820
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
focus = Vector((cx,cy,low.z + height*.53))

def capture(name,offset,target=focus,scale=None):
    cam.data.type="ORTHO"
    cam.data.ortho_scale=height*1.24 if scale is None else scale
    cam.location=target+Vector(offset)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=os.path.join(out,name+".png")
    bpy.ops.render.render(write_still=True)
    assert os.path.getsize(scene.render.filepath)>6000, name
capture("01_Cuervo_Refinado_Frontal",(0,-4,.12))
capture("02_Cuervo_Refinado_TresCuartos",(2.75,-3.8,.14))
capture("03_Cuervo_Refinado_Posterior",(0,4.1,.12))
capture("04_Cuervo_Detalle_Rostro",(1.1,-3.8,.09),
        Vector((cx,cy,low.z+height*.83)),height*.59)
capture("05_Cuervo_Guantes_Mangas",(1.3,-3.6,.12),
        Vector((cx+.41,cy,low.z+height*.61)),height*.65)
capture("06_Cuervo_Caida_Abrigo",(1.15,-3.7,.13),
        Vector((cx,cy,low.z+height*.43)),height*.91)

bpy.ops.file.pack_all()
blend=os.path.join(out,"El_Cuervo_Refinado_Fase7_REVISION.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
assert os.path.getsize(blend)>100000

bpy.ops.object.select_all(action="DESELECT")
exports=[obj for obj in bpy.data.objects if obj.type=="MESH" or obj==rig]
for obj in exports: obj.select_set(True)
bpy.context.view_layer.objects.active=rig
glb=os.path.join(out,"El_Cuervo_Refinado_Fase7_REVISION.glb")
bpy.ops.export_scene.gltf(filepath=glb,export_format="GLB",
                          use_selection=True,export_materials="EXPORT",
                          export_yup=True)
with open(glb,"rb") as file:
    magic,version,length=struct.unpack("<4sII",file.read(12))
    assert magic==b"glTF" and version==2 and length==os.path.getsize(glb)
    chunk,kind=struct.unpack("<I4s",file.read(8))
    assert kind==b"JSON"
    tree=json.loads(file.read(chunk).decode("utf-8"))
mesh_names=[node.get("name") for node in tree["nodes"] if "mesh" in node]
assert "Cloth_trenchcoat" in mesh_names and "Body" in mesh_names,mesh_names
assert len(tree.get("skins",[]))>=1, "The GLB lost its skeleton"
report.update(glb_nodes=mesh_names,
              total_triangles=sum(tris(o) for o in exports if o.type=="MESH"),
              glb_bytes=os.path.getsize(glb),
              blend_file=os.path.basename(blend),
              glb_file=os.path.basename(glb),
              blender_reimport_verified=False,
              godot43_import_verified=False,
              warnings=[
                "Artistic review required; not approved until real renders inspected.",
                "No proof of Android FPS, animation skinning in combat or cloth dynamics.",
                "Separate branch and art directory; no change to main or APK."
              ])
with open(os.path.join(out,"AUDITORIA_FASE7.json"),"w",encoding="utf8") as file:
    json.dump(report,file,indent=2,ensure_ascii=False)
print("CUERVO_FASE7_ACTUAL_GLB_AND_RENDERS",json.dumps(report,ensure_ascii=False),flush=True)
