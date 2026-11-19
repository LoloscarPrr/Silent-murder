extends SceneTree
## Silent Killer real mission regression — Fase 11. Run headless Godot 4.3.
## Verifies main scene, exact real GLB rig, wrist-bound pistol, aim, walk,
## crouch, melee gesture, gunfire, three-finger input and guard/mission setup.

const SCENE := "res://scenes/main.tscn"
var _scene: Node3D

func _initialize() -> void:
    call_deferred("_run")

func fail(message: String, code: int = 2) -> void:
    push_error("CUERVO_FASE11_FAILED: " + message)
    quit(code)

func _run() -> void:
    var packed := load(SCENE) as PackedScene
    if packed == null:
        fail("Production main scene not found")
        return
    _scene = packed.instantiate()
    get_root().add_child(_scene)
    # Unlike the normal engine launch, a -s SceneTree test does not assign
    # current_scene automatically. The existing tracer uses that property.
    current_scene = _scene
    await process_frame
    await physics_frame
    await physics_frame

    var player = _scene._player
    if player == null or player.health != 100:
        fail("Existing mission player failed")
        return
    if _scene._mission == null or _scene._hud == null or _scene._guards.size() < 3:
        fail("Mission/guard/heads-up interface regression")
        return
    # Prevent autonomous enemies from interrupting deterministic animation QA.
    for guard in _scene._guards:
        guard.set_physics_process(false)
    var visual = player._visual
    if visual == null or not visual.has_method("get_visual_status"):
        fail("Player fell back to procedural mannequin")
        return
    var status: Dictionary = visual.get_visual_status()
    if not status["real_character_loaded"] or status["skeleton_bones"] != 53:
        fail("Real CC0 GLB with 53 bones not active: " + str(status))
        return
    if status["mesh_instances"] < 9:
        fail("El Cuervo original body/coat/face meshes not all loaded")
        return
    var grip: Node3D = visual.get_weapon_grip()
    var weapon = player._weapon
    if grip == null or weapon._muzzle == null:
        fail("Gun does not have a valid skeletal hand grip and muzzle")
        return
    if not weapon._muzzle.is_ancestor_of(grip):
        # Ancestor direction is grip->muzzle, NOT muzzle->grip.
        if not grip.is_ancestor_of(weapon._muzzle):
            fail("Gun muzzle is not under real right-hand anchor")
            return
    var initial_magazine: int = weapon.magazine

    # Walk through the actual existing player controller, not lab controls.
    var previous_pos: Vector3 = player.global_position
    player.move_input = Vector2(0.0, -0.85)
    await create_timer(0.34).timeout
    status = visual.get_visual_status()
    if status["state"] != "walk" or not status["walk_clip_active"]:
        fail("Real walk clip did not activate from player joystick")
        return
    if player.global_position.distance_to(previous_pos) < 0.05:
        fail("Player did not move with original CharacterBody3D")
        return
    player.move_input = Vector2.ZERO
    await create_timer(0.13).timeout
    if visual.get_visual_status()["state"] != "idle":
        fail("Player did not return to idle after joystick release")
        return

    # Existing aiming action must select the real GLB Action.
    player.toggle_aim()
    await create_timer(1.16).timeout
    status = visual.get_visual_status()
    if not player.is_aiming or status["state"] != "aim":
        fail("Aim button did not drive actual El Cuervo rig")
        return
    var skeleton: Skeleton3D = visual._skeleton
    var lh := skeleton.find_bone("hand_l")
    var rh := skeleton.find_bone("hand_r")
    if lh < 0 or rh < 0:
        fail("Model lost original animated hands")
        return
    skeleton.force_update_all_bone_transforms()
    var distance: float = skeleton.get_bone_global_pose(lh).origin.distance_to(
        skeleton.get_bone_global_pose(rh).origin)
    if distance < .04 or distance > .25:
        fail("Aiming pose hands are separated: %.3f m" % distance)
        return

    # Existing weapon controller still consumes ammunition and fires from the
    # actual muzzle using the same safe camera-point->muzzle ray algorithm.
    weapon.set_trigger_held(true)
    await create_timer(0.28).timeout
    weapon.set_trigger_held(false)
    if weapon.shots_fired < 1 or weapon.magazine >= initial_magazine:
        fail("Weapon firing or ammo broke with new 3D character")
        return
    player.toggle_aim()

    # Existing crouch affects collision and visible mesh together; for now
    # this is temporary scaling, not a new skeletal crouch animation.
    player.toggle_crouch()
    await create_timer(0.24).timeout
    if not player.is_crouching or visual.scale.y > 0.95:
        fail("Crouching stopped affecting visible character")
        return
    player.toggle_crouch()

    # Existing contextual melee controller can still request the visual
    # short lunge; no new takedown animation claim.
    player._on_melee_animation(false)
    if visual._melee_left <= 0.0:
        fail("Melee visual callback lost")
        return

    # Direct multi-finger interactions through original HUD: one finger move,
    # one look and one sprint. None may steal the other finger's role.
    var ui = _scene._hud
    var size: Vector2 = get_root().size
    ui._press(11, Vector2(size.x * .13, size.y * .75))
    ui._drag(11, Vector2(size.x * .13 + 45, size.y * .75 - 50), Vector2(45,-50))
    ui._press(22, Vector2(size.x * .60, size.y * .42))
    ui._press(33, Vector2(size.x * .90, size.y * .84))
    print("FASE11_TOUCH_DEBUG move=", player.move_input,
          " look_touch=", ui._look_touch, " sprint=", player.is_sprinting,
          " crouch=", player.is_crouching, " aim=", player.is_aiming,
          " roles=", ui._roles, " mission=", ui._mission_state,
          " rects=", ui._buttons["sprint"].get_global_rect())
    if player.move_input.length() <= .2 or ui._look_touch != 22 or not player.is_sprinting:
        fail("Three-finger joystick/look/sprint broke after model integration")
        return
    ui._release(33)
    ui._release(22)
    ui._release(11)
    if not ui._roles.is_empty() or player.move_input.length() > .01:
        fail("Multi-finger roles left stuck")
        return

    print("CUERVO_FASE11_PASS: real CC0 rig=53 active in mission; animated walk+aim; wrist pistol; shots=", weapon.shots_fired)
    print("CUERVO_FASE11_MISSION_PASS: patrols=", _scene._guards.size(), " health=", player.health, " controls=3 fingers, crouch, melee")
    print("CUERVO_FASE11_AIM_GRIP_M=", distance)
    _scene.queue_free()
    quit(0)
