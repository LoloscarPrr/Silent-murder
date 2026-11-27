extends Node3D
## Deterministic ammo boundary checks; explicit tick avoids wall-clock races.
const MAIN = preload("res://scripts/main.gd")

func _ready() -> void:
 call_deferred("_run")

func _run() -> void:
 var game = MAIN.new()
 add_child(game)
 await get_tree().physics_frame
 var gun = game._player._weapon
 gun.set_physics_process(false)
 gun.request_reload()
 assert(not gun.is_reloading(), "Full magazine started reload")
 gun.magazine = 0
 gun.reserve = 3
 var shots: int = gun.shots_fired
 gun._fire_now()
 assert(gun.magazine == 0 and gun.shots_fired == shots, "Empty magazine fired or went negative")
 gun.request_reload()
 assert(gun.is_reloading(), "Partial reserve reload did not start")
 gun.set_trigger_held(true)
 gun._physics_process(.3)
 assert(gun.shots_fired == shots and gun.magazine == 0, "Fired during reload")
 var remaining: float = gun._reload_left
 gun.request_reload()
 assert(is_equal_approx(gun._reload_left, remaining), "Repeated reload restarted timer")
 gun._physics_process(2.0)
 assert(not gun.is_reloading() and gun.magazine == 3 and gun.reserve == 0, "Partial reserve did not conserve ammo")
 assert(gun.shots_fired == shots, "Reload completion fired in same tick")
 gun.set_trigger_held(false)
 gun.request_reload()
 assert(not gun.is_reloading(), "Empty reserve started reload")
 gun.magazine = 11
 gun.reserve = 8
 gun.request_reload()
 gun._physics_process(2.0)
 assert(gun.magazine == 12 and gun.reserve == 7, "Topping up consumed wrong reserve")
 print("AMMO_BOUNDARY_TEST_PASS")
 get_tree().quit(0)
