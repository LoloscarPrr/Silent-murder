extends Node3D
## Exercise the HUD's actual InputEvent dispatch, multi-owner fire, focus loss.
const MAIN = preload("res://scripts/main.gd")

func _ready() -> void:
 call_deferred("_run")

func _touch(hud, id: int, at: Vector2, pressed: bool) -> void:
 var event := InputEventScreenTouch.new()
 event.index = id
 event.position = at
 event.pressed = pressed
 hud._input(event)

func _drag(hud, id: int, at: Vector2, delta: Vector2) -> void:
 var event := InputEventScreenDrag.new()
 event.index = id
 event.position = at
 event.relative = delta
 hud._input(event)

func _run() -> void:
 var game = MAIN.new()
 add_child(game)
 await get_tree().process_frame
 await get_tree().physics_frame
 var player = game._player
 var hud = game._hud
 var gun = player._weapon
 for guard in game._guards:
  guard.set_physics_process(false)
 var size: Vector2 = get_viewport().get_visible_rect().size
 var move := Vector2(size.x*.13,size.y*.76)
 var look := Vector2(size.x*.60,size.y*.39)
 var fire: Vector2 = hud._buttons["fire"].get_global_rect().get_center()
 var sprint: Vector2 = hud._buttons["sprint"].get_global_rect().get_center()
 _touch(hud, 11, move, true)
 _drag(hud, 11, move+Vector2(45,-40), Vector2(45,-40))
 _touch(hud, 22, look, true)
 var yaw: float = player._desired_yaw
 _drag(hud, 22, look+Vector2(35,0), Vector2(35,0))
 _touch(hud, 33, fire, true)
 _touch(hud, 44, fire, true)
 _touch(hud, 55, sprint, true)
 assert(player.move_input.length() > .2 and hud._look_touch == 22, "Touch roles collided")
 assert(absf(player._desired_yaw-yaw) > .05 and gun._trigger_held and player.is_sprinting, "Look/fire/sprint not independent")
 _touch(hud, 33, fire, false)
 assert(gun._trigger_held, "Releasing first fire owner stopped second")
 _drag(hud, 44, look, look-fire)
 assert(gun._trigger_held and hud._look_touch == 22, "Dragging fire finger stole look")
 _touch(hud, 44, look, false)
 assert(not gun._trigger_held, "Fire stuck after last owner released")
 _touch(hud, 66, fire, true)
 assert(gun._trigger_held, "Second press failed")
 hud.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
 assert(hud._roles.is_empty() and hud._move_touch == -1 and hud._look_touch == -1, "Focus loss left touch roles")
 assert(player.move_input == Vector2.ZERO and not player.is_sprinting and not gun._trigger_held, "Focus loss left gameplay actions held")
 var shots: int = gun.shots_fired
 await get_tree().create_timer(.35).timeout
 assert(gun.shots_fired == shots, "Weapon fired after focus loss")
 _touch(hud, 66, fire, false)
 _drag(hud, 11, move, Vector2(60,0))
 assert(player.move_input == Vector2.ZERO and not gun._trigger_held, "Stale events restored actions")
 _touch(hud, 11, move, true)
 _drag(hud, 11, move+Vector2(40,0), Vector2(40,0))
 assert(player.move_input.length() > .2, "Movement did not recover after focus loss")
 _touch(hud, 11, move, false)
 assert(hud._roles.is_empty(), "Touch roles leaked after resume")
 print("TOUCH_LIFECYCLE_TEST_PASS")
 get_tree().quit(0)
