extends Node3D
## Alpha 0.5 regression: mission lifecycle with genuine scene integration.
const MAIN = preload("res://scripts/main.gd")
const MISSION = preload("res://scripts/mission_manager.gd")

var game
var player
var mission
var hud

func _ready() -> void:
 game = MAIN.new()
 add_child(game)
 call_deferred("_test_contract")

func _test_contract() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 player = game._player
 mission = game._mission
 hud = game._hud
 assert(player != null and mission != null and hud != null,"Mission not wired into main")
 assert(game._guards_total == 3,"Existing guards lost")
 assert(game._targets_total == 4,"Training props lost")
 assert(mission.state == mission.INFILTRATE,"Mission should start at INFILTRATE")
 assert(not mission.intel_collected,"Dossier must not be owned at spawn")
 assert(not mission._extraction_marker.visible,"Extraction must be inactive until dossier")

 # Exploit prevention: extraction is not permitted without obtaining the intel.
 player.global_position = mission.EXTRACTION_POSITION
 await get_tree().physics_frame
 assert(not mission.interact(),"Extraction allowed before retrieving dossier")
 assert(mission.state == mission.INFILTRATE,"Objective state changed without dossier")

 # Long distance cannot hack the terminal remotely.
 player.global_position = Vector3(0,.15,8)
 await get_tree().physics_frame
 assert(not mission.interact(),"Remote dossier pickup must be impossible")

 # Objective location unlocks the interaction button and dossier.
 player.global_position = mission.INTEL_POSITION + Vector3(0,.15,0)
 await get_tree().physics_frame
 mission._process(.2)
 assert(hud._buttons["interact"].visible,"Interaction button absent near dossier")
 var pickup_point: Vector2 = hud._buttons["interact"].get_global_rect().get_center()
 hud._press(50,pickup_point)
 hud._release(50)
 assert(mission.intel_collected,"Touching RECUPERAR did not retrieve dossier")
 assert(mission.intel_collected,"Dossier flag missing")
 assert(mission.state == mission.EXTRACT,"Mission did not advance to extraction")
 assert(mission._extraction_marker.visible,"Extraction indicator did not activate")
 assert(not mission._intel_marker.visible,"Intel console should no longer signal pickup")

 # Extract at the mission marker; ending freezes combat and shows restart UI.
 assert(not mission.interact(),"Extraction should still require proximity")
 player.global_position = mission.EXTRACTION_POSITION + Vector3(0,.15,0)
 await get_tree().physics_frame
 mission._process(.2)
 assert(hud._buttons["interact"].visible,"Extraction button absent at beacon")
 var extract_point: Vector2 = hud._buttons["interact"].get_global_rect().get_center()
 hud._press(51,extract_point)
 assert(mission.state == mission.SUCCESS,"EXTRAER button did not complete mission")
 hud._release(51)
 assert(mission.state == mission.SUCCESS,"Mission did not complete")
 assert(player.controls_locked,"Player remains controllable after success")
 assert(hud._mission_state == "success","Mission result screen missing")
 assert(hud._result_panel.visible,"Victory card missing")
 assert(hud._result_detail.text.contains("COMPLETADO"),"Victory result details incomplete")
 assert(hud._buttons["restart"].visible,"Restart action not available")
 var result_card: Rect2 = hud._result_panel.get_global_rect()
 var restart_center: Vector2 = hud._buttons["restart"].get_global_rect().get_center()
 assert(result_card.has_point(restart_center),"New game button outside result card")
 assert(hud._find_button(restart_center) == "restart","New game button does not accept input")
 for guard in game._guards:
  assert(not guard.is_physics_processing(),"Combat guard stayed active after victory")
 assert(not mission.interact(),"Mission may not complete twice")

 # Separate isolated manager instance validates defeat branch.
 var failed_run = MISSION.new()
 failed_run.player = player
 add_child(failed_run)
 failed_run.on_player_defeated()
 assert(failed_run.state == failed_run.FAILED,"Player death did not fail mission")
 assert(failed_run._extraction_marker.visible == false,"Failed run unexpectedly unlocked extraction")

 print("MISSION_TEST_PASS: no early extraction / pickup / extraction / success / UI retry / defeat")
 get_tree().quit(0)
