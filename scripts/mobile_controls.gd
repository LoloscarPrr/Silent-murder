extends CanvasLayer
## Silent Killer 0.5 — multitouch, objective interaction and mission result screen.
## The HUD buttons are visual only. ScreenTouch.index controls every action:
## finger 0 may move, finger 1 look, finger 2 sprint, finger 3 aim/crouch.

const JOYSTICK_SCRIPT = preload("res://scripts/joystick_canvas.gd")
const JOYSTICK_RADIUS := 78.0
const DEAD_ZONE := 0.09

var operative
var mission_manager
var _mission_state := ""
var _end_overlay: ColorRect
var _result_title: Label
var _result_subtitle: Label
var _mission_label: Label
var _roles: Dictionary = {} # touch index -> "move", "look", "sprint", "aim", "crouch", "info" or "idle"
var _move_touch := -1
var _look_touch := -1

var _joystick_center := Vector2.ZERO
var _joystick_knob := Vector2.ZERO
var _surface: Control
var _joystick_visual: Control
var _buttons: Dictionary = {} # action name -> Button used only for drawing
var _status: Label
var _fps_label: Label
var _ammo_label: Label
var _training_label: Label
var _health_label: Label
var _guards_label: Label
var _alert_label: Label
var _fps_elapsed := 0.0
var _scale := 1.0

func _ready() -> void:
 _surface = Control.new()
 _surface.name = "MultitouchHUD"
 _surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 _surface.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(_surface)

 _joystick_visual = JOYSTICK_SCRIPT.new()
 _joystick_visual.name = "Joystick"
 _joystick_visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 _joystick_visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(_joystick_visual)

 _status = _label("SILENT KILLER  /  NOCHE CERO", Vector2(26,18), 22)
 var hint := _label("ALPHA 0.5  •  OPERACION NOCHE CERO", Vector2(28,49), 14)
 hint.modulate = Color(.75,.83,.83)
 var crosshair := Label.new()
 crosshair.text = "+"
 crosshair.set_anchors_preset(Control.PRESET_CENTER)
 crosshair.position = Vector2(-7,-19)
 crosshair.add_theme_font_size_override("font_size",31)
 crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(crosshair)

 _fps_label = _label("-- FPS",Vector2.ZERO,18)
 _fps_label.anchor_left = .65
 _fps_label.anchor_right = .65
 _fps_label.anchor_top = .03
 _fps_label.anchor_bottom = .03
 _fps_label.modulate = Color(.78,.90,.81)

 _ammo_label = _label("12 / 48",Vector2.ZERO,23)
 _ammo_label.anchor_left = .78
 _ammo_label.anchor_right = .78
 _ammo_label.anchor_top = .04
 _ammo_label.anchor_bottom = .04
 _ammo_label.modulate = Color(1.0,.85,.62)
 _training_label = _label("BLANCOS 0 / 4",Vector2(28,79),17)
 _training_label.modulate = Color(.82,.88,.76)
 _guards_label = _label("GUARDIAS 0 / 3",Vector2(28,102),17)
 _guards_label.modulate = Color(.79,.89,1.0)
 _health_label = _label("VIDA 100 / 100",Vector2(28,126),18)
 _health_label.modulate = Color(.57,.98,.71)
 _alert_label = _label("ESTADO PATRULLA",Vector2.ZERO,17)
 _alert_label.anchor_left = .39
 _alert_label.anchor_right = .39
 _alert_label.anchor_top = .04
 _alert_label.anchor_bottom = .04
 _alert_label.modulate = Color(.63,.93,.73)

 _add_button("DISPARAR","fire",Vector2(.79,.41))
 _add_button("RECARGAR","reload",Vector2(.91,.35))
 _add_button("AGACHAR","crouch",Vector2(.79,.72))
 _add_button("CORRER","sprint",Vector2(.90,.84))
 _add_button("APUNTAR","aim",Vector2(.90,.57))
 _add_button("INFO","info",Vector2(.93,.12))
 _add_button("INTERACTUAR","interact",Vector2(.63,.79))
 _buttons["interact"].visible = false

 _mission_label = _label("RECUPERAR EXPEDIENTE",Vector2(28,153),17)
 _mission_label.modulate = Color(.45,.85,1.0)
 _make_result_overlay()

 if operative != null:
  operative.status_changed.connect(_set_status)
  operative.ammo_changed.connect(_on_ammo_changed)
  _ammo_label.text = operative.get_ammo_label()
 _surface.resized.connect(_layout)
 call_deferred("_layout")

func _label(value: String, at: Vector2, size: int) -> Label:
 var label := Label.new()
 label.text = value
 label.position = at
 label.add_theme_font_size_override("font_size",size)
 label.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(label)
 return label

