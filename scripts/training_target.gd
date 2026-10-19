extends StaticBody3D
## Non-human, stationary practice target. Three impacts to disable.

signal disabled(target: Node3D)

const MAX_HEALTH := 3
var health := MAX_HEALTH
var is_disabled := false
var _face: MeshInstance3D
var _rim: MeshInstance3D
var _healthy_material: StandardMaterial3D
var _disabled_material: StandardMaterial3D

func _ready() -> void:
 add_to_group("training_targets")
 collision_layer = 1
 collision_mask = 0
 _make_target()

func _make_target() -> void:
 _healthy_material = StandardMaterial3D.new()
 _healthy_material.albedo_color = Color(.78,.57,.29)
 _healthy_material.roughness = .82
 _disabled_material = StandardMaterial3D.new()
 _disabled_material.albedo_color = Color(.18,.22,.24)
 _disabled_material.roughness = .90
 var outline := StandardMaterial3D.new()
 outline.albedo_color = Color(.085,.12,.14)

 var pedestal := MeshInstance3D.new()
 var post_mesh := BoxMesh.new()
 post_mesh.size = Vector3(.13,1.20,.16)
 pedestal.mesh = post_mesh
 pedestal.position = Vector3(0,-.66,.035)
 pedestal.material_override = outline
 add_child(pedestal)

 _rim = MeshInstance3D.new()
 var rim_mesh := BoxMesh.new()
 rim_mesh.size = Vector3(.87,1.12,.12)
 _rim.mesh = rim_mesh
 _rim.material_override = outline
 add_child(_rim)

 _face = MeshInstance3D.new()
 var plate := BoxMesh.new()
 plate.size = Vector3(.67,.94,.14)
 _face.mesh = plate
 _face.position.z = -.018
 _face.material_override = _healthy_material
 add_child(_face)

 var decal := MeshInstance3D.new()
 var center_plate := BoxMesh.new()
 center_plate.size = Vector3(.22,.30,.018)
 decal.mesh = center_plate
 decal.position.z = -.098
 decal.material_override = outline
 _face.add_child(decal)

 var collision := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = Vector3(.87,1.12,.25)
 collision.shape = box
 add_child(collision)

func receive_shot(_point: Vector3, _normal: Vector3) -> bool:
 if is_disabled:
  return false
 health -= 1
 if health <= 0:
  is_disabled = true
  collision_layer = 0
  _face.material_override = _disabled_material
  _rim.rotation.z = deg_to_rad(9.0)
  disabled.emit(self)
 else:
  var ratio := float(health)/float(MAX_HEALTH)
  _healthy_material.albedo_color = Color(.78,.28 + .29*ratio,.17+.12*ratio)
 return true
