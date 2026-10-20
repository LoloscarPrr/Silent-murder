extends Node3D
## Alpha 0.6: A* grid for the existing flat warehouse.
## The grid is built once from the exact same collision-box footprints as the level.
## A 0.48 m clearance protects the 0.34 m guard capsule from cutting corners.

const CELL := 0.70
const GRID_HALF := 21
const CLEARANCE := 0.48

var _grid: AStarGrid2D = AStarGrid2D.new()
var _obstacles: Array[Rect2] = []
var _built := false
var searches := 0

func add_obstacle(center: Vector3, size: Vector3) -> void:
 # Floors, decals and waist-high painted stripes must not obstruct walking.
 if size.y < 0.55 or center.y+size.y*.5 < .50:
  return
 var expanded := Vector2(size.x*.5+CLEARANCE,size.z*.5+CLEARANCE)
 _obstacles.append(Rect2(Vector2(center.x,center.z)-expanded,expanded*2.0))
 _built = false

func build() -> void:
 _grid.region = Rect2i(Vector2i(-GRID_HALF,-GRID_HALF),Vector2i(GRID_HALF*2+1,GRID_HALF*2+1))
 _grid.cell_size = Vector2(CELL,CELL)
 _grid.offset = Vector2.ZERO
 _grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
 _grid.update()
 for z in range(-GRID_HALF,GRID_HALF+1):
  for x in range(-GRID_HALF,GRID_HALF+1):
   var cell := Vector2i(x,z)
   if _in_blocker(_cell_world(cell)):
    _grid.set_point_solid(cell,true)
 _built = true

func calculate_route(from: Vector3,to: Vector3) -> Array[Vector3]:
 var empty: Array[Vector3] = []
 if not _built:
  build()
 var start := _nearest_clear(_to_cell(from))
 var destination := _nearest_clear(_to_cell(to))
 if not _grid.region.has_point(start) or not _grid.region.has_point(destination):
  return empty
 if _grid.is_point_solid(start) or _grid.is_point_solid(destination):
  return empty
 searches += 1
 var ids: Array[Vector2i] = _grid.get_id_path(start,destination)
 if ids.is_empty():
  return empty
 var raw: Array[Vector3] = []
 # Never return the origin cell; the guard may be at an arbitrary point inside it.
 for i in range(1,ids.size()):
  var world := _cell_world(ids[i])
  raw.append(Vector3(world.x,from.y,world.y))
 var final_point := Vector3(to.x,from.y,to.z)
 if _line_clear(raw.back() if not raw.is_empty() else from,final_point):
  raw.append(final_point)
 if raw.is_empty():
  return empty
 # Greedy path smoothing, using the same padded obstacle geometry.
 var simplified: Array[Vector3] = []
 var cursor := from
 var index := 0
 while index < raw.size():
  var furthest := index
  for candidate in range(raw.size()-1,index-1,-1):
   if _line_clear(cursor,raw[candidate]):
    furthest = candidate
    break
  var next_step: Vector3 = raw[furthest]
  simplified.append(next_step)
  cursor = next_step
  index = furthest+1
 return simplified

func line_clear(a: Vector3,b: Vector3) -> bool:
 return _line_clear(a,b)

func walkable_at(pos: Vector3) -> bool:
 if not _built:
  build()
 var cell := _to_cell(pos)
 return _grid.region.has_point(cell) and not _grid.is_point_solid(cell)

func _nearest_clear(cell: Vector2i) -> Vector2i:
 if _grid.region.has_point(cell) and not _grid.is_point_solid(cell):
  return cell
 var best := Vector2i(GRID_HALF*5,GRID_HALF*5)
 var best_distance := INF
 for radius in range(1,9):
  for y in range(cell.y-radius,cell.y+radius+1):
   for x in range(cell.x-radius,cell.x+radius+1):
    if absi(x-cell.x) != radius and absi(y-cell.y) != radius:
     continue
    var candidate := Vector2i(x,y)
    if not _grid.region.has_point(candidate) or _grid.is_point_solid(candidate):
     continue
    var distance := Vector2(candidate).distance_squared_to(Vector2(cell))
    if distance < best_distance:
     best_distance = distance
     best = candidate
  if best_distance < INF:
   return best
 return best

func _to_cell(world: Vector3) -> Vector2i:
 return Vector2i(roundi(world.x/CELL),roundi(world.z/CELL))

func _cell_world(id: Vector2i) -> Vector2:
 return _grid.get_point_position(id)

func _in_blocker(point: Vector2) -> bool:
 for rectangle in _obstacles:
  if rectangle.has_point(point):
   return true
 return false

func _line_clear(a: Vector3,b: Vector3) -> bool:
 var origin := Vector2(a.x,a.z)
 var destination := Vector2(b.x,b.z)
 var distance := origin.distance_to(destination)
 var samples := maxi(1,ceili(distance/.23))
 for i in range(samples+1):
  var point := origin.lerp(destination,float(i)/float(samples))
  if absf(point.x) > GRID_HALF*CELL or absf(point.y) > GRID_HALF*CELL:
   return false
  if _in_blocker(point):
   return false
 return true
