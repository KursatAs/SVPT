import bpy

from .state import _svpt_state
from .utils import (
    activate_camera_backend,
    deactivate_camera_backend,
    get_r3d,
)


class SVPT_ViewBookmark(bpy.types.PropertyGroup):
    # Stores a saved view state
    name: bpy.props.StringProperty(
        name="View Name",
        default="View"
    )
    lens: bpy.props.FloatProperty(name="Lens", default=50.0)
    distance: bpy.props.FloatProperty(name="Distance", default=10.0)
    view_location: bpy.props.FloatVectorProperty(
        name="View Location",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    view_rotation: bpy.props.FloatVectorProperty(
        name="View Rotation",
        size=4,
        default=(1.0, 0.0, 0.0, 0.0)
    )
    view_perspective: bpy.props.StringProperty(
        name="Perspective",
        default="PERSP"
    )
    # Store view_matrix for accurate restoration (16 floats for 4x4 matrix)
    view_matrix: bpy.props.FloatVectorProperty(
        name="View Matrix",
        size=16,
        default=(1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
    )
    # SVPT state
    svpt_enabled: bpy.props.BoolProperty(name="SVPT Enabled", default=False)
    lens_zoom_enabled: bpy.props.BoolProperty(name="Lens Zoom", default=False)
    lens_zoom_backend: bpy.props.StringProperty(name="Backend", default="VIEWPORT")
    # Camera object matrix (for CAMERA backend)
    camera_matrix: bpy.props.FloatVectorProperty(
        name="Camera Matrix",
        size=16,
        default=(1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1)
    )


def update_enabled(self, context):
    r3d, space = get_r3d(context)
    if not r3d or not space:
        return

    if self.enabled:
        if not self.is_initialized:
            self.saved_lens = space.lens
            self.saved_distance = r3d.view_distance
            self.is_initialized = True

        self.manual_lens = space.lens
        _svpt_state["virtual_lens"] = space.lens
        _svpt_state["lens_zoom_ref_dist"] = r3d.view_distance
        _svpt_state["lens_zoom_anchor_lens"] = space.lens
        _svpt_state["lens_zoom_anchor_dist"] = r3d.view_distance
        if self.lens_zoom and self.lens_zoom_backend == 'CAMERA':
            activate_camera_backend(context)

    else:
        if _svpt_state["camera_backend_active"]:
            deactivate_camera_backend(context)
        space.lens = self.saved_lens
        r3d.view_distance = self.saved_distance
        self.is_initialized = False
        _svpt_state["virtual_lens"] = None
        _svpt_state["lens_zoom_ref_dist"] = None
        _svpt_state["lens_zoom_anchor_lens"] = None
        _svpt_state["lens_zoom_anchor_dist"] = None
        _svpt_state["camera_prev_use_local_camera"] = None
        _svpt_state["camera_prev_local_camera_name"] = None
        _svpt_state["camera_prev_lock_camera"] = None


def update_lens_zoom(self, context):
    r3d, space = get_r3d(context)
    if not r3d or not space or not self.enabled:
        return

    if self.lens_zoom:
        _svpt_state["virtual_lens"] = space.lens
        _svpt_state["lens_zoom_ref_dist"] = r3d.view_distance
        _svpt_state["lens_zoom_anchor_lens"] = space.lens
        _svpt_state["lens_zoom_anchor_dist"] = r3d.view_distance
        _svpt_state["camera_zoom_factor"] = 1.0
        _svpt_state["camera_initial_lens"] = space.lens
        _svpt_state["camera_initial_distance"] = r3d.view_distance
        if self.lens_zoom_backend == 'CAMERA':
            activate_camera_backend(context)
    else:
        if _svpt_state["camera_backend_active"]:
            deactivate_camera_backend(context)
        _svpt_state["virtual_lens"] = None
        _svpt_state["lens_zoom_ref_dist"] = None
        _svpt_state["lens_zoom_anchor_lens"] = None
        _svpt_state["lens_zoom_anchor_dist"] = None
        _svpt_state["camera_prev_use_local_camera"] = None
        _svpt_state["camera_prev_local_camera_name"] = None
        _svpt_state["camera_prev_lock_camera"] = None


def update_lens_zoom_backend(self, context):
    r3d, space = get_r3d(context)
    if not r3d or not space or not self.enabled or not self.lens_zoom:
        return

    _svpt_state["virtual_lens"] = space.lens
    _svpt_state["lens_zoom_ref_dist"] = r3d.view_distance
    _svpt_state["lens_zoom_anchor_lens"] = space.lens
    _svpt_state["lens_zoom_anchor_dist"] = r3d.view_distance
    _svpt_state["camera_zoom_factor"] = 1.0
    _svpt_state["camera_initial_lens"] = space.lens
    _svpt_state["camera_initial_distance"] = r3d.view_distance

    if self.lens_zoom_backend == 'CAMERA':
        activate_camera_backend(context)
    elif _svpt_state["camera_backend_active"]:
        deactivate_camera_backend(context)


def update_manual_lens(self, context):
    r3d, space = get_r3d(context)
    if space and self.enabled:
        space.lens = self.manual_lens
        _svpt_state["virtual_lens"] = self.manual_lens
        _svpt_state["camera_zoom_factor"] = 1.0
        _svpt_state["camera_initial_lens"] = self.manual_lens
        if self.lens_zoom and self.lens_zoom_backend == 'CAMERA':
            cam_obj = activate_camera_backend(context)
            if cam_obj:
                cam_obj.data.lens = self.manual_lens
        if r3d:
            _svpt_state["lens_zoom_ref_dist"] = r3d.view_distance
            _svpt_state["camera_initial_distance"] = r3d.view_distance
            _svpt_state["lens_zoom_anchor_lens"] = self.manual_lens
            _svpt_state["lens_zoom_anchor_dist"] = r3d.view_distance




class SVPT_Settings(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Enabled",
        description="Enable or disable SVPT zoom behavior",
        default=False,
        update=update_enabled,
    )

    lens_zoom: bpy.props.BoolProperty(
        name="Lens Zoom",
        description="Use lens/FOV-based zoom for stable perspective behavior",
        default=True,
        update=update_lens_zoom,
    )

    lens_zoom_backend: bpy.props.EnumProperty(
        name="Lens Zoom Backend",
        description="Select where lens zoom is calculated",
        items=[
            ('VIEWPORT', "Viewport", "Use 3D View lens with SVPT handoff behavior"),
            ('CAMERA', "Scene Camera", "Switch to scene camera view and use camera optics"),
        ],
        default='VIEWPORT',
        update=update_lens_zoom_backend,
    )


    use_mouse_pivot: bpy.props.BoolProperty(
        name="Mouse Pivot",
        description="Zoom around the surface under the mouse cursor when possible",
        default=True
    )

    smooth_scroll: bpy.props.BoolProperty(
        name="Smooth Scroll",
        description="Enable smooth inertia-based scroll zoom",
        default=True
    )

    speed: bpy.props.FloatProperty(default=0.05)


    manual_lens: bpy.props.FloatProperty(
        name="Manual Lens",
        description="Set viewport lens directly while SVPT is enabled",
        default=85.0,
        update=update_manual_lens
    )

    saved_lens: bpy.props.FloatProperty(default=50.0)
    saved_distance: bpy.props.FloatProperty(default=1.0)
    is_initialized: bpy.props.BoolProperty(default=False)


def update_active_bookmark(self, context):
    # When active bookmark changes, restore it automatically
    if len(self.bookmarks) > 0 and self.active_index < len(self.bookmarks):
        # Call restore operator
        bpy.ops.view3d.svpt_restore_view_bookmark(index=self.active_index)


class SVPT_ViewBookmarkCollection(bpy.types.PropertyGroup):
    # Collection of view bookmarks stored in Scene (persistent)
    bookmarks: bpy.props.CollectionProperty(type=SVPT_ViewBookmark)
    active_index: bpy.props.IntProperty(
        name="Active Bookmark",
        default=0,
        update=update_active_bookmark
    )

