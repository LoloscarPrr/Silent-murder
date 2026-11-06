extends SceneTree

func _initialize() -> void:
    var packed = load("res://El_Cuervo_Base_Humana_v1.glb")
    if packed == null or not (packed is PackedScene):
        push_error("ERROR: GLB no pudo cargarse como PackedScene en Godot 4.3")
        quit(2)
        return
    var root = packed.instantiate()
    var counts = count_human_nodes(root)
    print("GODOT43_IMPORTED mesh_instances=", counts.x, " skeleton3d=", counts.y)
    root.free()
    if counts.x < 1 or counts.y < 1:
        push_error("ERROR: faltan MeshInstance3D o Skeleton3D en Godot")
        quit(3)
        return
    quit(0)

func count_human_nodes(node: Node) -> Vector2i:
    var meshes = 1 if node is MeshInstance3D else 0
    var skeletons = 1 if node is Skeleton3D else 0
    for child in node.get_children():
        var sub = count_human_nodes(child)
        meshes += sub.x
        skeletons += sub.y
    return Vector2i(meshes, skeletons)
