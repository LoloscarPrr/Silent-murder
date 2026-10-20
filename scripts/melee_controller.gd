extends Node
## Alpha 0.5.3 — stealth requires a truly unaware patrolling guard.
## No ammunition or automatic attacks. Player must press the contextual button.

signal availability_changed(available: bool, label: String)
signal attack_performed(stealth: bool)
signal attack_message(message: String)

const RANGE := 1.90
const COOLDOWN := 0.75
const CHECK_INTERVAL := 0.12

var player: CharacterBody3D
var _cooldown := 0.0
var _scan_wait := 0.0
var _available := false
var _last_label := ""

func _physics_process(delta: float) -> void:
 _cooldown = maxf(0.0, _cooldown-delta)
 _scan_wait -= delta
 if _scan_wait <= 0.0:
  _scan_wait = CHECK_INTERVAL
  var info := find_target()
  var can_attack := not info.is_empty() and _cooldown <= 0.0
  var label := ""
  if can_attack:
   label = "REDUCIR" if info["stealth"] else "GOLPEAR"
  if can_attack != _available or label != _last_label:
   _available = can_attack
   _last_label = label
   availability_changed.emit(_available,label)

func try_attack() -> bool:
 if _cooldown > 0.0 or player == null or player.controls_locked or player.health <= 0:
  return false
 var info := find_target()
 if info.is_empty():
  return false
 var guard = info["guard"]
 var stealth: bool = info["stealth"]
 var landed := false
 if stealth:
  landed = guard.receive_takedown()
 else:
  landed = guard.receive_melee_strike()
 if not landed:
  return false
 _cooldown = COOLDOWN
 attack_performed.emit(stealth)
 if stealth:
  attack_message.emit("REDUCCION SILENCIOSA")
 else:
  attack_message.emit("GOLPE CUERPO A CUERPO")
  # A physical scuffle can draw nearby guards, but is quieter than the pistol.
  if player.has_signal("weapon_fired"):
   player.weapon_fired.emit(player.global_position,3.4)
 _available = false
 _last_label = ""
 availability_changed.emit(false,"")
 return true

func find_target() -> Dictionary:
 if player == null or not is_instance_valid(player) or player.controls_locked or player.health <= 0:
  return {}
 var best_guard: CharacterBody3D = null
 var best_distance := INF
 for actor in get_tree().get_nodes_in_group("guards"):
  var guard := actor as CharacterBody3D
  if guard == null or guard.is_disabled:
   continue
  var horizontal := Vector2(player.global_position.x,player.global_position.z).distance_to(
   Vector2(guard.global_position.x,guard.global_position.z))
  if horizontal > RANGE or horizontal >= best_distance:
   continue
  # No melee through cover, walls or other guards.
  if not _unobstructed(guard):
   continue
  best_guard = guard
  best_distance = horizontal
 if best_guard == null:
  return {}
 return {"guard":best_guard,"stealth":_is_unaware_from_behind(best_guard)}

func _unobstructed(guard: CharacterBody3D) -> bool:
 var a: Vector3 = player.global_position + Vector3.UP*1.10
 var b: Vector3 = guard.global_position + Vector3.UP*1.10
 var query := PhysicsRayQueryParameters3D.create(a,b)
 query.exclude = [player.get_rid()]
 query.collision_mask = 1
 var hit := player.get_world_3d().direct_space_state.intersect_ray(query)
 return not hit.is_empty() and hit["collider"] == guard

func _is_unaware_from_behind(guard: CharacterBody3D) -> bool:
 # Investigation and searching are NOT safe opportunities for an instant takedown.
 # Likewise, the guard cannot have retained a substantial partial detection.
 if guard.state != guard.PATROL or guard.detection > 0.05:
  return false
 var toward_player: Vector3 = player.global_position-guard.global_position
 toward_player.y = 0.0
 if toward_player.length_squared() < 0.001:
  return false
 var forward := -guard.global_transform.basis.z
 forward.y = 0.0
 return forward.normalized().dot(toward_player.normalized()) < -0.45
