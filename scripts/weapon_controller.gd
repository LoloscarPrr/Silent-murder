extends Node3D
## Alpha 0.4: hit-scan pistol with sound events for nearby guards.
## Runs the physics ray from screen center in _physics_process for safe queries.

signal ammo_updated(magazine: int, reserve: int)
signal shot_report(message: String)
signal gunshot_at(origin: Vector3, radius: float)

const MAG_CAPACITY := 12
const START_RESERVE := 48
const SHOT_INTERVAL := .22
const RELOAD_DURATION := 1.30
const RANGE := 95.0

var operative: CharacterBody3D
var camera: Camera3D
var visual
var magazine := MAG_CAPACITY
var reserve := START_RESERVE
var shots_fired := 0
var hits := 0

var _trigger_held := false
var _cooldown := 0.0
var _reload_left := 0.0
var _muzzle: Marker3D
var _flash: MeshInstance3D
var _flash_left := 0.0

func _ready() -> void:
 name = "TrainingPistol"
 _attach_pistol()
 ammo_updated.emit(magazine,reserve)

func _physics_process(delta: float) -> void:
 _cooldown = maxf(0.0,_cooldown-delta)
 _flash_left = maxf(0.0,_flash_left-delta)
 if _flash != null:
  _flash.visible = _flash_left > 0.0
 if _reload_left > 0.0:
  _reload_left = maxf(0.0,_reload_left-delta)
  if _reload_left == 0.0:
   var amount := mini(MAG_CAPACITY - magazine,reserve)
   magazine += amount
   reserve -= amount
   ammo_updated.emit(magazine,reserve)
   shot_report.emit("Recarga completa")
  return
 if _trigger_held and _cooldown <= 0.0:
  _fire_now()

func set_trigger_held(held: bool) -> void:
 _trigger_held = held

func request_reload() -> void:
 if _reload_left > 0.0 or magazine >= MAG_CAPACITY or reserve <= 0:
  return
 _reload_left = RELOAD_DURATION
 shot_report.emit("Recargando...")

func get_ammo_label() -> String:
 return "%02d / %02d" % [magazine,reserve]

func is_reloading() -> bool:
 return _reload_left > 0.0

func _fire_now() -> void:
 _cooldown = SHOT_INTERVAL
 if magazine <= 0:
  shot_report.emit("Sin munición: RECARGAR")
  return
 magazine -= 1
 shots_fired += 1
 ammo_updated.emit(magazine,reserve)
 _flash_left = .075
 # Silenced shots are not completely inaudible within the depot.
 gunshot_at.emit(operative.global_position,9.0)

 if camera == null or operative == null:
  return
 var screen_center := camera.get_viewport().get_visible_rect().size * .5
 var origin := camera.project_ray_origin(screen_center)
 var direction := camera.project_ray_normal(screen_center).normalized()
 var end := origin + direction * RANGE
 var query := PhysicsRayQueryParameters3D.create(origin,end)
 query.exclude = [operative.get_rid()]
 query.collision_mask = 1
 var ray_hit := get_world_3d().direct_space_state.intersect_ray(query)
 var hit_end := end
 var did_hit_target := false
 if not ray_hit.is_empty():
  hit_end = ray_hit["position"]
  var collider: Object = ray_hit["collider"]
  if collider != null and collider.has_method("receive_shot"):
   did_hit_target = collider.receive_shot(ray_hit["position"],ray_hit["normal"])
 if did_hit_target:
  hits += 1
  shot_report.emit("Impacto confirmado")
 else:
  shot_report.emit("Disparo")
 _draw_tracer(_muzzle.global_position if _muzzle != null else origin,hit_end)

func _draw_tracer(start_point: Vector3,end_point: Vector3) -> void:
 var trace_mesh := ImmediateMesh.new()
 trace_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
 trace_mesh.surface_add_vertex(start_point)
 trace_mesh.surface_add_vertex(end_point)
 trace_mesh.surface_end()
 var trace := MeshInstance3D.new()
 trace.mesh = trace_mesh
 var material := StandardMaterial3D.new()
 material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
 material.albedo_color = Color(1.0,.83,.43)
 trace.material_override = material
 get_tree().current_scene.add_child(trace)
 get_tree().create_timer(.065).timeout.connect(func() -> void:
  if is_instance_valid(trace):
   trace.queue_free()
 )

func _attach_pistol() -> void:
 if visual == null or not is_instance_valid(visual.elbow_right):
  return
 var grip_node: Node3D = visual.elbow_right
 var gun := Node3D.new()
 gun.name = "SuppressedPistol_Blockout"
 gun.position = Vector3(.01,-.40,-.16)
 grip_node.add_child(gun)
 var metal := _mat(Color(.14,.16,.17))
 var black := _mat(Color(.035,.045,.052))
 _box(gun,"Receiver",Vector3(0,0,-.09),Vector3(.17,.15,.36),metal)
 _box(gun,"Slide",Vector3(0,.075,-.12),Vector3(.18,.10,.40),black)
 _box(gun,"Grip",Vector3(0,-.16,.01),Vector3(.12,.26,.14),black)
 _box(gun,"Suppressor",Vector3(0,.05,-.41),Vector3(.095,.095,.37),metal)
 _muzzle = Marker3D.new()
 _muzzle.position = Vector3(0,.05,-.62)
 gun.add_child(_muzzle)
 var flash_mesh := SphereMesh.new()
 flash_mesh.radius = .09
 flash_mesh.height = .14
 _flash = MeshInstance3D.new()
 _flash.mesh = flash_mesh
 var hot := StandardMaterial3D.new()
 hot.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
 hot.albedo_color = Color(1.0,.72,.23)
 _flash.material_override = hot
 _flash.visible = false
 _muzzle.add_child(_flash)

func _box(parent: Node3D,label: String,position: Vector3,dimensions: Vector3,material: Material) -> void:
 var mesh := BoxMesh.new()
 mesh.size = dimensions
 var part := MeshInstance3D.new()
 part.name = label
 part.mesh = mesh
 part.material_override = material
 part.position = position
 parent.add_child(part)

func _mat(tint: Color) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = tint
 material.roughness = .79
 material.metallic = .26
 return material