func _add_button(caption: String, action: String, at: Vector2) -> void:
 var button := Button.new()
 button.name = action
 button.text = caption
 button.set_meta("anchor_position",at)
 button.mouse_filter = Control.MOUSE_FILTER_IGNORE
 button.focus_mode = Control.FOCUS_NONE
 button.disabled = false
 _surface.add_child(button)
 _buttons[action] = button

func _layout() -> void:
 if _surface == null:
  return
 var view := _surface.size
 _scale = clampf(minf(view.x / 1280.0,view.y / 720.0),.8,1.45)
 for action in _buttons:
  var button: Button = _buttons[action]
  var at: Vector2 = button.get_meta("anchor_position")
  var width := (230.0 if action == "restart" else (142.0 if action == "interact" else 108.0)) * _scale
  var height := (80.0 if action == "restart" else 72.0) * _scale
  button.position = Vector2(view.x * at.x - width*.5,view.y * at.y - height*.5)
  button.size = Vector2(width,height)
  button.add_theme_font_size_override("font_size",int(17.0*_scale))
 if _end_overlay != null:
  _end_overlay.size = view
  _result_title.position = Vector2(view.x * .5 - 260.0 * _scale,view.y * .34)
  _result_title.size = Vector2(520.0 * _scale,76.0 * _scale)
  _result_subtitle.position = Vector2(view.x * .5 - 260.0 * _scale,view.y * .49)
  _result_subtitle.size = Vector2(520.0 * _scale,80.0 * _scale)
 if _move_touch == -1:
  _joystick_center = Vector2(view.x*.13,view.y*.76)
  _joystick_knob = _joystick_center
 _redraw()

func _process(delta: float) -> void:
 _fps_elapsed += delta
 if _fps_elapsed >= .5:
  _fps_elapsed = 0.0
  if _fps_label != null:
   _fps_label.text = "%d FPS" % Engine.get_frames_per_second()

func _input(event: InputEvent) -> void:
 if operative == null:
  return
 if event is InputEventScreenTouch:
  var touch := event as InputEventScreenTouch
  if touch.pressed:
   _press(touch.index,touch.position)
  else:
   _release(touch.index)
 elif event is InputEventScreenDrag:
  var drag := event as InputEventScreenDrag
  _drag(drag.index,drag.position,drag.relative)
 elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
  operative.apply_look((event as InputEventMouseMotion).relative,false)

func _press(index: int, at: Vector2) -> void:
 if _mission_state != "":
  if _find_button(at) == "restart":
   get_tree().reload_current_scene()
  return
 if _roles.has(index):
  _release(index)
 # Buttons take precedence over the look area, but only within their actual rects.
 var action := _find_button(at)
 if action != "":
  _roles[index] = action
  _refresh_button(action)
  match action:
   "sprint":
    operative.is_sprinting = true
   "fire":
    operative.set_fire_held(true)
   "reload":
    operative.reload_weapon()
   "interact":
    if mission_manager != null:
     mission_manager.interact()
   "crouch":
    operative.toggle_crouch()
    operative.is_sprinting = _action_held("sprint")
   "aim":
    operative.toggle_aim()
    operative.is_sprinting = _action_held("sprint")
   "info":
    _set_status("Dedo izquierdo: mover  |  derecho: mirar  |  otro: correr")
  return

 var size := get_viewport().get_visible_rect().size
 if _move_touch == -1 and at.x < size.x*.39 and at.y > size.y*.35:
  _roles[index] = "move"
  _move_touch = index
  _joystick_center = at
  _update_move(at)
 elif _look_touch == -1 and at.x >= size.x*.39:
  _roles[index] = "look"
  _look_touch = index
 else:
  # Ignore additional contacts until released. Never steal an existing finger.
  _roles[index] = "idle"

func _drag(index: int, at: Vector2, delta: Vector2) -> void:
 if not _roles.has(index):
  return
 var action: String = _roles[index]
 if action == "move" and index == _move_touch:
  _update_move(at)
 elif action == "look" and index == _look_touch:
  operative.apply_look(delta)
 # A button finger stays bound to its button even if it slides outside.

func _release(index: int) -> void:
 if not _roles.has(index):
  return
 var action: String = _roles[index]
 _roles.erase(index)
 match action:
  "move":
   if index == _move_touch:
    _move_touch = -1
    operative.move_input = Vector2.ZERO
    _joystick_center = Vector2(_surface.size.x*.13,_surface.size.y*.76)
    _joystick_knob = _joystick_center
    _redraw()
  "look":
   if index == _look_touch:
    _look_touch = -1
  "sprint":
   # Another finger could still be holding sprint.
   operative.is_sprinting = _action_held("sprint")
  "fire":
   operative.set_fire_held(_action_held("fire"))
 if _buttons.has(action):
  _refresh_button(action)

func _find_button(at: Vector2) -> String:
 # Topmost buttons first (overlap resolved deterministically).
 for action in (["restart"] if _mission_state != "" else ["interact","info","reload","fire","aim","crouch","sprint"]):
  var button: Button = _buttons[action]
  if button.visible and button.get_global_rect().has_point(at):
   return action
 return ""

