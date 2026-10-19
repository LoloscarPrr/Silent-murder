extends CanvasLayer
## Independent touch identifiers for movement vs. right-side camera.

var operative
var _move_touch := -1
var _look_touch := -1
var _joystick_center := Vector2.ZERO
var _joystick_knob := Vector2.ZERO
var _surface: Control
var _joystick_visual: Control
var _status: Label
var _crosshair: Label

func _ready() -> void:
 _surface = Control.new()
 _surface.name = "HUD_Surface"
 _surface.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 _surface.mouse_filter = Control.MOUSE_FILTER_IGNORE
 add_child(_surface)
 _joystick_visual = preload("res://scripts/joystick_canvas.gd").new()
 _joystick_visual.name = "JoystickVisual"
 _joystick_visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
 _joystick_visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
 _surface.add_child(_joystick_visual)
 _status = Label.new()
 _status.text = "SILENT MURDER // Prueba de movimiento"
 _status.position = Vector2(26,23)
 _status.add_theme_font_size_override("font_size",22)
 _surface.add_child(_status)
 var hint := Label.new()
 hint.text = "FASE 0.1  •  SIN COMBATE"
 hint.position = Vector2(28,55)
 hint.modulate = Color(.72,.82,.8)
 hint.add_theme_font_size_override("font_size",15)
 _surface.add_child(hint)
 _crosshair = Label.new()
 _crosshair.text = "+"
 _crosshair.set_anchors_preset(Control.PRESET_CENTER)
 _crosshair.position = Vector2(-6,-17)
 _crosshair.add_theme_font_size_override("font_size",30)
 _surface.add_child(_crosshair)
 _button("AGACHAR",Vector2(.80,.71),"crouch")
 _button("CORRER",Vector2(.88,.83),"sprint")
 _button("APUNTAR",Vector2(.88,.58),"aim")
 _button("INFO",Vector2(.93,.06),"info")
 if operative != null:
  operative.status_changed.connect(_set_status)
 _surface.resized.connect(_surface_changed)
 call_deferred("_surface_changed")

func _surface_changed() -> void:
 if _move_touch == -1:
  _joystick_center = Vector2(_surface.size.x*.125,_surface.size.y*.76)
  _joystick_knob = _joystick_center
 _redraw_joystick()

func _input(event: InputEvent) -> void:
 if operative == null:
  return
 if event is InputEventScreenTouch:
  var e := event as InputEventScreenTouch
  var point := e.position
  if e.pressed:
   if _move_touch == -1 and point.x < get_viewport().get_visible_rect().size.x*.38 and point.y > get_viewport().get_visible_rect().size.y*.35:
    _move_touch = e.index
    _joystick_center = point
    _joystick_knob = point
    _update_move(point)
   elif _look_touch == -1 and point.x > get_viewport().get_visible_rect().size.x*.38 and not _is_button_zone(point):
    _look_touch = e.index
  else:
   if e.index == _move_touch:
    _move_touch = -1
    operative.move_input = Vector2.ZERO
    _joystick_center = Vector2(_surface.size.x*.125,_surface.size.y*.76)
    _joystick_knob = _joystick_center
   if e.index == _look_touch:
    _look_touch = -1
  _redraw_joystick()
 elif event is InputEventScreenDrag:
  var drag := event as InputEventScreenDrag
  if drag.index == _move_touch:
   _update_move(drag.position)
  elif drag.index == _look_touch:
   operative.apply_look(drag.relative)
 elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
  operative.apply_look((event as InputEventMouseMotion).relative,false)

func _is_button_zone(at: Vector2) -> bool:
 var size := get_viewport().get_visible_rect().size
 return (at.x > size.x*.72 and at.y > size.y*.45) or (at.x > size.x*.86 and at.y < size.y*.19)

func _update_move(at: Vector2) -> void:
 var displacement := (at-_joystick_center).limit_length(72.0)
 _joystick_knob = _joystick_center+displacement
 operative.move_input = displacement/72.0
 _redraw_joystick()

func _button(caption: String,anchor: Vector2,action: String) -> void:
 var b := Button.new()
 b.text = caption
 b.name = caption
 b.custom_minimum_size = Vector2(100,68)
 b.anchor_left = anchor.x
 b.anchor_top = anchor.y
 b.anchor_right = anchor.x
 b.anchor_bottom = anchor.y
 b.offset_left = -52.0
 b.offset_right = 52.0
 b.offset_top = -32.0
 b.offset_bottom = 36.0
 _surface.add_child(b)
 if action == "crouch":
  b.pressed.connect(func() -> void: operative.toggle_crouch())
 if action == "aim":
  b.pressed.connect(func() -> void: operative.toggle_aim())
 if action == "info":
  b.pressed.connect(func() -> void: _status.text = "Movimiento + cámara: fase 0.1")
 if action == "sprint":
  b.button_down.connect(func() -> void: operative.is_sprinting = true)
  b.button_up.connect(func() -> void: operative.is_sprinting = false)

func _set_status(message: String) -> void:
 _status.text = message

func _redraw_joystick() -> void:
 if _joystick_visual != null:
  _joystick_visual.center = _joystick_center
  _joystick_visual.knob = _joystick_knob
  _joystick_visual.queue_redraw()
