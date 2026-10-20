extends Node3D
## Alpha 0.5.3: camera selects aim; muzzle determines whether cover blocks a shot.

const PLAYER = preload("res://scripts/player_controller.gd")
const TARGET = preload("res://scripts/training_target.gd")
var player
var target

func _ready() -> void:
 var floor := StaticBody3D.new()
 floor.position.y = -.10
 var col := CollisionShape3D.new()
 var shape := BoxShape3D.new()
 shape.size = Vector3(80,.20,80)
 col.shape = shape
 floor.add_child(col)
 add_child(floor)
 player = PLAYER.new()
 player.position = Vector3(0,.05,0)
 add_child(player)
 call_deferred("_check")

func _check() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 var camera: Camera3D = player._camera
 var weapon = player._weapon
 var center: Vector2 = camera.get_viewport().get_visible_rect().size*.5
 var camera_origin: Vector3 = camera.project_ray_origin(center)
 var camera_forward: Vector3 = camera.project_ray_normal(center).normalized()
 var aim_point: Vector3 = camera_origin+camera_forward*7.0
 target = TARGET.new()
 target.position = aim_point
 add_child(target)
 await get_tree().physics_frame
 var before: Dictionary = weapon.resolve_shot_path()
 assert(not before.is_empty(),"Unable to resolve weapon aim")
 assert(before["impact"].get("collider") == target,"Unblocked gun cannot hit target")

 # A small solid slab intersects the muzzle trajectory at close range.
 # We position it away from the camera ray so the reticle still sees the target.
 var muzzle: Vector3 = weapon._muzzle.global_position
 var barrier := StaticBody3D.new()
 var obstacle := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = Vector3(.42,.42,.42)
 obstacle.shape = box
 barrier.add_child(obstacle)
 barrier.position = muzzle.lerp(aim_point,.18)
 add_child(barrier)
 await get_tree().physics_frame
 var after: Dictionary = weapon.resolve_shot_path()
 assert(not after.is_empty(),"Unable to resolve aim after placing cover")
 assert(after["camera_hit"].get("collider") == target,"Cover test invalid: slab hides reticle as well")
 assert(after["impact"].get("collider") == barrier,"Muzzle shot passed through near cover")

 var hp_before: int = target.health
 weapon._fire_now()
 assert(target.health == hp_before,"Target lost health through muzzle cover")
 print("SHOT_COVER_TEST_PASS: reticle sees target, muzzle blocked, no damage through cover")
 get_tree().quit(0)
