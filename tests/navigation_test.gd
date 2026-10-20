extends Node3D
## Warehouse route regression: grid uses box footprints, avoids long racks, guards
## obtain new waypoints when patrol/investigation/chase targets change.

const MAIN = preload("res://scripts/main.gd")
var game

func _ready() -> void:
 game = MAIN.new()
 add_child(game)
 call_deferred("_test")

func _test() -> void:
 await get_tree().physics_frame
 await get_tree().physics_frame
 var navigation = game._navigation
 assert(navigation != null,"Main warehouse has no navigation model")
 assert(navigation._built,"Navigation grid not built at scene launch")
 assert(navigation._obstacles.size() >= 8,"Collision boxes were not registered")
 assert(navigation.walkable_at(Vector3(0,.1,9)),"Spawn should be walkable")
 assert(not navigation.walkable_at(Vector3(-6,.1,-7)),"Storage rack A should block travel")

 # A direct walk would go THROUGH rack A. A* must guide the guard around.
 var start := Vector3(-10,.15,-7)
 var goal := Vector3(-2,.15,-7)
 assert(not navigation.line_clear(start,goal),"Rack must obstruct straight line")
 var route: Array[Vector3] = navigation.get_path(start,goal)
 assert(route.size() >= 2,"A* did not find a multi-point detour")
 var prior: Vector3 = start
 var detour := false
 for point in route:
  assert(navigation.line_clear(prior,point),"A* smoothed path cuts into an obstacle")
  if absf(point.z-start.z) >= 2.0:
   detour = true
  prior = point
 assert(detour,"Route did not go around the rack")
 assert(prior.distance_to(goal) < .75,"Route did not reach target")
 # Repeated planning returns deterministic, obstacle-safe paths.
 for iteration in range(10):
  var repeat: Array[Vector3] = navigation.get_path(start,goal)
  assert(repeat.size() >= 2,"Replan failed")
  var previous: Vector3 = start
  for step in repeat:
   assert(navigation.line_clear(previous,step),"One replan cuts through the rack")
   previous = step

 # Integrate with guard controller; no magical straight-line pursuit through rack.
 var guard = game._guards[0]
 guard.set_physics_process(false)
 guard.global_position = start
 guard.navigation = navigation
 guard._route.clear()
 guard._route_refresh = 0.0
 var first_point: Vector3 = guard._next_route_point(.1,goal)
 assert(guard._route.size() > 1,"Guard did not request A* route")
 assert(navigation.line_clear(start,first_point),"Guard steers into first obstacle")
 assert(absf(first_point.z-start.z) > 1.0,"First routing step should avoid rack")
 var planned_before: int = guard.replans
 var changed_goal := Vector3(-2,.15,4)
 guard._next_route_point(.1,changed_goal)
 assert(guard.replans > planned_before,"Guard did not replan when destination changed")
 assert(guard._route_goal.is_equal_approx(changed_goal),"Route goal did not update")

 # Patrol, noise investigation and chase all share the same route steering method.
 guard._switch(guard.PATROL)
 guard._next_route_point(.1,goal)
 assert(not guard._route.is_empty(),"Patrol has no path")
 guard._switch(guard.INVESTIGATE)
 guard._next_route_point(.1,goal)
 assert(not guard._route.is_empty(),"Investigation has no path")
 guard._switch(guard.ALERT)
 guard._next_route_point(.1,goal)
 assert(not guard._route.is_empty(),"Pursuit has no path")

 print("NAVIGATION_TEST_PASS: mapped obstacles / detour / 10 replans / patrol / search / chase")
 get_tree().quit(0)
