extends CharacterBody3D
## Silent Murder v0.4 — lightweight guard finite-state AI.
## States: patrol -> suspicious/investigate -> alert -> search -> patrol.
## Every sight test uses physics LOS; hearing reacts to shots but not through telepathy.

signal guard_disabled(guard: Node3D)
signal awareness_changed(guard: Node3D, new_state: String)

const PATROL := "PATRULLA"
const INVESTIGATE := "SOSPECHA"
const ALERT := "ALERTA"
const SEARCH := "BUSCANDO"

const WALK_SPEED := 1.45
const CHASE_SPEED := 2.55
const DETECT_RANGE := 14.5
const ATTACK_RANGE := 11.5
const VIEW_ANGLE_DEGREES := 86.0
const SHOOT_COOLDOWN := 1.45
const SHOT_DAMAGE := 7
const MAX_HP := 3

var player: CharacterBody3D
var waypoints: Array[Vector3] = []
var state := PATROL
var health := MAX_HP
var is_disabled := false
var detection := 0.0
var shots_fired := 0

var _waypoint_index := 0
var _interest := Vector3.ZERO
var _last_known := Vector3.ZERO
var _investigate_timer := 0.0
var _lost_timer := 0.0
var _fire_timer := 0.7
var _patrol_pause := 0.0
var _indicator: MeshInstance3D
var _torso: MeshInstance3D
var _left_leg: MeshInstance3D
var _right_leg: MeshInstance3D
var _anim_time := 0.0
var _tint: StandardMaterial3D

func _ready() -> void:
 name = "Guard_%d" % get_instance_id()
 add_to_group("guards")
 collision_layer = 1
 collision_mask = 1
 _build_body()

func _physics_process(delta: float) -> void:
 if is_disabled or player == null or not is_instance_valid(player):
  return
 _fire_timer = maxf(0.0,_fire_timer-delta)
 _patrol_pause = maxf(0.0,_patrol_pause-delta)
 var can_see := can_see_player()
 _update_detection(delta,can_see)
 var destination := global_position
 var speed := 0.0
 match state:
  PATROL:
   if waypoints.size() > 0:
    destination = waypoints[_waypoint_index]
    speed = WALK_SPEED if _patrol_pause <= 0.0 else 0.0
    if _horizontal_distance(destination) < .55:
     _waypoint_index = (_waypoint_index + 1) % waypoints.size()
     _patrol_pause = .55
  INVESTIGATE:
   destination = _interest
   speed = WALK_SPEED * 1.15
   _investigate_timer -= delta
   if _horizontal_distance(destination) < .85 or _investigate_timer <= 0.0:
    _switch(SEARCH)
    _investigate_timer = 2.4
  SEARCH:
   destination = _interest
   speed = WALK_SPEED * .65
   _investigate_timer -= delta
   if _investigate_timer <= 0.0:
    detection = 0.0
    _switch(PATROL)
  ALERT:
   destination = player.global_position if can_see else _last_known
   var distance := _horizontal_distance(destination)
   # Back off slightly once close enough to shoot.
   speed = CHASE_SPEED if distance > 5.3 else 0.0
   if can_see and distance < ATTACK_RANGE and _fire_timer <= 0.0:
    _shoot_player()
   if not can_see:
    _lost_timer += delta
    if _lost_timer >= 4.3:
     _interest = _last_known
     _investigate_timer = 3.0
     _switch(SEARCH)
   else:
    _lost_timer = 0.0
 _move_guard(delta,destination,speed)

func _update_detection(delta: float,seen: bool) -> void:
 if state == ALERT:
  if seen:
   _last_known = player.global_position
  return
 if seen:
  var distance := _horizontal_distance(player.global_position)
  var speed_factor := 1.7 if player.is_sprinting else (0.48 if player.is_crouching else 1.0)
  var proximity := clampf(1.75-distance/15.0,.65,1.65)
  detection = minf(1.0,detection+delta*.60*speed_factor*proximity)
  _last_known = player.global_position
  if detection >= 1.0:
   _switch(ALERT)
  elif state == PATROL:
   _interest = player.global_position
   _investigate_timer = 3.4
   _switch(INVESTIGATE)
 else:
  detection = maxf(0.0,detection-delta*.25)

func can_see_player() -> bool:
 if player == null or not is_instance_valid(player):
  return false
 var eye := global_position + Vector3(0,1.53,0)
 var crouched := player.is_crouching
 var target := player.global_position + Vector3(0,.87 if crouched else 1.30,0)
 var toward := target-eye
 var distance := toward.length()
 if distance > DETECT_RANGE or distance < .001:
  return false
 # Only see actors roughly ahead (unless already fully engaged).
 var forward := -global_transform.basis.z
 var flat_dir := Vector3(toward.x,0,toward.z).normalized()
 var dot := forward.dot(flat_dir)
 if state != ALERT and dot < cos(deg_to_rad(VIEW_ANGLE_DEGREES*.5)):
  return false
 var query := PhysicsRayQueryParameters3D.create(eye,target)
 query.exclude = [get_rid()]
 query.collision_mask = 1
 var hit := get_world_3d().direct_space_state.intersect_ray(query)
 return not hit.is_empty() and hit["collider"] == player

