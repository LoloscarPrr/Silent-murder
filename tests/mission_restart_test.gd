extends SceneTree
## Real scene reload, not just the existence of a retry button.
const SCENE := "res://scenes/main.tscn"

func _initialize() -> void:
 call_deferred("_run")

func _check_fresh(game) -> bool:
 if game == null:
  return false
 var p = game._player
 var m = game._mission
 var h = game._hud
 if p.health != 100 or p.controls_locked or p._weapon.magazine != 12 or p._weapon.reserve != 48:
  return false
 if m.state != m.INFILTRATE or m.intel_collected or m._extraction_marker.visible:
  return false
 if h._mission_state != "" or h._result_panel.visible or not h._roles.is_empty():
  return false
 if game._guards.size() != 3 or game._guards_disabled != 0 or game._targets_disabled != 0:
  return false
 for guard in game._guards:
  if guard.is_disabled or not guard.is_physics_processing():
   return false
 return true

func _fail(message: String) -> void:
 push_error("MISSION_RESTART_FAILED: " + message)
 quit(2)

func _retry(game) -> void:
 var h = game._hud
 var e := InputEventScreenTouch.new()
 e.index = 77
 e.position = h._buttons["restart"].get_global_rect().get_center()
 e.pressed = true
 h._input(e)

func _run() -> void:
 var packed := load(SCENE) as PackedScene
 var initial := packed.instantiate()
 root.add_child(initial)
 current_scene = initial
 await process_frame
 await physics_frame
 var game = current_scene
 if not _check_fresh(game):
  _fail("Initial mission invalid")
  return
 for guard in game._guards:
  guard.set_physics_process(false)
 var p = game._player
 p._weapon.magazine = 2
 p._weapon.reserve = 5
 p.receive_enemy_damage(250)
 if game._mission.state != game._mission.FAILED:
  _fail("Defeat state missing")
  return
 var old_id: int = game.get_instance_id()
 _retry(game)
 for i in range(20):
  await process_frame
  if current_scene != null and current_scene.get_instance_id() != old_id:
   break
 await physics_frame
 game = current_scene
 if game == null or game.get_instance_id() == old_id or not _check_fresh(game):
  _fail("Defeat retry did not reset real mission")
  return
 for guard in game._guards:
  guard.set_physics_process(false)
 p = game._player
 var m = game._mission
 p.global_position = m.INTEL_POSITION + Vector3(0,.15,0)
 if not m.interact():
  _fail("Dossier interaction failed")
  return
 p.global_position = m.EXTRACTION_POSITION + Vector3(0,.15,0)
 if not m.interact() or m.state != m.SUCCESS:
  _fail("Extraction interaction failed")
  return
 old_id = game.get_instance_id()
 _retry(game)
 for i in range(20):
  await process_frame
  if current_scene != null and current_scene.get_instance_id() != old_id:
   break
 await physics_frame
 game = current_scene
 if game == null or game.get_instance_id() == old_id or not _check_fresh(game):
  _fail("Victory retry did not reset real mission")
  return
 print("MISSION_RESTART_TEST_PASS")
 quit(0)
