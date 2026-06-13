import bpy
import bpy_extras.view3d_utils as v3d

from .state import _svpt_state


def get_r3d(context):
    area = context.area
    if area and area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                return space.region_3d, space
    return None, None


def get_mouse_pivot(context, event):
    region = context.region
    rv3d = context.region_data

    coord = (event.mouse_region_x, event.mouse_region_y)

    view_vec = v3d.region_2d_to_vector_3d(region, rv3d, coord)
    origin = v3d.region_2d_to_origin_3d(region, rv3d, coord)

    depsgraph = context.evaluated_depsgraph_get()
    hit, loc, normal, index, obj, matrix = context.scene.ray_cast(
        depsgraph, origin, view_vec
    )

    if hit:
        return loc

    return None


# Get or create the SVPT Camera collection.
def _get_or_create_svpt_collection(scene):

    collection = bpy.data.collections.get("SVPT Camera")
    if collection is None:
        collection = bpy.data.collections.new("SVPT Camera")
        scene.collection.children.link(collection)
    return collection


def _get_or_create_svpt_camera(scene):
    cam_obj = bpy.data.objects.get("SVPT_Temp_Camera")
    if cam_obj is None or cam_obj.type != 'CAMERA':
        cam_obj = bpy.data.objects.get("SVPT_TempCamera")
    if cam_obj is None or cam_obj.type != 'CAMERA':
        cam_data = bpy.data.cameras.new("SVPT_Temp_CameraData")
        cam_obj = bpy.data.objects.new("SVPT_Temp_Camera", cam_data)
        svpt_collection = _get_or_create_svpt_collection(scene)
        svpt_collection.objects.link(cam_obj)
    elif cam_obj.name not in scene.objects:
        svpt_collection = _get_or_create_svpt_collection(scene)
        svpt_collection.objects.link(cam_obj)
    return cam_obj



def activate_camera_backend(context):
    r3d, space = get_r3d(context)
    if not r3d or not space:
        return None

    scene = context.scene
    cam_obj = _get_or_create_svpt_camera(scene)

    # Show the SVPT camera when activating (viewport AND render)
    cam_obj.hide_set(False)
    cam_obj.hide_viewport = False
    cam_obj.hide_render = False  #  Enable for rendering!!!

    if not _svpt_state["camera_backend_active"]:
        _svpt_state["camera_prev_scene_camera_name"] = scene.camera.name if scene.camera else ""
        _svpt_state["camera_prev_view_perspective"] = r3d.view_perspective
        _svpt_state["camera_prev_use_local_camera"] = getattr(space, "use_local_camera", None)
        _svpt_state["camera_prev_local_camera_name"] = space.camera.name if getattr(space, "camera", None) else ""
        _svpt_state["camera_prev_lock_camera"] = getattr(space, "lock_camera", None)
        cam_obj.matrix_world = r3d.view_matrix.inverted()
        cam_obj.data.lens = space.lens

        _svpt_state["camera_zoom_factor"] = 1.0
        _svpt_state["camera_initial_lens"] = space.lens
        _svpt_state["camera_initial_distance"] = r3d.view_distance
        _svpt_state["camera_initial_sensor_width"] = cam_obj.data.sensor_width

    scene.camera = cam_obj
    if hasattr(space, "use_local_camera"):
        space.use_local_camera = True
    if hasattr(space, "camera"):
        space.camera = cam_obj
    if hasattr(space, "lock_camera"):
        space.lock_camera = True
    r3d.view_perspective = 'CAMERA'

    _svpt_state["camera_backend_active"] = True
    _svpt_state["camera_object_name"] = cam_obj.name
    return cam_obj


def deactivate_camera_backend(context):

    scene = context.scene
    r3d, space = get_r3d(context)

    # Hide the SVPT camera when deactivating
    cam_obj_name = _svpt_state["camera_object_name"]
    if cam_obj_name:
        cam_obj = bpy.data.objects.get(cam_obj_name)
        if cam_obj:
            cam_obj.hide_set(True)
            cam_obj.hide_viewport = True
            cam_obj.hide_render = True  # Hide from renders too

    prev_cam_name = _svpt_state["camera_prev_scene_camera_name"]
    if prev_cam_name:
        prev_cam = bpy.data.objects.get(prev_cam_name)
        scene.camera = prev_cam if prev_cam and prev_cam.type == 'CAMERA' else None
    else:
        scene.camera = None

    prev_perspective = _svpt_state["camera_prev_view_perspective"]
    if r3d and prev_perspective in {'PERSP', 'ORTHO', 'CAMERA'}:
        r3d.view_perspective = prev_perspective

    if space:
        prev_use_local = _svpt_state["camera_prev_use_local_camera"]
        if prev_use_local is not None and hasattr(space, "use_local_camera"):
            space.use_local_camera = prev_use_local

        if hasattr(space, "camera"):
            prev_local_cam_name = _svpt_state["camera_prev_local_camera_name"]
            if prev_local_cam_name:
                prev_local_cam = bpy.data.objects.get(prev_local_cam_name)
                space.camera = prev_local_cam if prev_local_cam and prev_local_cam.type == 'CAMERA' else None
            else:
                space.camera = None

        prev_lock_camera = _svpt_state["camera_prev_lock_camera"]
        if prev_lock_camera is not None and hasattr(space, "lock_camera"):
            space.lock_camera = prev_lock_camera

    _svpt_state["camera_backend_active"] = False
    _svpt_state["camera_object_name"] = None
    _svpt_state["camera_prev_scene_camera_name"] = None
    _svpt_state["camera_prev_view_perspective"] = None
    _svpt_state["camera_prev_use_local_camera"] = None
    _svpt_state["camera_prev_local_camera_name"] = None
    _svpt_state["camera_prev_lock_camera"] = None
    _svpt_state["camera_zoom_factor"] = 1.0
    _svpt_state["camera_initial_lens"] = None
    _svpt_state["camera_initial_distance"] = None
    _svpt_state["camera_initial_sensor_width"] = None


