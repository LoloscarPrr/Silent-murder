extends Control
## Decorative virtual stick; input is handled in mobile_controls.gd.
var center := Vector2(160,550)
var knob := Vector2(160,550)

func _draw() -> void:
 draw_circle(center,72.0,Color(.52,.62,.64,.19))
 draw_arc(center,72.0,0.0,TAU,64,Color(.78,.84,.83,.57),2.0,true)
 draw_circle(knob,29.0,Color(.7,.82,.83,.50))
 draw_arc(knob,29.0,0.0,TAU,48,Color(.93,.95,.93,.75),2.0,true)
