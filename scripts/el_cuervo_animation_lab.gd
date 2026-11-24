extends Node3D
## Silent Killer / El Cuervo — Fase 10: laboratorio real de animaciones.
## ESCENA AISLADA: no reemplaza res://scenes/main.tscn ni al personaje jugable.
## Abre el GLB real de Fase 9 (53 huesos, caminar/apuntar validados).
## Prueba desde Android con botones táctiles o desde PC con W/↑, Q, Espacio.
##
## API de pruebas: set_test_mode("idle" | "walk" | "aim"), get_debug_status().

const CUERVO_GLB := "res://character_assets/el_cuervo/fase9_animaciones/El_Cuervo_Fase9_Walk_Aim_REVISION.glb"
const WALK_CLIP := "Cuervo_Walk_InPlace"
const AIM_CLIP := "Cuervo_Aim_Raise"
const WALK_SPEED := 1.5
const CAM_HEIGHT := 1.4
const CAMERA_DISTANCE := 4.7

var _body: CharacterBody3D
var _model: Node3D
var _anim: AnimationPlayer
var _skeleton: Skeleton3D
var _camera: Camera3D
var _status: Label
var _walk_toggle: Button
var _aim_toggle: Button
var _walk_touch_held := false
var _aim_enabled := false
var _mode := ""
var _error := ""
var _turn_angle := 0.0
var _clips: Array[String] = []

func _ready() -> void:
    name = "ElCuervo_Fase10_Laboratorio"
    _make_scene_environment()
    _make_floor()
    _make_character()
    _make_camera()
    _make_ui()
    if _error.is_empty():
        set_test_mode("idle")
    else:
        _status.text = _error

func _make_character() -> void:
    _body = CharacterBody3D.new()
    _body.name = "Cuervo_Prueba_NoGameplay"
    _body.position = Vector3(0.0, 0.03, 0.0)
    add_child(_body)

    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.28
    capsule.height = 1.83
    var shape := CollisionShape3D.new()
    shape.name = "Collider"
    shape.shape = capsule
    shape.position.y = 0.915
    _body.add_child(shape)

    var resource: Resource = load(CUERVO_GLB)
    if resource == null or not (resource is PackedScene):
        _error = "ERROR: No se pudo importar El Cuervo Fase 9 (.glb)"
        push_error(_error)
        return
    _model = (resource as PackedScene).instantiate() as Node3D
    if _model == null:
        _error = "ERROR: el modelo no contiene raíz Node3D"
        push_error(_error)
        return
    _model.name = "ElCuervo_Real_CC0_Animado"
    _body.add_child(_model)
    _scan_imported_nodes(_model)
    if _anim == null or _skeleton == null:
        _error = "ERROR: faltan AnimationPlayer o Skeleton3D en el modelo"
        push_error(_error)
        return
    if _skeleton.get_bone_count() != 53:
        _error = "ERROR: número inesperado de huesos (%d)" % _skeleton.get_bone_count()
        push_error(_error)
        return
    for clip in _anim.get_animation_list():
        _clips.append(String(clip))
    if not WALK_CLIP in _clips or not AIM_CLIP in _clips:
        _error = "ERROR: faltan clips Walk/Aim: %s" % str(_clips)
        push_error(_error)
        return
    var walk := _anim.get_animation(WALK_CLIP)
    walk.loop_mode = Animation.LOOP_LINEAR
    # Aiming is intentionally not looped: keep the final two-handed pose.
    _anim.get_animation(AIM_CLIP).loop_mode = Animation.LOOP_NONE
    _anim.animation_finished.connect(_on_animation_finished)

func _scan_imported_nodes(node: Node) -> void:
    if node is AnimationPlayer and _anim == null:
        _anim = node as AnimationPlayer
    if node is Skeleton3D and _skeleton == null:
        _skeleton = node as Skeleton3D
    for child in node.get_children():
        _scan_imported_nodes(child)

