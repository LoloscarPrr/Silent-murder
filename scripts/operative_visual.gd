extends Node3D
## Silent Killer 0.5.2: procedural locomotion with melee strike / takedown poses.
## Uses only Godot primitives. A rigged humanoid asset will replace it later.

var _time := 0.0
var _walk_blend := 0.0
var _crouch_blend := 0.0
var _aim_blend := 0.0
var _sprint_blend := 0.0
var _melee_left := 0.0
var _melee_stealth := false

var torso: Node3D
var head: Node3D
var hip_left: Node3D
var hip_right: Node3D
var knee_left: Node3D
var knee_right: Node3D
var shoulder_left: Node3D
var shoulder_right: Node3D
var elbow_left: Node3D
var elbow_right: Node3D

func _ready() -> void:
 name = "Operative_Articulated_Prototype"
 _build()

func play_melee_animation(stealth: bool) -> void:
 _melee_left = .36 if stealth else .28
 _melee_stealth = stealth

func animate_pose(delta: float, movement: float, strafing: float, crouched: bool, aiming: bool, running: bool) -> void:
 _melee_left = maxf(0.0,_melee_left-delta)
 var f := clampf(movement, 0.0, 1.0)
 _walk_blend = move_toward(_walk_blend, f, delta * 5.5)
 _crouch_blend = move_toward(_crouch_blend, 1.0 if crouched else 0.0, delta * 5.0)
 _aim_blend = move_toward(_aim_blend, 1.0 if aiming else 0.0, delta * 6.0)
 _sprint_blend = move_toward(_sprint_blend, 1.0 if running and not crouched and not aiming else 0.0, delta * 4.0)
 _time += delta * (5.4 + _sprint_blend * 4.2) * _walk_blend
 var stride := sin(_time) * _walk_blend * (0.38 + _sprint_blend * 0.22) * (1.0 - _aim_blend * 0.55)
 var counter := sin(_time + PI)
 var step_up_left := maxf(0.0, sin(_time)) * _walk_blend
 var step_up_right := maxf(0.0, counter) * _walk_blend
 # A crouch is a full posed transition, not just a smaller silhouette.
 scale.y = lerpf(scale.y, 1.0 - _crouch_blend * 0.37, minf(1.0, delta * 8.0))
 position.y = lerpf(position.y, -_crouch_blend * 0.015, minf(1.0, delta * 7.0))
 torso.rotation.x = lerpf(torso.rotation.x, _crouch_blend * -0.21 + _sprint_blend * -0.10, minf(1.0,delta * 7.0))
 torso.rotation.z = lerpf(torso.rotation.z, clampf(strafing, -1.0, 1.0) * -0.055, minf(1.0,delta * 6.0))
 head.rotation.x = lerpf(head.rotation.x, _aim_blend * -0.05, minf(1.0,delta * 7.0))
 var crouch_hip := _crouch_blend * 0.30
 hip_left.rotation.x = lerpf(hip_left.rotation.x, stride + crouch_hip, minf(1.0,delta * 9.0))
 hip_right.rotation.x = lerpf(hip_right.rotation.x, -stride + crouch_hip, minf(1.0,delta * 9.0))
 knee_left.rotation.x = lerpf(knee_left.rotation.x, -step_up_left * 0.36 - _crouch_blend * 0.40, minf(1.0,delta * 10.0))
 knee_right.rotation.x = lerpf(knee_right.rotation.x, -step_up_right * 0.36 - _crouch_blend * 0.40, minf(1.0,delta * 10.0))
 shoulder_left.rotation.x = lerpf(shoulder_left.rotation.x, -stride * 0.80 - _aim_blend * 0.75, minf(1.0,delta * 9.0))
 shoulder_right.rotation.x = lerpf(shoulder_right.rotation.x, stride * 0.80 - _aim_blend * 0.75, minf(1.0,delta * 9.0))
 elbow_left.rotation.x = lerpf(elbow_left.rotation.x, -0.11 - _aim_blend * 0.80, minf(1.0,delta * 9.0))
 elbow_right.rotation.x = lerpf(elbow_right.rotation.x, -0.11 - _aim_blend * 0.80, minf(1.0,delta * 9.0))
 var breath := sin(Time.get_ticks_msec() * 0.0026) * 0.003
 torso.position.y = 1.23 + breath + absf(sin(_time)) * _walk_blend * 0.012
 if _melee_left > 0.0:
  var duration := .36 if _melee_stealth else .28
  var phase := 1.0 - _melee_left / duration
  var punch := sin(PI*phase)
  if _melee_stealth:
   shoulder_left.rotation.x = -0.85*punch
   shoulder_right.rotation.x = -1.12*punch
   elbow_left.rotation.x = -1.15*punch
   torso.rotation.x -= .19*punch
  else:
   shoulder_right.rotation.x = -1.45*punch
   elbow_right.rotation.x = -.82*punch
   torso.rotation.y = -.18*punch
 else:
  torso.rotation.y = lerpf(torso.rotation.y,0.0,minf(1.0,delta*12.0))

