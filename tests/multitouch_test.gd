extends Node3D
## Offline deterministic five-finger input test. Never included in main gameplay.

const PLAYER = preload("res://scripts/player_controller.gd")
const HUD = preload("res://scripts/mobile_controls.gd")

var operative
var controls

func _ready() -> void:
 operative = PLAYER.new()
 add_child(operative)
 controls = HUD.new()
 controls.operative = operative
 add_child(controls)
 call_deferred("_run_test")

func _run_test() -> void:
 await get_tree().process_frame
 var s: Vector2 = get_viewport().get_visible_rect().size
 var move_point := Vector2(s.x*.13,s.y*.76)
 var look_point := Vector2(s.x*.61,s.y*.39)
 var sprint_point := Vector2(s.x*.90,s.y*.84)
 var aim_point := Vector2(s.x*.90,s.y*.57)
 var crouch_point := Vector2(s.x*.79,s.y*.72)

 # Three fingers at once: movement (11), camera (22), held sprint (33).
 controls._press(11,move_point)
 controls._drag(11,move_point+Vector2(52,-52),Vector2(52,-52))
 assert(operative.move_input.length() > .5,"move finger not registered")

 controls._press(22,look_point)
 var initial_yaw: float = operative._desired_yaw
 controls._drag(22,look_point+Vector2(42,0),Vector2(42,0))
 assert(absf(operative._desired_yaw-initial_yaw) > .05,"look finger not independent")

 controls._press(33,sprint_point)
 assert(operative.is_sprinting,"sprint button not held")
 assert(operative.move_input.length() > .5,"sprint interfered with movement")
 assert(controls._look_touch == 22,"sprint interfered with look")

 # Finger four can toggle aim while the other three stay attached.
 controls._press(44,aim_point)
 assert(operative.is_aiming,"aim button did not activate")
 assert(operative.is_sprinting,"holding sprint lost when aiming")
 assert(controls._look_touch == 22,"aim displaced the look finger")
 controls._release(44)

 # Looking can stop without affecting the movement and running fingers.
 controls._release(22)
 assert(controls._look_touch == -1,"camera did not release")
 assert(operative.move_input.length() > .5,"camera release cleared move")
 assert(operative.is_sprinting,"camera release cleared sprint")

 controls._release(33)
 assert(not operative.is_sprinting,"sprint stuck after lifting finger")
 assert(operative.move_input.length() > .5,"sprint release cleared move")

 controls._press(55,crouch_point)
 assert(operative.is_crouching,"crouch did not trigger")
 controls._release(55)

 controls._release(11)
 assert(operative.move_input.length() < .01,"joystick stuck after release")
 assert(controls._roles.is_empty(),"dangling touch roles")

 controls._press(66,move_point)
 controls._press(77,sprint_point)
 controls._reset_touches()
 assert(controls._roles.is_empty(),"focus loss did not reset touches")
 assert(not operative.is_sprinting,"focus loss did not reset sprint")
 assert(operative.move_input == Vector2.ZERO,"focus loss did not reset joystick")

 print("MULTITOUCH_TEST_PASS: move + look + run + aim + crouch, independent ids")
 get_tree().quit(0)
