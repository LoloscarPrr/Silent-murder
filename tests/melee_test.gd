extends Node3D
## Test melee hit registration, rear takedown, wall blocking and multitouch.

const MAIN = preload("res://scripts/main.gd")
var game

func _ready() -> void:
 game = MAIN.new()
 add_child(game)
 call_deferred("_exercise")

func _exercise() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 var player = game._player
 var hud = game._hud
 var melee = player._melee
 assert(game._guards.size() >= 2,"Need guards from existing mission")
 for guard in game._guards:
  guard.set_physics_process(false)

 var rear = game._guards[0]
 rear.rotation.y = 0.0
 player.global_position = rear.global_position + Vector3(0,0,1.40)
 player.velocity = Vector3.ZERO
 await get_tree().physics_frame
 var info: Dictionary = melee.find_target()
 assert(not info.is_empty(),"Rear guard not selectable in melee range")
 assert(info["guard"] == rear,"Wrong rear target selected")
 assert(info["stealth"],"Rear of unaware guard should allow silent takedown")
 melee._cooldown = 0.0
 melee._physics_process(.16)
 assert(hud._buttons["melee"].visible,"Melee context button absent behind guard")
 assert(hud._buttons["melee"].text == "REDUCIR","Stealth context should say REDUCIR")
 var ammo_before: int = player._weapon.magazine
 var removed_before: int = game._guards_disabled

 # Separate fingers can hold the virtual joystick and tap stealth action.
 var size: Vector2 = get_viewport().get_visible_rect().size
 hud._press(10,Vector2(size.x*.13,size.y*.76))
 var take_down: Vector2 = hud._buttons["melee"].get_global_rect().get_center()
 hud._press(22,take_down)
 hud._release(22)
 assert(rear.is_disabled,"Stealth takedown failed")
 assert(game._guards_disabled == removed_before+1,"Melee did not update guard HUD counter")
 assert(player._weapon.magazine == ammo_before,"Melee spent bullets")
 assert(hud._move_touch == 10,"Melee stole joystick finger")
 hud._release(10)
 assert(hud._roles.is_empty(),"Melee left dangling fingers")
 assert(not melee.try_attack(),"Immediate follow-up should be on cooldown")

 # Frontal attacks take three separate actions; never silently one-shot an aware guard.
 var frontal = game._guards[1]
 frontal.rotation.y = 0.0
 player.global_position = frontal.global_position + Vector3(0,0,-1.4)
 player.velocity = Vector3.ZERO
 await get_tree().physics_frame
 info = melee.find_target()
 assert(not info.is_empty() and info["guard"] == frontal,"Frontal guard not available")
 assert(not info["stealth"],"Frontal target wrongly permits silent takedown")
 melee._cooldown = 0.0
 melee._physics_process(.16)
 assert(hud._buttons["melee"].text == "GOLPEAR","Frontal control should say GOLPEAR")
 assert(player.perform_melee(),"First frontal strike rejected")
 assert(frontal.health == 2 and not frontal.is_disabled,"Frontal strike should deal one HP")
 assert(frontal.state == frontal.ALERT,"Frontal strike should alert guard")
 assert(not player.perform_melee(),"Melee cooldown ignored")

 # Cover blocks melee even at very close range.
 var barrier := StaticBody3D.new()
 barrier.position = (player.global_position+frontal.global_position)*.5 + Vector3(0,.90,0)
 var collision := CollisionShape3D.new()
 var box := BoxShape3D.new()
 box.size = Vector3(2.0,2.0,.17)
 collision.shape = box
 barrier.add_child(collision)
 add_child(barrier)
 await get_tree().physics_frame
 assert(melee.find_target().is_empty(),"Attack may not pass through walls")
 barrier.queue_free()
 await get_tree().physics_frame
 await get_tree().physics_frame

 melee._cooldown = 0.0
 assert(player.perform_melee(),"Second frontal strike rejected")
 assert(frontal.health == 1 and not frontal.is_disabled,"Second melee damage incorrect")
 melee._cooldown = 0.0
 assert(player.perform_melee(),"Third frontal strike rejected")
 assert(frontal.is_disabled,"Guard not disabled after three melee hits")
 assert(game._guards_disabled == removed_before+2,"Guard kill count did not increase correctly")
 assert(not player.perform_melee(),"Cannot attack an already disabled guard")

 player.controls_locked = true
 assert(not player.perform_melee(),"Melee action possible during mission result")
 print("MELEE_TEST_PASS: behind stealth / frontal blows / cover / cooldown / multitouch / guard counter")
 get_tree().quit(0)
