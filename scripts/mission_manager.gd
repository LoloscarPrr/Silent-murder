extends Node3D
## Silent Killer Alpha 0.5 — Operación Noche Cero.
## Recover the sealed intel dossier, then return to the extraction beacon.
## Guards are an obstacle but eliminating them is never mandatory.

signal mission_finished(success: bool)

const INFILTRATE := "INFILTRAR"
const EXTRACT := "EXTRAER"
const SUCCESS := "EXITO"
const FAILED := "FRACASO"
const INTERACT_RADIUS := 2.25

const INTEL_POSITION := Vector3(11.5,0.0,-6.5)
const EXTRACTION_POSITION := Vector3(-11.5,0.0,11.5)

var player: CharacterBody3D
var hud
var guards: Array[CharacterBody3D] = []
var state := INFILTRATE
var intel_collected := false
var _intel_marker: Node3D
var _extraction_marker: Node3D
var _extraction_light: OmniLight3D
var _range_ready := false
var _update_counter := 0.0

func _ready() -> void:
 name = "OperacionNocheCero"
 _make_intel_terminal()
 _make_extraction()
 _update_ui()

func _process(delta: float) -> void:
 if player == null or not is_instance_valid(player) or state == SUCCESS or state == FAILED:
  return
 _update_counter += delta
 if _update_counter < .13:
  return
 _update_counter = 0.0
 var destination := INTEL_POSITION if state == INFILTRATE else EXTRACTION_POSITION
 var distance := _horizontal_distance(destination)
 _range_ready = distance <= INTERACT_RADIUS
 if hud != null:
  hud.set_interaction_available(_range_ready, "RECUPERAR" if state == INFILTRATE else "EXTRAER")
  var goal := "RECUPERAR EXPEDIENTE" if state == INFILTRATE else "LLEGAR A EXTRACCION"
  hud.set_mission_status("%s  •  %d m" % [goal,ceili(distance)])

func interact() -> bool:
 if player == null or not is_instance_valid(player):
  return false
 if state == SUCCESS or state == FAILED:
  return false
 var destination := INTEL_POSITION if state == INFILTRATE else EXTRACTION_POSITION
 if _horizontal_distance(destination) > INTERACT_RADIUS:
  return false
 if state == INFILTRATE:
  intel_collected = true
  state = EXTRACT
  _range_ready = false
  _intel_marker.visible = false
  _extraction_marker.visible = true
  _extraction_light.visible = true
  _update_ui()
  return true
 if state == EXTRACT and intel_collected:
  _finish(true)
  return true
 return false

func on_player_defeated() -> void:
 if state == SUCCESS or state == FAILED:
  return
 _finish(false)

func _finish(won: bool) -> void:
 state = SUCCESS if won else FAILED
 _range_ready = false
 if player != null:
  player.move_input = Vector2.ZERO
  player.is_sprinting = false
  player.set_fire_held(false)
  player.controls_locked = true
 for guard in guards:
  if is_instance_valid(guard):
   guard.set_physics_process(false)
 if hud != null:
  hud.set_interaction_available(false,"")
  hud.set_mission_status("CONTRATO COMPLETADO" if won else "CONTRATO FALLIDO")
  hud.show_mission_result(won)
 mission_finished.emit(won)

func _update_ui() -> void:
 if hud == null:
  return
 var destination := INTEL_POSITION if state == INFILTRATE else EXTRACTION_POSITION
 var distance := _horizontal_distance(destination)
 hud.set_mission_status("%s  •  %d m" % [
  "RECUPERAR EXPEDIENTE" if state == INFILTRATE else "LLEGAR A EXTRACCION",
  ceili(distance)
 ])
 hud.set_interaction_available(distance <= INTERACT_RADIUS,
  "RECUPERAR" if state == INFILTRATE else "EXTRAER")
 if state == EXTRACT:
  hud.set_alert_status("OBJETIVO ASEGURADO")

func _horizontal_distance(point: Vector3) -> float:
 if player == null:
  return 999.0
 return Vector2(player.global_position.x,player.global_position.z).distance_to(Vector2(point.x,point.z))

func _make_intel_terminal() -> void:
 _intel_marker = Node3D.new()
 _intel_marker.name = "Intel_Dossier_Terminal"
 _intel_marker.position = INTEL_POSITION
 add_child(_intel_marker)
 var matte := _material(Color(.115,.15,.175),false)
 var blue := _material(Color(.15,.70,.95),true)
 _box(_intel_marker,"Steel console",Vector3(0,.65,0),Vector3(1.12,1.3,.72),matte)
 _box(_intel_marker,"Data display",Vector3(0,1.04,-.37),Vector3(.83,.54,.055),blue)
 _box(_intel_marker,"Sealed dossier",Vector3(0,1.43,-.04),Vector3(.53,.13,.40),_material(Color(.70,.57,.29),false))
 var lamp := OmniLight3D.new()
 lamp.position = Vector3(0,2.2,0)
 lamp.light_color = Color(.3,.73,1.0)
 lamp.light_energy = .85
 lamp.omni_range = 4.0
 lamp.shadow_enabled = false
 _intel_marker.add_child(lamp)

func _make_extraction() -> void:
 _extraction_marker = Node3D.new()
 _extraction_marker.name = "ExtractionBeacon"
 _extraction_marker.position = EXTRACTION_POSITION
 add_child(_extraction_marker)
 var green := _material(Color(.28,.88,.53),true)
 var steel := _material(Color(.16,.25,.25),false)
 # Distinctive glowing gate and floor marker are visible from a distance.
 _box(_extraction_marker,"Landing zone",Vector3(0,.028,0),Vector3(3.1,.055,3.1),steel)
 for x in [-1.32,1.32]:
  _box(_extraction_marker,"Beacon pillar",Vector3(x,1.35,0),Vector3(.16,2.7,.19),green)
 _box(_extraction_marker,"Extraction header",Vector3(0,2.72,0),Vector3(2.83,.17,.19),green)
 _extraction_light = OmniLight3D.new()
 _extraction_light.name = "Extraction Signal"
 _extraction_light.position = Vector3(0,2.5,0)
 _extraction_light.omni_range = 6.0
 _extraction_light.light_color = Color(.19,1.0,.48)
 _extraction_light.light_energy = 1.15
 _extraction_light.shadow_enabled = false
 _extraction_marker.add_child(_extraction_light)
 _extraction_marker.visible = false
 _extraction_light.visible = false

func _box(parent: Node3D, label: String, pos: Vector3, dimensions: Vector3, material: Material) -> void:
 var mesh := BoxMesh.new()
 mesh.size = dimensions
 var instance := MeshInstance3D.new()
 instance.mesh = mesh
 instance.name = label
 instance.position = pos
 instance.material_override = material
 parent.add_child(instance)

func _material(color: Color, emissive: bool) -> StandardMaterial3D:
 var mat := StandardMaterial3D.new()
 mat.albedo_color = color
 mat.roughness = .82
 if emissive:
  mat.emission_enabled = true
  mat.emission = color
  mat.emission_energy_multiplier = 1.2
 return mat
