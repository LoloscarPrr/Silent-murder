extends Node3D
## Alpha 0.5.1 — regression for the screenshot bug: failed mission showing 100 HP.

const MAIN = preload("res://scripts/main.gd")
var game
var defeats := 0

func _ready() -> void:
 game = MAIN.new()
 add_child(game)
 call_deferred("_run_checks")

func _run_checks() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 var player = game._player
 var hud = game._hud
 var mission = game._mission
 var starting_position: Vector3 = player.global_position
 player.player_defeated.connect(func() -> void: defeats += 1)
 assert(player.health == 100,"Test must begin with full HP")
 assert(mission.state == mission.INFILTRATE,"Test must begin before dossier")

 player.receive_enemy_damage(250)
 assert(player.health == 0,"Health should remain zero after terminal damage")
 assert(player.controls_locked,"Player movement must be locked after defeat")
 assert(player.global_position.is_equal_approx(starting_position),"Player teleported after defeat")
 assert(defeats == 1,"Defeat must be emitted exactly once")
 assert(mission.state == mission.FAILED,"Mission did not transition to failure")
 assert(hud._mission_state == "failure","Failure overlay missing")
 assert(hud._health_label.text == "VIDA 0 / 100","HUD incorrectly shows full HP after defeat")
 assert(hud._result_panel.visible,"Result card was not displayed")
 assert(hud._buttons["restart"].visible,"Retry action is hidden")
 assert(hud._result_detail.text.contains("VIDA: 0"),"Card does not report the final HP")

 # Check that the retry surface is genuinely inside the visible result card.
 var panel_bounds: Rect2 = hud._result_panel.get_global_rect()
 var retry_bounds: Rect2 = hud._buttons["restart"].get_global_rect()
 assert(panel_bounds.has_point(retry_bounds.get_center()),"Retry button outside the result card")
 assert(hud._find_button(retry_bounds.get_center()) == "restart","Retry cannot receive touch")

 # Terminal state must not be overwritten by more shots.
 player._damage_grace = 0.0
 player.receive_enemy_damage(18)
 assert(player.health == 0,"Subsequent damage modified fatal HP")
 assert(defeats == 1,"Additional shots emitted another defeat")
 assert(mission.state == mission.FAILED,"Further shots changed finished mission")

 for guard in game._guards:
  assert(not guard.is_physics_processing(),"Guard kept attacking after game over")

 print("MISSION_FAILURE_TEST_PASS: 0 HP / no respawn / clear panel / accessible retry")
 get_tree().quit(0)
