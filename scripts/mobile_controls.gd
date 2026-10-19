extends CanvasLayer
## Silent Murder 0.3 — independent multi-finger touch controls and firing.
## The HUD buttons are visual only. ScreenTouch.index controls every action:
## finger 0 may move, finger 1 look, finger 2 sprint, finger 3 aim/crouch.

const JOYSTICK_SCRIPT = preload("res://scripts/joystick_canvas.gd")
const JOYSTICK_RADIUS := 78.0
const DEAD_ZONE := 0.09

var operative
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

 _status = _label("SILENT MURDER  /  ENTRENAMIENTO", Vector2(26,18), 22)
 var hint := _label("ALPHA 0.3  •  DISPARO Y MULTITOUCH", Vector2(28,49), 14)
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

 _add_button("DISPARAR","fire",Vector2(.79,.41))
 _add_button("RECARGAR","reload",Vector2(.91,.35))
 _add_button("AGACHAR","crouch",Vector2(.79,.72))
 _add_button("CORRER","sprint",Vector2(.90,.84))
 _add_button("APUNTAR","aim",Vector2(.90,.57))
 _add_button("INFO","info",Vector2(.93,.12))

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
  var width := 108.0 * _scale
  var height := 72.0 * _scale
  button.position = Vector2(view.x * at.x - width*.5,view.y * at.y - height*.5)
  button.size = Vector2(width,height)
  button.add_theme_font_size_override("font_size",int(17.0*_scale))
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
 for action in ["info","reload","fire","aim","crouch","sprint"]:
  var button: Button = _buttons[action]
  if button.get_global_rect().has_point(at):
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