func _action_held(action: String) -> bool:
 for index in _roles:
  if _roles[index] == action:
   return true
 return false

func _refresh_button(action: String) -> void:
 var button: Button = _buttons[action]
 button.modulate = Color(1.0,.84,.59) if _action_held(action) else Color(1.0,1.0,1.0)

func _update_move(at: Vector2) -> void:
 var radius := JOYSTICK_RADIUS * _scale
 var offset := (at-_joystick_center).limit_length(radius)
 _joystick_knob = _joystick_center + offset
 var axis := offset / radius
 if axis.length() < DEAD_ZONE:
  axis = Vector2.ZERO
 operative.move_input = axis
 _redraw()

func _on_ammo_changed(magazine: int, reserve: int) -> void:
 if _ammo_label != null:
  _ammo_label.text = "%02d / %02d" % [magazine,reserve]

func set_training_progress(cleared: int, total: int) -> void:
 if _training_label != null:
  _training_label.text = "BLANCOS %d / %d" % [cleared,total]
  if cleared == total and total > 0:
   _training_label.modulate = Color(.53,1.0,.62)
   _set_status("ENTRENAMIENTO COMPLETADO")

func set_health(current: int,maximum: int) -> void:
 if _health_label != null:
  _health_label.text = "VIDA %d / %d" % [current,maximum]
  _health_label.modulate = Color(.95,.34,.32) if current < maximum*.30 else Color(.57,.98,.71)

func set_guard_progress(cleared: int,total: int) -> void:
 if _guards_label != null:
  _guards_label.text = "GUARDIAS %d / %d" % [cleared,total]
  _guards_label.modulate = Color(.57,.98,.71) if cleared >= total and total > 0 else Color(.79,.89,1.0)

func set_alert_status(state: String) -> void:
 if _alert_label == null:
  return
 _alert_label.text = "ESTADO %s" % state
 match state:
  "ALERTA":
   _alert_label.modulate = Color(1.0,.30,.26)
  "SOSPECHA":
   _alert_label.modulate = Color(1.0,.73,.26)
  _:
   _alert_label.modulate = Color(.63,.93,.73)

func set_mission_status(value: String) -> void:
 if _mission_label != null:
  _mission_label.text = value

func set_interaction_available(enabled: bool,caption: String) -> void:
 if _buttons.has("interact"):
  var button: Button = _buttons["interact"]
  button.visible = enabled and _mission_state == ""
  if caption != "":
   button.text = caption

func _make_result_overlay() -> void:
 _end_overlay = ColorRect.new()
 _end_overlay.name = "MissionResultBackdrop"
 _end_overlay.color = Color(.015,.022,.031,.83)
 _end_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 _end_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _end_overlay.visible = false
 _surface.add_child(_end_overlay)

 _result_title = Label.new()
 _result_title.add_theme_font_size_override("font_size",34)
 _result_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 _result_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(_result_title)

 _result_subtitle = Label.new()
 _result_subtitle.add_theme_font_size_override("font_size",20)
 _result_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
 _result_subtitle.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(_result_subtitle)

 _add_button("REINTENTAR","restart",Vector2(.5,.72))
 _buttons["restart"].visible = false
 _result_title.visible = false
 _result_subtitle.visible = false

func show_mission_result(success: bool) -> void:
 if _mission_state != "":
  return
 _reset_touches()
 _mission_state = "success" if success else "failure"
 _end_overlay.visible = true
 _result_title.visible = true
 _result_subtitle.visible = true
 _result_title.text = "CONTRATO COMPLETADO" if success else "OPERACION FALLIDA"
 _result_title.modulate = Color(.48,1.0,.65) if success else Color(1.0,.48,.45)
 _result_subtitle.text = "Expediente recuperado. Extraccion confirmada." if success else "El operativo fue neutralizado. Intenta otra ruta."
 _buttons["restart"].visible = true
 _buttons["restart"].text = "NUEVA PARTIDA" if success else "REINTENTAR"
 _layout()

func _set_status(message: String) -> void:
 if _status != null:
  _status.text = message

func _redraw() -> void:
 if _joystick_visual != null:
  _joystick_visual.center = _joystick_center
  _joystick_visual.knob = _joystick_knob
  _joystick_visual.radius = JOYSTICK_RADIUS*_scale
  _joystick_visual.queue_redraw()

func _reset_touches() -> void:
 _roles.clear()
 _move_touch = -1
 _look_touch = -1
 if operative != null:
  operative.move_input = Vector2.ZERO
  operative.is_sprinting = false
  operative.set_fire_held(false)
 _layout()
 for action in _buttons:
  _refresh_button(action)

func _notification(what: int) -> void:
 if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
  if _surface != null:
   _reset_touches()
