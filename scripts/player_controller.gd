extends CharacterBody3D
## Silent Killer v0.5.1 — terminal defeat is not a respawn,
## articulated locomotion and obstacle-aware over-shoulder camera.

signal status_changed(status: String)
signal ammo_changed(magazine: int, reserve: int)
signal health_changed(current: int, maximum: int)
signal player_defeated() 
signal weapon_fired(origin: Vector3, radius: float)

const VISUAL_SCRIPT = preload("res://scripts/operative_visual.gd")
const WEAPON_SCRIPT = preload("res://scripts/weapon_controller.gd")
const WALK_SPEED := 3.75
const SPRINT_SPEED := 6.2
const CROUCH_SPEED := 1.85
const AIM_SPEED := 2.65
const ACCELERATION := 20.0
const DECELERATION := 26.0
const TURN_SMOOTH := 13.0
const TOUCH_SENSITIVITY := .0030
const MOUSE_SENSITIVITY := .0025
const MAX_HEALTH := 100
const STANDING_HEIGHT := 1.8
const CROUCHED_HEIGHT := 1.20

var health := MAX_HEALTH
var controls_locked := false
var _damage_grace := 0.0
var move_input := Vector2.ZERO
var is_sprinting := false
var is_crouching := false
var is_aiming := false

var _desired_yaw := 0.0
var _desired_pitch := -0.09
var _current_pitch := -0.09
var _camera: Camera3D
var _rig: Node3D
var _collider: CollisionShape3D
var _capsule: CapsuleShape3D
var _visual: Node3D
var _weapon

func _ready() -> void:
 name = "SilentKiller_Operative"
 _desired_yaw = rotation.y
 _make_collision()
 _visual = VISUAL_SCRIPT.new()
 add_child(_visual)
 _make_camera()
 _weapon = WEAPON_SCRIPT.new()
 _weapon.operative = self
 _weapon.camera = _camera
 _weapon.visual = _visual
 _weapon.ammo_updated.connect(_on_ammo_updated)
 _weapon.gunshot_at.connect(_on_weapon_fired)
 _weapon.shot_report.connect(_on_shot_report)
 add_child(_weapon)
 status_changed.emit("OPERACIÓN NOCHE CERO • Alpha 0.5.1")
 health_changed.emit(health,MAX_HEALTH)

func _physics_process(delta: float) -> void:
 if controls_locked:
  velocity = Vector3.ZERO
  return
 _damage_grace = maxf(0.0,_damage_grace-delta)
 rotation.y = lerp_angle(rotation.y,_desired_yaw,minf(1.0,TURN_SMOOTH*delta))
 _current_pitch = lerpf(_current_pitch,_desired_pitch,minf(1.0,10.0*delta))
 _rig.rotation.x = _current_pitch

 var keys := Input.get_vector("ui_left","ui_right","ui_up","ui_down")
 var axis := move_input if move_input.length() > .08 else keys
 axis = axis.limit_length(1.0)
 if absf(axis.x) < .045:
  axis.x = 0.0
 if absf(axis.y) < .045:
  axis.y = 0.0
 var running := is_sprinting and not is_crouching and not is_aiming
 var speed := WALK_SPEED
 if is_crouching:
  speed = CROUCH_SPEED
 elif is_aiming:
  speed = AIM_SPEED
 elif running:
  speed = SPRINT_SPEED
 var input_direction := Vector3(axis.x,0.0,axis.y)
 var direction := global_transform.basis * input_direction
 var target := Vector2(direction.x,direction.z) * speed
 var current := Vector2(velocity.x,velocity.z)
 current = current.move_toward(target,(ACCELERATION if axis.length() > .04 else DECELERATION)*delta)
 velocity.x = current.x
 velocity.z = current.y
 if not is_on_floor():
  velocity.y -= 20.0 * delta
 else:
  velocity.y = -0.08
 move_and_slide()

 _update_crouch_shape(delta)
 var horizontal := Vector2(velocity.x,velocity.z).length()
 _visual.animate_pose(delta,minf(1.0,horizontal/maxf(speed,.1)),axis.x,is_crouching,is_aiming,running)
 _update_camera(delta)

func apply_look(delta_pixels: Vector2,touch: bool = true) -> void:
 var sensitivity := TOUCH_SENSITIVITY if touch else MOUSE_SENSITIVITY
 _desired_yaw -= delta_pixels.x * sensitivity
 _desired_pitch = clampf(_desired_pitch - delta_pixels.y * sensitivity,-.88,.52)

