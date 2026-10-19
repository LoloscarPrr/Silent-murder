extends CharacterBody3D
## Silent Murder v0.1: provisional character, movement and over-shoulder camera.

signal status_changed(status: String)

const WALK_SPEED := 4.0
const SPRINT_SPEED := 6.3
const CROUCH_SPEED := 2.0
const MOUSE_SENSITIVITY := 0.0025
const TOUCH_SENSITIVITY := 0.0034

var move_input := Vector2.ZERO
var is_sprinting := false
var is_crouching := false
var is_aiming := false
var walk_time := 0.0
var pitch := -0.09

var _camera: Camera3D
var _camera_rig: Node3D
var _body: Node3D
var _left_leg: MeshInstance3D
var _right_leg: MeshInstance3D
var _left_arm: MeshInstance3D
var _right_arm: MeshInstance3D

func _ready() -> void:
 name = "Operative_Prototype"
 _make_collision()
 _make_model()
 _make_camera()
 status_changed.emit("Infiltración de prueba: explorar el depósito")

func _physics_process(delta: float) -> void:
 var keyboard_move := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
 var directional := move_input if move_input.length() > 0.08 else keyboard_move
 var speed := CROUCH_SPEED if is_crouching else (SPRINT_SPEED if is_sprinting else WALK_SPEED)
 var local_direction := Vector3(directional.x,0.0,directional.y)
 var world_direction := global_transform.basis * local_direction
 if world_direction.length() > 1.0:
  world_direction = world_direction.normalized()
 velocity.x = world_direction.x * speed
 velocity.z = world_direction.z * speed
 if not is_on_floor():
  velocity.y -= 20.0 * delta
 else:
  velocity.y = -0.05
 move_and_slide()
 _animate_prototype(delta,directional.length())
 _camera.fov = lerpf(_camera.fov,49.0 if is_aiming else 65.0,minf(1.0,delta*6.0))
 _camera.position.x = lerpf(_camera.position.x,0.42 if is_aiming else 0.67,minf(1.0,delta*6.0))

func apply_look(delta_pixels: Vector2,touch: bool = true) -> void:
 var sensitivity := TOUCH_SENSITIVITY if touch else MOUSE_SENSITIVITY
 rotate_y(-delta_pixels.x*sensitivity)
 pitch = clampf(pitch-delta_pixels.y*sensitivity,-0.92,0.62)
 _camera_rig.rotation.x = pitch

func toggle_crouch() -> void:
 is_crouching = not is_crouching
 status_changed.emit("Agachado" if is_crouching else "De pie")

func toggle_aim() -> void:
 is_aiming = not is_aiming
 status_changed.emit("Apuntando (sin arma en 0.1)" if is_aiming else "Explorando")

func _make_collision() -> void:
 var shape := CapsuleShape3D.new()
 shape.radius = .34
 shape.height = 1.78
 var collider := CollisionShape3D.new()
 collider.shape = shape
 collider.position.y = .90
 add_child(collider)

func _make_model() -> void:
 _body = Node3D.new()
 _body.name = "Model_Primitive_Placeholder"
 add_child(_body)
 var fabric := _material(Color(.075,.086,.105))
 var vest := _material(Color(.15,.18,.19))
 var trousers := _material(Color(.09,.115,.13))
 var gloves := _material(Color(.02,.027,.033))
 var boots := _material(Color(.035,.044,.051))
 var skin := _material(Color(.52,.385,.32))
 var collar := _material(Color(.28,.305,.315))
 _part("Torso - tailored jacket",Vector3(0,1.30,0),Vector3(.57,.72,.32),fabric)
 _part("Reinforced vest",Vector3(0,1.36,-.175),Vector3(.39,.48,.045),vest)
 _part("Collar",Vector3(0,1.74,0),Vector3(.27,.14,.3),collar)
 _part("Head",Vector3(0,1.91,0),Vector3(.27,.30,.27),skin)
 _part("Hair",Vector3(0,2.075,0),Vector3(.28,.065,.29),gloves)
 _left_arm = _part("Left glove and sleeve",Vector3(-.38,1.31,0),Vector3(.16,.66,.19),fabric)
 _right_arm = _part("Right glove and sleeve",Vector3(.38,1.31,0),Vector3(.16,.66,.19),fabric)
 _part("Left glove",Vector3(-.38,.96,0),Vector3(.16,.18,.20),gloves)
 _part("Right glove",Vector3(.38,.96,0),Vector3(.16,.18,.20),gloves)
 _left_leg = _part("Left leg",Vector3(-.16,.49,0),Vector3(.22,.87,.23),trousers)
 _right_leg = _part("Right leg",Vector3(.16,.49,0),Vector3(.22,.87,.23),trousers)
 _part("Left boot",Vector3(-.16,.075,-.045),Vector3(.23,.16,.35),boots)
 _part("Right boot",Vector3(.16,.075,-.045),Vector3(.23,.16,.35),boots)

func _make_camera() -> void:
 _camera_rig = Node3D.new()
 _camera_rig.name = "OverShoulder_Rig"
 _camera_rig.position = Vector3(0,1.48,0)
 add_child(_camera_rig)
 _camera_rig.rotation.x = pitch
 _camera = Camera3D.new()
 _camera.name = "FollowCamera"
 _camera.position = Vector3(.67,.07,3.1)
 _camera.fov = 65.0
 _camera.current = true
 _camera_rig.add_child(_camera)

func _animate_prototype(delta: float,intensity: float) -> void:
 var moving := intensity > .1
 walk_time += delta*(9.0 if is_sprinting else 6.0)*(intensity if moving else 0.0)
 var cycle := sin(walk_time)*minf(intensity,1.0)
 _left_leg.rotation.x = lerpf(_left_leg.rotation.x,cycle*.16,delta*10.0)
 _right_leg.rotation.x = lerpf(_right_leg.rotation.x,-cycle*.16,delta*10.0)
 _left_arm.rotation.x = lerpf(_left_arm.rotation.x,-cycle*.11,delta*9.0)
 _right_arm.rotation.x = lerpf(_right_arm.rotation.x,cycle*.11,delta*9.0)
 _body.scale.y = lerpf(_body.scale.y,.78 if is_crouching else 1.0,delta*7.0)

func _part(label: String,at: Vector3,dimensions: Vector3,mat: Material) -> MeshInstance3D:
 var node := MeshInstance3D.new()
 node.name = label
 var mesh := BoxMesh.new()
 mesh.size = dimensions
 node.mesh = mesh
 node.material_override = mat
 node.position = at
 _body.add_child(node)
 return node

func _material(tint: Color) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = tint
 m.roughness = .92
 return m
