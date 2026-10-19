extends Control
## Passive joystick visual. The router in mobile_controls.gd owns every touch.

var center := Vector2(160,550)
var knob := Vector2(160,550)
var radius := 78.0

func _draw() -> void:
 draw_circle(center,radius,Color(.52,.62,.64,.19))
 draw_arc(center,radius,0.0,TAU,64,Color(.78,.84,.83,.57),2.0,true)
 draw_circle(knob,radius*.39,Color(.7,.82,.83,.50))
 draw_arc(knob,radius*.39,0.0,TAU,48,Color(.93,.95,.93,.75),2.0,true)
