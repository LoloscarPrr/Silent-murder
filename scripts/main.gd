extends Node3D
## Silent Killer v0.6: Noche Cero mission with obstacle-aware guard routing.

const PLAYER_SCRIPT = preload("res://scripts/player_controller.gd")
const UI_SCRIPT = preload("res://scripts/mobile_controls.gd")
const TARGET_SCRIPT = preload("res://scripts/training_target.gd")
const GUARD_SCRIPT = preload("res://scripts/guard_ai.gd")
const MISSION_SCRIPT = preload("res://scripts/mission_manager.gd")
const NAVIGATION_SCRIPT = preload("res://scripts/grid_navigation.gd")
var _player: CharacterBody3D
var _level: Node3D
var _navigation
var _targets_total := 0
var _targets_disabled := 0
var _guards_total := 0
var _guards_disabled := 0
var _guards: Array[CharacterBody3D] = []
var _hud
var _mission

func _ready() -> void:
 _make_environment()
 _navigation = NAVIGATION_SCRIPT.new()
 _navigation.name = "WarehouseRouteGrid"
 add_child(_navigation)
 _level = Node3D.new()
 _level.name = "Depot_Blockout_00"
 add_child(_level)
 _build_depot()
 _navigation.build()
 _build_practice_range()
 _player = PLAYER_SCRIPT.new()
 _player.position = Vector3(0.0, 0.18, 9.0)
 add_child(_player)
 _player.weapon_fired.connect(_on_player_shot)
 _player.player_defeated.connect(_on_player_defeated)
 _spawn_guards()
 _hud = UI_SCRIPT.new()
 _hud.operative = _player
 add_child(_hud)
 _hud.set_training_progress(_targets_disabled,_targets_total)
 _hud.set_guard_progress(_guards_disabled,_guards_total)
 _hud.set_health(_player.health,_player.MAX_HEALTH)
 _player.health_changed.connect(_hud.set_health)
 _mission = MISSION_SCRIPT.new()
 _mission.player = _player
 _mission.hud = _hud
 _mission.guards = _guards
 _hud.mission_manager = _mission
 add_child(_mission)

func _spawn_guards() -> void:
 var paths: Array[Array] = [
  [Vector3(-3.2,.15,5.0),Vector3(-3.2,.15,0.3),Vector3(-3.2,.15,-4.7)],
  [Vector3(3.2,.15,-5.0),Vector3(3.2,.15,.8),Vector3(3.2,.15,6.2)],
  [Vector3(-2.1,.15,-12.5),Vector3(1.5,.15,-12.5),Vector3(1.5,.15,-8.2)]
 ]
 for i in range(paths.size()):
  var guard := GUARD_SCRIPT.new()
  guard.player = _player
  guard.navigation = _navigation
  guard.position = paths[i][0]
  guard.waypoints.assign(paths[i])
  guard.name = "Guard_%02d" % (i + 1)
  _level.add_child(guard)
  guard.guard_disabled.connect(_on_guard_disabled)
  guard.awareness_changed.connect(_on_guard_awareness)
  _guards.append(guard)
  _guards_total += 1

func _on_player_shot(origin: Vector3, radius: float) -> void:
 for guard in _guards:
  if not guard.is_disabled:
   guard.hear_noise(origin,radius)
 _refresh_guard_status()

func _on_guard_disabled(_guard: Node3D) -> void:
 _guards_disabled += 1
 if _hud != null:
  _hud.set_guard_progress(_guards_disabled,_guards_total)
 _refresh_guard_status()

func _on_guard_awareness(_guard: Node3D,_new_state: String) -> void:
 _refresh_guard_status()

func _refresh_guard_status() -> void:
 if _hud == null:
  return
 var state := "PATRULLA"
 for guard in _guards:
  if guard.is_disabled:
   continue
  if guard.state == guard.ALERT:
   state = "ALERTA"
   break
  elif guard.state == guard.INVESTIGATE or guard.state == guard.SEARCH:
   state = "SOSPECHA"
 _hud.set_alert_status(state)

func _on_player_defeated() -> void:
 if _mission != null:
  _mission.on_player_defeated()
 else:
  for guard in _guards:
   guard.reset_after_player_defeat()
 _refresh_guard_status()

func _build_practice_range() -> void:
 # Clear forward lanes allow precision aiming while keeping the existing level.
 for location in [
  Vector3(-3.1,1.42,3.1),
  Vector3(0.5,1.42,-2.9),
  Vector3(3.5,1.42,2.1),
  Vector3(1.9,1.42,-11.2)
 ]:
  var target := TARGET_SCRIPT.new()
  target.name = "PracticeTarget_%d" % (_targets_total + 1)
  target.position = location
  _level.add_child(target)
  target.disabled.connect(_on_target_disabled)
  _targets_total += 1

func _on_target_disabled(_target: Node3D) -> void:
 _targets_disabled += 1
 if _hud != null:
  _hud.set_training_progress(_targets_disabled,_targets_total)
 if _targets_disabled == _targets_total and _player != null:
  _player.status_changed.emit("Entrenamiento completo: %d blancos" % _targets_total)

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

func _solid(label: String, at: Vector3, dimensions: Vector3, mat: StandardMaterial3D, collidable: bool = true) -> void:
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
  if _navigation != null:
   _navigation.add_obstacle(at,dimensions)
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
