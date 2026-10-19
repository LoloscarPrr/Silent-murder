extends Node3D
## CI test: real physics hits, magazine / reserve, reload, and multitouch fire.

const PLAYER = preload("res://scripts/player_controller.gd")
const TARGET = preload("res://scripts/training_target.gd")
const HUD = preload("res://scripts/mobile_controls.gd")

var operative
var target
var controls

func _ready() -> void:
 var floor_body := StaticBody3D.new()
 floor_body.position.y = -.10
 var floor_collider := CollisionShape3D.new()
 var shape := BoxShape3D.new()
 shape.size = Vector3(80,.20,80)
 floor_collider.shape = shape
 floor_body.add_child(floor_collider)
 add_child(floor_body)

 operative = PLAYER.new()
 operative.position = Vector3(0,.05,0)
 add_child(operative)

 controls = HUD.new()
 controls.operative = operative
 add_child(controls)

 call_deferred("_test")

func _test() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame

 var camera: Camera3D = operative._camera
 var center := camera.get_viewport().get_visible_rect().size * .5
 var origin := camera.project_ray_origin(center)
 var direction := camera.project_ray_normal(center).normalized()

 target = TARGET.new()
 target.position = origin + direction * 7.0
 add_child(target)
 await get_tree().physics_frame

 var weapon = operative._weapon
 assert(weapon.magazine == 12 and weapon.reserve == 48,"Initial ammo mismatch")
 weapon.set_trigger_held(true)
 await get_tree().create_timer(.72).timeout
 weapon.set_trigger_held(false)
 assert(weapon.shots_fired >= 3,"Holding fire did not shoot repeatedly")
 assert(weapon.hits >= 3,"Center reticle did not hit practice target")
 assert(target.is_disabled,"Training target did not deactivate after three hits")
 assert(weapon.magazine < 12,"Magazine was not consumed")
 var before_reload: int = weapon.magazine
 weapon.request_reload()
 assert(weapon.is_reloading(),"Reload did not start")
 await get_tree().create_timer(1.45).timeout
 assert(not weapon.is_reloading(),"Reload did not finish")
 assert(weapon.magazine == 12,"Reload did not restore magazine")
 assert(weapon.reserve == 48 - (12-before_reload),"Reserve ammo incorrect")

 # Input multitouch must not drop independent touch roles during firing.
 var s: Vector2 = get_viewport().get_visible_rect().size
 controls._press(11,Vector2(s.x*.13,s.y*.75))
 controls._drag(11,Vector2(s.x*.13,s.y*.75)+Vector2(40,-30),Vector2(40,-30))
 controls._press(22,Vector2(s.x*.60,s.y*.40))
 controls._press(33,Vector2(s.x*.79,s.y*.41))
 assert(operative.move_input.length() > .3,"Firing canceled movement")
 assert(controls._look_touch == 22,"Firing stole camera finger")
 assert(weapon._trigger_held,"Firing finger was not registered")
 await get_tree().create_timer(.27).timeout
 controls._release(33)
 assert(not weapon._trigger_held,"Firing got stuck after lifting finger")
 assert(operative.move_input.length() > .3,"Fire release erased joystick")
 controls._release(22)
 controls._release(11)
 assert(controls._roles.is_empty(),"Touch roles were not released")
 print("COMBAT_TEST_PASS: training target / 12-round pistol / reload / multitouch")
 get_tree().quit(0)