func set_test_mode(mode_name: String) -> void:
    if not _error.is_empty() or _anim == null:
        return
    if mode_name not in ["idle", "walk", "aim"]:
        push_warning("Modo de laboratorio desconocido: %s" % mode_name)
        return
    if _mode == mode_name:
        return
    _mode = mode_name
    match mode_name:
        "walk":
            _aim_enabled = false
            _anim.play(WALK_CLIP, 0.22, 1.0)
        "aim":
            _aim_enabled = true
            _anim.play(AIM_CLIP, 0.25, 1.0)
        "idle":
            _aim_enabled = false
            # First frame of the in-place walk has relaxed arms.
            # No phantom third animation is claimed or created.
            _anim.play(WALK_CLIP, 0.15, 1.0)
            _anim.seek(0.0, true)
            _anim.pause()
    _update_hud()

func get_debug_status() -> Dictionary:
    return {
        "model_path": CUERVO_GLB,
        "error": _error,
        "mode": _mode,
        "clip": String(_anim.current_animation) if _anim != null else "",
        "animation_count": _clips.size(),
        "animation_names": _clips.duplicate(),
        "rig_bones": _skeleton.get_bone_count() if _skeleton != null else 0,
        "has_character_body": _body != null,
        "has_camera": _camera != null,
        "has_touch_controls": _walk_toggle != null and _aim_toggle != null,
        "game_main_replaced": false,
    }

func _on_animation_finished(name: StringName) -> void:
    # Explicitly hold last evaluated aim pose. Godot may otherwise return
    # bones toward import rest as a non-looped clip finishes.
    if name == AIM_CLIP and _mode == "aim":
        _anim.seek(maxf(0.0, _anim.get_animation(AIM_CLIP).length - 0.01), true)
        _anim.pause()
        _update_hud()

func _physics_process(delta: float) -> void:
    if _body == null or not _error.is_empty():
        return
    var is_keyboard_walking := Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)
    var should_walk := (_walk_touch_held or is_keyboard_walking) and not _aim_enabled
    if should_walk and _mode != "walk":
        set_test_mode("walk")
    elif not should_walk and _mode == "walk":
        set_test_mode("idle")
    if should_walk:
        # Movement is handled by CharacterBody3D only. The clip is IN PLACE,
        # so the GLB does not apply root motion a second time.
        _body.velocity.x = 0.0
        _body.velocity.z = -WALK_SPEED
    else:
        _body.velocity.x = 0.0
        _body.velocity.z = 0.0
    if not _body.is_on_floor():
        _body.velocity.y -= 15.0 * delta
    else:
        _body.velocity.y = -0.03
    _body.move_and_slide()
    if _camera != null:
        _camera.global_position = _camera.global_position.lerp(
            _body.global_position + Vector3(0.0, CAM_HEIGHT + 1.0, CAMERA_DISTANCE),
            minf(1.0, delta * 6.0)
        )
        _camera.look_at(_body.global_position + Vector3(0.0, 1.04, 0.0), Vector3.UP)

func _unhandled_key_input(event: InputEvent) -> void:
    if not (event is InputEventKey) or not event.pressed or event.echo:
        return
    if event.keycode == KEY_Q:
        _toggle_aim()
    elif event.keycode == KEY_SPACE:
        _walk_touch_held = false
        _aim_enabled = false
        set_test_mode("idle")

func _toggle_aim() -> void:
    if _mode == "aim":
        set_test_mode("idle")
    else:
        _walk_touch_held = false
        set_test_mode("aim")
    _update_hud()

func _update_hud() -> void:
    if _status != null:
        var state := "REPOSO"
        if _mode == "walk":
            state = "CAMINANDO"
        elif _mode == "aim":
            state = "APUNTANDO (SIN PISTOLA)"
        _status.text = "EL CUERVO — LAB FASE 10\nEstado: %s\n53 huesos · 2 clips reales" % state
    if _aim_toggle != null:
        _aim_toggle.text = "DEJAR DE APUNTAR" if _mode == "aim" else "APUNTAR"
    if _walk_toggle != null:
        _walk_toggle.disabled = _mode == "aim"

