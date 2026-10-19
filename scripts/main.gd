extends Node3D
## Silent Murder v0.1: a self-contained 3D industrial blockout.

const PLAYER_SCRIPT = preload("res://scripts/player_controller.gd")
const UI_SCRIPT = preload("res://scripts/mobile_controls.gd")
var _player: CharacterBody3D
var _level: Node3D

func _ready() -> void:
 _make_environment()
 _level = Node3D.new()
 _level.name = "Depot_Blockout_00"
 add_child(_level)
 _build_depot()
 _player = PLAYER_SCRIPT.new()
 _player.position = Vector3(0.0, 0.18, 9.0)
 add_child(_player)
 var ui := UI_SCRIPT.new()
 ui.operative = _player
 add_child(ui)

func _make_environment() -> void:
 var world := WorldEnvironment.new()
 var env := Environment.new()
 env.background_mode = Environment.BG_COLOR
 env.background_color = Color(.055,.069,.085)
 env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 env.ambient_light_color = Color(.34,.41,.45)
 env.ambient_light_energy = .8
 world.environment = env
 add_child(world)
 var moon := DirectionalLight3D.new()
 moon.name = "Moonlight"
 moon.rotation_degrees = Vector3(-55,-26,0)
 moon.light_color = Color(.62,.75,.9)
 moon.light_energy = .65
 moon.shadow_enabled = false
 add_child(moon)
 _lamp(Vector3(-5,5,-5),Color(1,.73,.43),5.0)
 _lamp(Vector3(8,5,2),Color(.56,.75,1),4.5)

func _build_depot() -> void:
 var floor_mat := _mat(Color(.17,.20,.22))
 var wall_mat := _mat(Color(.23,.27,.29))
 var crate_mat := _mat(Color(.29,.31,.30))
 var accent := _mat(Color(.43,.29,.16))
 _solid("Warehouse floor", Vector3(0,-.15,0),Vector3(32,.3,32),floor_mat)
 _solid("Wall North",Vector3(0,2.2,-16),Vector3(32,4.4,.6),wall_mat)
 _solid("Wall South",Vector3(0,2.2,16),Vector3(32,4.4,.6),wall_mat)
 _solid("Wall West",Vector3(-16,2.2,0),Vector3(.6,4.4,32),wall_mat)
 _solid("Wall East",Vector3(16,2.2,0),Vector3(.6,4.4,32),wall_mat)
 _solid("Storage rack A",Vector3(-6,1.2,-7),Vector3(2.0,2.4,7.0),crate_mat)
 _solid("Storage rack B",Vector3(6,1.2,-7),Vector3(2.0,2.4,7.0),crate_mat)
 _solid("Loading crate 1",Vector3(-6,.75,2),Vector3(2.2,1.5,2.2),accent)
 _solid("Loading crate 2",Vector3(5.5,.7,5),Vector3(2.0,1.4,2.1),crate_mat)
 _solid("Cargo container",Vector3(9,1.5,-12),Vector3(5.5,3,4),crate_mat)
 _solid("Inspection office",Vector3(-11,1.8,-11),Vector3(4,3.6,5),wall_mat)
 for i in range(7):
  var x := -13.0 + float(i) * 4.2
  _solid("Floor stripe %d" % i,Vector3(x,.013,10.2),Vector3(1.8,.02,.12),accent,false)

func _solid(label: String, at: Vector3, dimensions: Vector3, mat: StandardMaterial3D, collidable := true) -> void:
 var mesh := BoxMesh.new()
 mesh.size = dimensions
 var visual := MeshInstance3D.new()
 visual.name = label
 visual.mesh = mesh
 visual.material_override = mat
 visual.position = at
 if collidable:
  var static_body := StaticBody3D.new()
  static_body.name = label
  var shape := BoxShape3D.new()
  shape.size = dimensions
  var collider := CollisionShape3D.new()
  collider.shape = shape
  static_body.position = at
  visual.position = Vector3.ZERO
  static_body.add_child(visual)
  static_body.add_child(collider)
  _level.add_child(static_body)
 else:
  _level.add_child(visual)

func _lamp(at: Vector3, tint: Color, energy: float) -> void:
 var light := OmniLight3D.new()
 light.position = at
 light.light_color = tint
 light.light_energy = energy
 light.omni_range = 13.0
 light.shadow_enabled = false
 add_child(light)

func _mat(tint: Color) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = tint
 m.metallic = .04
 m.roughness = .94
 return m
