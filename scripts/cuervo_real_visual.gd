extends Node3D
## SILENT KILLER — EL CUERVO FASE 11 / PERSONAJE 3D EN MISIÓN.
##
## Adapter for player_controller.gd (unchanged movement/mission/multitouch API).
## Replaces only the placeholder geometric visual on the FEATURE branch.
## Real CC0 MakeHuman mesh + Blender-authored GLB with 53 bones.
## Prototype walk and aim clips. No crouch/sprint/melee animation claims yet.
##
## The legacy visual may be restored without uninstalling/restarting the game
## if this asset fails: player_controller.gd checks is_ready_for_gameplay().
const MODEL_PATH := "res://character_assets/el_cuervo/fase9_animaciones/El_Cuervo_Fase9_Walk_Aim_REVISION.glb"
const WALK := "Cuervo_Walk_InPlace"
const AIM := "Cuervo_Aim_Raise"

var elbow_right: Node3D # Compatibility with legacy weapon_controller contract.
var _character: Node3D
var _player: AnimationPlayer
var _skeleton: Skeleton3D
var _right_hand: Node3D
var _hand_index := -1
var _valid := false
var _state := ""
var _melee_left := 0.0
var _melee_stealth := false
var _aiming := false
var _crouch_alpha := 0.0
var _running := false
var _movement := 0.0
var _last_error := ""
var _skin_mesh_count := 0

func _ready() -> void:
    name = "ElCuervo_Real3D_Fase11"
    var resource := load(MODEL_PATH)
    if resource == null or not resource is PackedScene:
        _last_error = "GLB animado no importado"
        push_warning("El Cuervo: " + _last_error)
        return
    _character = (resource as PackedScene).instantiate() as Node3D
    if _character == null:
        _last_error = "GLB sin nodo raíz 3D"
        return
    _character.name = "ElCuervo_Rigged_53Bones"
    # Blender's front camera sees the original model from -Y; the exported
    # glTF faces +Z. Godot gameplay forward is -Z. Turn the visual only.
    _character.rotation.y = PI
    add_child(_character)
    _inspect(_character)
    if _skeleton == null or _player == null or _skeleton.get_bone_count() != 53:
        _last_error = "Esqueleto o AnimationPlayer incorrectos"
        push_warning("El Cuervo: " + _last_error)
        return
    if not _player.has_animation(WALK) or not _player.has_animation(AIM):
        _last_error = "Faltan animaciones Walk/Aim"
        push_warning("El Cuervo: " + _last_error)
        return
    _hand_index = _skeleton.find_bone("hand_r")
    if _hand_index < 0:
        _last_error = "No se encuentra hand_r para el arma"
        push_warning("El Cuervo: " + _last_error)
        return
    _player.get_animation(WALK).loop_mode = Animation.LOOP_LINEAR
    _player.get_animation(AIM).loop_mode = Animation.LOOP_NONE
    _player.animation_finished.connect(_on_animation_finished)
    _right_hand = Node3D.new()
    _right_hand.name = "WeaponGrip_RightHand_RealRig"
    add_child(_right_hand)
    elbow_right = _right_hand
    _valid = true
    _set_clip("idle")
    _update_weapon_grip()

func _inspect(node: Node) -> void:
    if node is AnimationPlayer and _player == null:
        _player = node as AnimationPlayer
    elif node is Skeleton3D and _skeleton == null:
        _skeleton = node as Skeleton3D
    elif node is MeshInstance3D:
        _skin_mesh_count += 1
    for child in node.get_children():
        _inspect(child)

func is_ready_for_gameplay() -> bool:
    return _valid

func get_weapon_grip() -> Node3D:
    return _right_hand

func get_visual_status() -> Dictionary:
    return {
        "real_character_loaded": _valid,
        "asset": MODEL_PATH,
        "skeleton_bones": _skeleton.get_bone_count() if _skeleton else 0,
        "mesh_instances": _skin_mesh_count,
        "state": _state,
        "aim_clip_active": _player != null and _player.current_animation == AIM,
        "walk_clip_active": _player != null and _player.current_animation == WALK,
        "gun_anchor": _right_hand != null,
        "fallback_reason": _last_error,
        "notes": "Walk/Aim skeletal; crouch, sprint and melee gestures temporary",
    }

func animate_pose(delta: float, movement: float, strafing: float, crouched: bool, aiming: bool, running: bool) -> void:
    if not _valid:
        return
    _melee_left = maxf(0.0, _melee_left - delta)
    _aiming = aiming
    _running = running
    _movement = clampf(movement, 0.0, 1.0)
    _crouch_alpha = move_toward(_crouch_alpha, 1.0 if crouched else 0.0, delta * 4.6)
    # Temporary squat silhouette until an anatomical crouch Action is authored.
    scale.y = lerpf(scale.y, 1.0 - _crouch_alpha * 0.31, minf(1.0, delta * 7.0))

    # Aim takes precedence over locomotion. Gameplay movement still works while
    # aiming, even though no separate aim-strafe animation exists yet.
    var wanted := "idle"
    if aiming:
        wanted = "aim"
    elif movement > 0.10:
        wanted = "walk"
    if wanted != _state:
        _set_clip(wanted)

    if _state == "walk":
        _player.speed_scale = (1.55 if running else (0.68 if crouched else 1.0))
    else:
        _player.speed_scale = 1.0

    # A short visible torso pivot for takedown/strike while keeping the
    # real skinned body. The gameplay melee detection remains unchanged.
    var twist := 0.0
    if _melee_left > 0.0:
        var duration := .36 if _melee_stealth else .28
        twist = .16 * sin(PI * (1.0 - _melee_left / duration))
    _character.rotation.y = lerp_angle(_character.rotation.y, PI + twist, minf(1.0, delta * 15.0))
    _update_weapon_grip()

func play_melee_animation(stealth: bool) -> void:
    _melee_stealth = stealth
    _melee_left = .36 if stealth else .28

func _set_clip(state: String) -> void:
    if not _valid or _player == null:
        return
    _state = state
    match state:
        "walk":
            _player.play(WALK, 0.20, 1.0)
        "aim":
            _player.play(AIM, 0.24, 1.0)
        "idle":
            # No false "idle" third clip; hold the source walk neutral frame.
            _player.play(WALK, 0.16, 1.0)
            _player.seek(0.0, true)
            _player.pause()

func _on_animation_finished(clip: StringName) -> void:
    if clip == AIM and _state == "aim":
        # Godot clips end after 1.0s: keep last skinned pose stable.
        var max_time := _player.get_animation(AIM).length
        _player.seek(maxf(0.0, max_time - 0.01), true)
        _player.pause()

func _process(_delta: float) -> void:
    if _valid:
        # Follows the evaluated skeletal hand even when the player is idle.
        _update_weapon_grip()

func _update_weapon_grip() -> void:
    if _right_hand == null or _skeleton == null or _hand_index < 0:
        return
    var skel_hand := _skeleton.get_bone_global_pose(_hand_index)
    var world_hand := _skeleton.to_global(skel_hand.origin)
    _right_hand.position = to_local(world_hand)
    # Unlike BoneAttachment, keep gun forward relative to the camera/player,
    # not twisted to the skinning bone's local wrist roll.
    _right_hand.rotation = Vector3.ZERO