func _make_scene_environment() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.075, 0.086, 0.105)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.52, 0.58, 0.65)
    env.ambient_light_energy = 0.65
    world.environment = env
    add_child(world)
    var light := DirectionalLight3D.new()
    light.name = "Studio_Key_Light"
    light.rotation_degrees = Vector3(-47.0, -26.0, 0.0)
    light.light_color = Color(0.91, 0.94, 1.0)
    light.light_energy = 1.4
    light.shadow_enabled = false
    add_child(light)

func _make_floor() -> void:
    var floor := StaticBody3D.new()
    floor.name = "Stage_Floor"
    floor.position = Vector3(0.0, -0.11, -2.0)
    add_child(floor)
    var mesh := BoxMesh.new()
    mesh.size = Vector3(12.0, 0.2, 18.0)
    var visual := MeshInstance3D.new()
    visual.name = "Floor_Visible"
    visual.mesh = mesh
    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.18, 0.19, 0.21)
    material.roughness = 1.0
    visual.material_override = material
    floor.add_child(visual)
    var solid := CollisionShape3D.new()
    var shape := BoxShape3D.new()
    shape.size = mesh.size
    solid.shape = shape
    floor.add_child(solid)

func _make_camera() -> void:
    _camera = Camera3D.new()
    _camera.name = "Camera_3rdPerson_Lab"
    _camera.current = true
    _camera.position = Vector3(0, CAM_HEIGHT + 1.0, CAMERA_DISTANCE)
    _camera.fov = 56.0
    _camera.near = 0.08
    add_child(_camera)
    _camera.look_at(Vector3(0, 1.0, 0), Vector3.UP)

func _make_ui() -> void:
    var layer := CanvasLayer.new()
    layer.name = "Overlay_Touch"
    add_child(layer)
    var panel := Control.new()
    panel.name = "FullScreen_UI"
    panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(panel)

    _status = Label.new()
    _status.name = "Lab_Status"
    _status.position = Vector2(18.0, 16.0)
    _status.add_theme_font_size_override("font_size", 21)
    _status.add_theme_color_override("font_color", Color(0.96, 0.96, 0.99))
    _status.mouse_filter = Control.MOUSE_FILTER_IGNORE
    panel.add_child(_status)

    var controls := HBoxContainer.new()
    controls.name = "Mobile_Lab_Controls"
    controls.anchor_left = 0.04
    controls.anchor_right = 0.96
    controls.anchor_top = 1.0
    controls.anchor_bottom = 1.0
    controls.offset_top = -102
    controls.offset_bottom = -18
    controls.add_theme_constant_override("separation", 16)
    controls.mouse_filter = Control.MOUSE_FILTER_PASS
    panel.add_child(controls)

    _walk_toggle = Button.new()
    _walk_toggle.name = "Hold_Walk"
    _walk_toggle.text = "MANTENER CAMINAR"
    _walk_toggle.focus_mode = Control.FOCUS_NONE
    _walk_toggle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    _walk_toggle.button_down.connect(func() -> void:
        _walk_touch_held = true
    )
    _walk_toggle.button_up.connect(func() -> void:
        _walk_touch_held = false
    )
    controls.add_child(_walk_toggle)

    _aim_toggle = Button.new()
    _aim_toggle.name = "Toggle_Aim"
    _aim_toggle.text = "APUNTAR"
    _aim_toggle.focus_mode = Control.FOCUS_NONE
    _aim_toggle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    _aim_toggle.pressed.connect(_toggle_aim)
    controls.add_child(_aim_toggle)

    var idle_btn := Button.new()
    idle_btn.name = "Return_Idle"
    idle_btn.text = "REPOSO"
    idle_btn.focus_mode = Control.FOCUS_NONE
    idle_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    idle_btn.pressed.connect(func() -> void:
        _walk_touch_held = false
        set_test_mode("idle")
    )
    controls.add_child(idle_btn)