func toggle_crouch() -> void:
 if is_crouching:
  if not _can_stand():
   status_changed.emit("No hay espacio para levantarse")
   return
  is_crouching = false
  status_changed.emit("De pie")
 else:
  is_crouching = true
  is_sprinting = false
  status_changed.emit("Sigilo: agachado")

func toggle_aim() -> void:
 is_aiming = not is_aiming
 if is_aiming:
  is_sprinting = false
 status_changed.emit("Modo puntería" if is_aiming else "Explorando")

func set_fire_held(held: bool) -> void:
 if _weapon != null:
  _weapon.set_trigger_held(held)

func reload_weapon() -> void:
 if _weapon != null:
  _weapon.request_reload()

func get_ammo_label() -> String:
 return _weapon.get_ammo_label() if _weapon != null else "-- / --"

func receive_enemy_damage(amount: int) -> void:
 if controls_locked or health <= 0 or _damage_grace > 0.0 or amount <= 0:
  return
 health = maxi(0,health-amount)
 _damage_grace = .48
 health_changed.emit(health,MAX_HEALTH)
 if health == 0:
  _on_defeated()
 else:
  status_changed.emit("Bajo fuego: -%d HP" % amount)

func _on_defeated() -> void:
 # Keep health at zero until the retry button reloads the entire mission.
 # Emit only once even if two guards hit on the same physics frame.
 if controls_locked:
  return
 controls_locked = true
 velocity = Vector3.ZERO
 is_sprinting = false
 is_aiming = false
 move_input = Vector2.ZERO
 set_fire_held(false)
 status_changed.emit("Operativo neutralizado")
 player_defeated.emit()

func _on_weapon_fired(origin: Vector3,radius: float) -> void:
 weapon_fired.emit(origin,radius)

func _on_ammo_updated(magazine: int, reserve: int) -> void:
 ammo_changed.emit(magazine,reserve)

func _on_shot_report(message: String) -> void:
 status_changed.emit(message)

func _make_collision() -> void:
 _capsule = CapsuleShape3D.new()
 _capsule.radius = .32
 _capsule.height = STANDING_HEIGHT
 _collider = CollisionShape3D.new()
 _collider.name = "OperativeCollision"
 _collider.shape = _capsule
 _collider.position.y = STANDING_HEIGHT * .5
 add_child(_collider)

func _update_crouch_shape(delta: float) -> void:
 var wanted := CROUCHED_HEIGHT if is_crouching else STANDING_HEIGHT
 _capsule.height = move_toward(_capsule.height,wanted,delta * 2.5)
 _collider.position.y = _capsule.height*.5

func _can_stand() -> bool:
 var stand := CapsuleShape3D.new()
 stand.radius = _capsule.radius
 stand.height = STANDING_HEIGHT
 var query := PhysicsShapeQueryParameters3D.new()
 query.shape = stand
 query.transform = Transform3D(global_transform.basis,global_position+Vector3.UP*(STANDING_HEIGHT*.5))
 query.exclude = [get_rid()]
 query.collision_mask = collision_mask
 return get_world_3d().direct_space_state.intersect_shape(query,1).is_empty()

func _make_camera() -> void:
 _rig = Node3D.new()
 _rig.name = "ShoulderCameraPivot"
 _rig.position = Vector3(0,1.47,0)
 add_child(_rig)
 _rig.rotation.x = _desired_pitch
 _camera = Camera3D.new()
 _camera.name = "CollisionAwareCamera"
 _camera.position = Vector3(.64,.08,3.00)
 _camera.fov = 66.0
 _camera.near = .06
 _camera.current = true
 _rig.add_child(_camera)

func _update_camera(delta: float) -> void:
 var pivot_height := (1.04 if is_crouching else 1.47)
 _rig.position.y = lerpf(_rig.position.y,pivot_height,minf(1.0,delta*7.0))
 var target_x := .46 if is_aiming else .66
 var target_distance := 2.15 if is_aiming else 3.08
 var desired_local := Vector3(target_x,.10,target_distance)
 var from := _rig.global_position
 var to := _rig.to_global(desired_local)
 var ray := PhysicsRayQueryParameters3D.create(from,to)
 ray.exclude = [get_rid()]
 ray.collision_mask = collision_mask
 var hit := get_world_3d().direct_space_state.intersect_ray(ray)
 var blocked := not hit.is_empty()
 if blocked:
  var allowed := maxf(.35,from.distance_to(hit["position"])-.20)
  desired_local = desired_local.normalized()*allowed
 var response := 16.0 if blocked else 7.5
 _camera.position = _camera.position.lerp(desired_local,minf(1.0,delta*response))
 _camera.fov = lerpf(_camera.fov,51.0 if is_aiming else 66.0,minf(1.0,delta*7.0))
