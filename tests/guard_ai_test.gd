extends Node3D
## CI smoke test for guard perception, hearing, state, damage and elimination.
## Headless-friendly: assertions are performed on physics frames.

const PLAYER = preload("res://scripts/player_controller.gd")
const GUARD = preload("res://scripts/guard_ai.gd")

var player
var guard

func _ready() -> void:
 _floor()
 player = PLAYER.new()
 player.position = Vector3(0,.1,-5)
 add_child(player)
 guard = GUARD.new()
 guard.player = player
 guard.position = Vector3(0,.1,0)
 guard.waypoints = [Vector3(0,.1,0),Vector3(0,.1,1.5)]
 add_child(guard)
 call_deferred("_exercise")

func _floor() -> void:
 var body := StaticBody3D.new()
 body.position = Vector3(0,-.1,0)
 var collision := CollisionShape3D.new()
 var shape := BoxShape3D.new()
 shape.size = Vector3(40,.2,40)
 collision.shape = shape
 body.add_child(collision)
 add_child(body)

func _exercise() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 assert(guard.can_see_player(),"Guard failed to see exposed player within forward FOV")
 var wall := StaticBody3D.new()
 var c := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = Vector3(2.6,3.0,.3)
 c.shape = box
 wall.add_child(c)
 wall.position = Vector3(0,1.5,-2.5)
 add_child(wall)
 await get_tree().physics_frame
 assert(not guard.can_see_player(),"Wall failed to block guard visibility")
 guard.hear_noise(Vector3(0,0,-3),7.0)
 assert(guard.state == guard.INVESTIGATE,"Nearby noise did not start investigation")
 # The player is behind cover: no new alert based on impossible LOS.
 await get_tree().create_timer(.25).timeout
 assert(guard.state != guard.ALERT,"Guard saw player through cover")
 wall.queue_free()
 await get_tree().physics_frame
 await get_tree().physics_frame
 guard.global_position = Vector3(0,.1,0)
 guard.rotation.y = 0.0
 assert(guard.can_see_player(),"Guard could not reacquire player after cover removed")
 guard._switch(guard.ALERT)
 guard._fire_timer = 0.0
 var hp_before: int = player.health
 await get_tree().create_timer(.32).timeout
 assert(guard.shots_fired > 0,"Alerted guard did not shoot")
 assert(player.health < hp_before,"Guard shot did not damage player")

 var hp_after: int = player.health
 player._damage_grace = 0.0
 player.receive_enemy_damage(7)
 assert(player.health == hp_after - 7,"Player damage accounting incorrect")
 player._damage_grace = 0.0
 player.receive_enemy_damage(150)
 assert(player.health == player.MAX_HEALTH,"Player did not respawn at full health")
 assert(guard.state == guard.ALERT,"Test setup changed guard unexpectedly")
 guard.reset_after_player_defeat()
 assert(guard.state == guard.PATROL,"Guard remained alerted after defeat reset")

 var hit_point := guard.global_position + Vector3.UP
 for i in range(3):
  assert(guard.receive_shot(hit_point,Vector3.BACK),"Guard ignored a valid hit")
 assert(guard.is_disabled,"Guard not disabled after three hits")
 assert(guard.collision_layer == 0,"Disabled guard still blocks gunfire")
 assert(not guard.receive_shot(hit_point,Vector3.BACK),"Disabled guard accepted extra hit")
 print("GUARD_AI_TEST_PASS: LOS / cover / hearing / alert / enemy damage / respawn / disable")
 get_tree().quit(0)