func _build() -> void:
 var suit := _mat(Color(0.095,0.112,0.125))
 var fabric := _mat(Color(0.13,0.149,0.156))
 var armor := _mat(Color(0.20,0.235,0.237))
 var dark := _mat(Color(0.035,0.046,0.054))
 var skin := _mat(Color(0.52,0.36,0.29))
 var metal := _mat(Color(0.30,0.34,0.34))

 torso = Node3D.new()
 torso.name = "Torso"
 torso.position.y = 1.23
 add_child(torso)
 _box(torso, "Tailored jacket", Vector3(0,0.07,0),Vector3(0.54,0.65,0.31),suit)
 _box(torso, "Low profile protection",Vector3(0,0.08,-0.164),Vector3(0.39,0.42,0.055),armor)
 _box(torso, "Waist belt",Vector3(0,-0.28,0),Vector3(0.49,0.10,0.33),dark)
 _box(torso, "Collar",Vector3(0,0.42,0),Vector3(0.25,0.13,0.29),fabric)
 _box(torso, "Chest strap",Vector3(0.12,0.08,-0.198),Vector3(0.09,0.41,0.025),dark)
 _box(torso, "Small buckle",Vector3(0,-0.29,-0.185),Vector3(0.11,0.07,0.025),metal)
 head = Node3D.new()
 head.name = "HeadPivot"
 head.position = Vector3(0,0.64,0)
 torso.add_child(head)
 _sphere(head,"Head",Vector3(0,0,0),Vector3(.29,.32,.285),skin)
 _sphere(head,"Short hair",Vector3(0,.153,.016),Vector3(.31,.12,.295),dark)
 _box(head,"Back neck guard",Vector3(0,-.20,.045),Vector3(.27,.10,.26),fabric)

 hip_left = _limb_pivot(self,"Left thigh", Vector3(-.16,.92,0))
 hip_right = _limb_pivot(self,"Right thigh", Vector3(.16,.92,0))
 _capsule(hip_left,"Left trouser",Vector3(0,-.23,0),.125,.49,suit)
 _capsule(hip_right,"Right trouser",Vector3(0,-.23,0),.125,.49,suit)
 knee_left = _limb_pivot(hip_left,"Left knee",Vector3(0,-.45,0))
 knee_right = _limb_pivot(hip_right,"Right knee",Vector3(0,-.45,0))
 _capsule(knee_left,"Left shin",Vector3(0,-.19,0),.112,.42,fabric)
 _capsule(knee_right,"Right shin",Vector3(0,-.19,0),.112,.42,fabric)
 _box(knee_left,"Left boot",Vector3(0,-.42,-.055),Vector3(.25,.20,.36),dark)
 _box(knee_right,"Right boot",Vector3(0,-.42,-.055),Vector3(.25,.20,.36),dark)

 shoulder_left = _limb_pivot(torso,"Left shoulder",Vector3(-.38,.33,0))
 shoulder_right = _limb_pivot(torso,"Right shoulder",Vector3(.38,.33,0))
 _capsule(shoulder_left,"Left jacket sleeve",Vector3(0,-.19,0),.105,.42,suit)
 _capsule(shoulder_right,"Right jacket sleeve",Vector3(0,-.19,0),.105,.42,suit)
 elbow_left = _limb_pivot(shoulder_left,"Left elbow",Vector3(0,-.40,0))
 elbow_right = _limb_pivot(shoulder_right,"Right elbow",Vector3(0,-.40,0))
 _capsule(elbow_left,"Left forearm",Vector3(0,-.16,0),.087,.32,fabric)
 _capsule(elbow_right,"Right forearm",Vector3(0,-.16,0),.087,.32,fabric)
 _box(elbow_left,"Left glove",Vector3(0,-.34,-.007),Vector3(.16,.16,.17),dark)
 _box(elbow_right,"Right glove",Vector3(0,-.34,-.007),Vector3(.16,.16,.17),dark)

func _limb_pivot(parent: Node, label: String, at: Vector3) -> Node3D:
 var n := Node3D.new()
 n.name = label
 n.position = at
 parent.add_child(n)
 return n

func _box(parent: Node3D,label: String,at: Vector3,dims: Vector3,mat: Material) -> void:
 var m := BoxMesh.new()
 m.size = dims
 _place(parent,label,m,at,mat)

func _capsule(parent: Node3D,label: String,at: Vector3,radius: float,height: float,mat: Material) -> void:
 var m := CapsuleMesh.new()
 m.radius = radius
 m.height = height
 m.radial_segments = 8
 m.rings = 3
 _place(parent,label,m,at,mat)

func _sphere(parent: Node3D,label: String,at: Vector3,dims: Vector3,mat: Material) -> void:
 var m := SphereMesh.new()
 m.radial_segments = 12
 m.rings = 6
 var part := _place(parent,label,m,at,mat)
 part.scale = dims

func _place(parent: Node3D,label: String,mesh: Mesh,at: Vector3,mat: Material) -> MeshInstance3D:
 var part := MeshInstance3D.new()
 part.name = label
 part.mesh = mesh
 part.position = at
 part.material_override = mat
 parent.add_child(part)
 return part

func _mat(color: Color) -> StandardMaterial3D:
 var m := StandardMaterial3D.new()
 m.albedo_color = color
 m.roughness = .89
 return m
