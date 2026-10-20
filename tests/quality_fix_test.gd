extends Node3D
## Alpha 0.5.3: guard awareness, permanent melee control, alert HUD and timed toast.

const MAIN = preload("res://scripts/main.gd")
var game

func _ready() -> void:
 game = MAIN.new()
 add_child(game)
 call_deferred("_check")

func _check() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 var player = game._player
 var guard = game._guards[0]
 var melee = player._melee
 var hud = game._hud
 var mission = game._mission
 guard.set_physics_process(false)
 player.global_position = guard.global_position+Vector3(0.0,0.0,1.40)
 guard.rotation.y = 0.0
 await get_tree().physics_frame

 guard._switch(guard.PATROL)
 guard.detection = 0.0
 var info: Dictionary = melee.find_target()
 assert(not info.is_empty() and info["stealth"],"Unaware guard cannot be silently reduced")

 guard._switch(guard.INVESTIGATE)
 info = melee.find_target()
 assert(not info.is_empty() and not info["stealth"],"Investigating guard can be silently reduced")
 guard._switch(guard.SEARCH)
 info = melee.find_target()
 assert(not info.is_empty() and not info["stealth"],"Searching guard can be silently reduced")
 guard._switch(guard.ALERT)
 info = melee.find_target()
 assert(not info.is_empty() and not info["stealth"],"Alerted guard can be silently reduced")
 guard._switch(guard.PATROL)
 guard.detection = .25
 info = melee.find_target()
 assert(not info.is_empty() and not info["stealth"],"Partially aware patrol allows an instant takedown")
 guard.detection = 0.0

 var button: Button = hud._buttons["melee"]
 hud.set_melee_available(false,"")
 assert(button.visible,"Melee button must stay visible, but dimmed")
 assert(button.disabled,"Melee button should be disabled out of range")
 assert(hud._find_button(button.get_global_rect().get_center()) != "melee","Disabled melee control consumed a tap")
 hud.set_melee_available(true,"REDUCIR")
 assert(button.visible and not button.disabled,"Melee button did not reactivate in range")
 assert(button.text == "REDUCIR","Correct contextual takedown label missing")
 assert(hud._find_button(button.get_global_rect().get_center()) == "melee","Active melee button cannot be pressed")

 hud.set_alert_status("ALERTA")
 assert(hud._alert_label.text == "ALARMA: ALERTA","Guard alarm label is not independent")
 mission.state = mission.EXTRACT
 mission.intel_collected = true
 mission._update_ui()
 assert(hud._alert_label.text == "ALARMA: ALERTA","Mission progress overwrote guard alarm")
 assert(hud._mission_label.text.contains("EXTRACCION"),"Extraction objective not shown")

 var fixed_title: String = hud._status.text
 hud._set_status("GOLPE CUERPO A CUERPO")
 assert(hud._status.text == fixed_title,"Action replaced the permanent game title")
 assert(hud._event_label.visible,"Temporary feedback is missing")
 hud._process(2.0)
 assert(not hud._event_label.visible,"Old action feedback did not expire")

 print("QUALITY_FIX_TEST_PASS: aware takedowns blocked / stable melee / alarm separate / toast expiry")
 get_tree().quit(0)