func hear_noise(source: Vector3,radius: float) -> void:
 if is_disabled:
  return
 var distance := _horizontal_distance(source)
 if distance > radius:
  return
 _interest = source
 _last_known = source
 if state == ALERT:
  return
 detection = maxf(detection,.15)
 _investigate_timer = 4.6
 _switch(INVESTIGATE)

func receive_shot(_point: Vector3,_normal: Vector3) -> bool:
 if is_disabled:
  return false
 health -= 1
 if health <= 0:
  is_disabled = true
  collision_layer = 0
  collision_mask = 0
  velocity = Vector3.ZERO
  set_physics_process(false)
  _tint.albedo_color = Color(.18,.21,.22)
  _torso.rotation.z = deg_to_rad(38.0)
  _indicator.visible = false
  guard_disabled.emit(self)
 else:
  detection = 1.0
  _last_known = player.global_position if player != null else global_position
  _switch(ALERT)
 return true

func reset_after_player_defeat() -> void:
 if is_disabled:
  return
 velocity = Vector3.ZERO
 detection = 0.0
 _lost_timer = 0.0
 _investigate_timer = 0.0
 _fire_timer = 1.8
 _switch(PATROL)

func _shoot_player() -> void:
 _fire_timer = SHOOT_COOLDOWN
 if not can_see_player():
  return
 shots_fired += 1
 if player.has_method("receive_enemy_damage"):
  player.receive_enemy_damage(SHOT_DAMAGE)

func _move_guard(delta: float,target: Vector3,speed: float) -> void:
 var delta_position := target-global_position
 delta_position.y = 0.0
 var heading := Vector3.ZERO
 if delta_position.length() > .28 and speed > 0.0:
  heading = delta_position.normalized()
  rotation.y = lerp_angle(rotation.y,atan2(-heading.x,-heading.z),minf(1.0,delta*7.5))
  var target_velocity := heading * speed
  velocity.x = move_toward(velocity.x,target_velocity.x,delta*6.5)
  velocity.z = move_toward(velocity.z,target_velocity.z,delta*6.5)
 else:
  velocity.x = move_toward(velocity.x,0.0,delta*8.0)
  velocity.z = move_toward(velocity.z,0.0,delta*8.0)
 if not is_on_floor():
  velocity.y -= 20.0*delta
 else:
  velocity.y = -.1
 move_and_slide()
 _anim_time += delta*5.6
 var amount := minf(1.0,Vector2(velocity.x,velocity.z).length()/WALK_SPEED)
 _left_leg.rotation.x = sin(_anim_time)*.3*amount
 _right_leg.rotation.x = -sin(_anim_time)*.3*amount

func _switch(next_state: String) -> void:
 if state == next_state:
  return
 state = next_state
 match state:
  PATROL:
   _indicator.material_override = _state_color(Color(.26,.73,.48))
  INVESTIGATE, SEARCH:
   _indicator.material_override = _state_color(Color(1.0,.72,.17))
  ALERT:
   _indicator.material_override = _state_color(Color(.93,.18,.16))
 awareness_changed.emit(self,state)

func _horizontal_distance(point: Vector3) -> float:
 return Vector2(global_position.x,global_position.z).distance_to(Vector2(point.x,point.z))

func _build_body() -> void:
 var capsule := CapsuleShape3D.new()
 capsule.radius = .34
 capsule.height = 1.78
 var body_collision := CollisionShape3D.new()
 body_collision.shape = capsule
 body_collision.position.y = .91
 add_child(body_collision)
 var fabric := _state_color(Color(.20,.24,.27))
 var armor := _state_color(Color(.12,.16,.18))
 var dark := _state_color(Color(.044,.054,.063))
 _tint = fabric
 _torso = _mesh_box(self,"GuardJacket",Vector3(0,1.29,0),Vector3(.54,.64,.34),fabric)
 _mesh_box(self,"LightVest",Vector3(0,1.36,-.19),Vector3(.38,.46,.055),armor)
 _mesh_box(self,"Head",Vector3(0,1.82,0),Vector3(.31,.30,.31),dark)
 _mesh_box(self,"LeftArm",Vector3(-.36,1.3,0),Vector3(.16,.67,.19),fabric)
 _mesh_box(self,"RightArm",Vector3(.36,1.3,0),Vector3(.16,.67,.19),fabric)
 _left_leg = _mesh_box(self,"LeftLeg",Vector3(-.16,.50,0),Vector3(.23,.93,.22),armor)
 _right_leg = _mesh_box(self,"RightLeg",Vector3(.16,.50,0),Vector3(.23,.93,.22),armor)
 _indicator = _mesh_box(self,"AwarenessIndicator",Vector3(0,2.18,0),Vector3(.18,.12,.18),_state_color(Color(.26,.73,.48)))

func _mesh_box(parent: Node3D,label: String,at: Vector3,scale_size: Vector3,mat: Material) -> MeshInstance3D:
 var mesh := BoxMesh.new()
 mesh.size = scale_size
 var part := MeshInstance3D.new()
 part.name = label
 part.mesh = mesh
 part.position = at
 part.material_override = mat
 parent.add_child(part)
 return part

func _state_color(tint: Color) -> StandardMaterial3D:
 var material := StandardMaterial3D.new()
 material.albedo_color = tint
 material.roughness = .82
 return material
