import math

import bpy

from .constants import (
    CTRL_SPEED_MULTIPLIER,
    FACTOR_MAX,
    FACTOR_MIN,
    MAX_DIST,
    MAX_LENS,
    MIN_DIST,
    MIN_LENS,
    SHIFT_SPEED_MULTIPLIER,
)
from .state import _svpt_state
from .utils import activate_camera_backend, deactivate_camera_backend, get_mouse_pivot, get_r3d


DRAG_PIXEL_TO_DELTA = 0.08
BLENDER_MAX_LENS = 250.0
ANCHOR_SNAP_LENS_TOLERANCE = 0.5
ANCHOR_SNAP_DIST_TOLERANCE = 0.002


def _apply_camera_lens_zoom(context, lens, delta, effective_speed):
    cam_obj = activate_camera_backend(context)
    if not cam_obj:
        return {'PASS_THROUGH'}

    _r3d, space = get_r3d(context)
    if not space:
        return {'PASS_THROUGH'}

    initial_lens = _svpt_state["camera_initial_lens"]
    initial_distance = _svpt_state["camera_initial_distance"]

    if initial_lens is None:
        initial_lens = lens
        _svpt_state["camera_initial_lens"] = initial_lens

    if initial_distance is None:
        _r3d, _s = get_r3d(context)
        if _r3d:
            initial_distance = _r3d.view_distance
            _svpt_state["camera_initial_distance"] = initial_distance

    prev_zoom_factor = _svpt_state["camera_zoom_factor"]
    factor = math.exp(delta * effective_speed)
    factor = max(FACTOR_MIN, min(FACTOR_MAX, factor))

    new_zoom_factor = prev_zoom_factor * factor
    new_zoom_factor = max(0.1, min(100.0, new_zoom_factor))
    _svpt_state["camera_zoom_factor"] = new_zoom_factor

    new_lens = initial_lens * new_zoom_factor
    new_lens = max(MIN_LENS, min(MAX_LENS, new_lens))

    cam_obj.data.lens = new_lens
    if space:
        space.lens = new_lens

    r3d, _sp = get_r3d(context)
    if r3d and initial_distance:
        new_distance = initial_distance / new_zoom_factor
        new_distance = max(MIN_DIST, min(MAX_DIST, new_distance))
        r3d.view_distance = new_distance

    return {'FINISHED'}


def _apply_svpt_zoom(context, event, delta, use_speed_modifiers=True):
    s = context.window_manager.svpt_settings
    r3d, space = get_r3d(context)

    if not r3d or not s.enabled:
        return {'PASS_THROUGH'}

    dist = r3d.view_distance
    lens = space.lens

    effective_speed = s.speed
    if use_speed_modifiers:
        if event.ctrl:
            effective_speed *= CTRL_SPEED_MULTIPLIER
        elif event.shift:
            effective_speed *= SHIFT_SPEED_MULTIPLIER

    factor = math.exp(delta * effective_speed)
    factor = max(FACTOR_MIN, min(FACTOR_MAX, factor))

    pivot = None
    if s.use_mouse_pivot:
        pivot = get_mouse_pivot(context, event)

    if pivot is None:
        pivot = r3d.view_location

    if s.lens_zoom:
        if s.lens_zoom_backend == 'CAMERA':
            return _apply_camera_lens_zoom(context, lens, delta, effective_speed)

        if _svpt_state["camera_backend_active"]:
            deactivate_camera_backend(context)

        prev_vl = _svpt_state["virtual_lens"]
        ref_dist = _svpt_state["lens_zoom_ref_dist"]
        anchor_lens = _svpt_state["lens_zoom_anchor_lens"]
        anchor_dist = _svpt_state["lens_zoom_anchor_dist"]

        if prev_vl is None:
            prev_vl = max(MIN_LENS, min(MAX_LENS, lens))
            _svpt_state["virtual_lens"] = prev_vl

        if ref_dist is None:
            ref_dist = max(MIN_DIST, min(MAX_DIST, dist))
            _svpt_state["lens_zoom_ref_dist"] = ref_dist

        if anchor_lens is None or anchor_dist is None:
            anchor_lens = prev_vl
            anchor_dist = ref_dist
            _svpt_state["lens_zoom_anchor_lens"] = anchor_lens
            _svpt_state["lens_zoom_anchor_dist"] = anchor_dist

        # If lens was edited externally while under the 250mm cap, resync the canonical state.
        if space.lens < BLENDER_MAX_LENS and abs(space.lens - prev_vl) > 1e-6:
            prev_vl = max(MIN_LENS, min(MAX_LENS, space.lens))
            _svpt_state["virtual_lens"] = prev_vl
            ref_dist = max(MIN_DIST, min(MAX_DIST, r3d.view_distance))
            _svpt_state["lens_zoom_ref_dist"] = ref_dist

        fov = 2.0 * math.atan(36.0 / (2.0 * prev_vl))
        fov -= delta * effective_speed
        fov = max(0.005, min(3.1, fov))
        new_vl = 36.0 / (2.0 * math.tan(fov / 2.0))
        new_vl = max(MIN_LENS, min(MAX_LENS, new_vl))
        _svpt_state["virtual_lens"] = new_vl

        if new_vl <= BLENDER_MAX_LENS:
            space.lens = new_vl
            r3d.view_distance = ref_dist
        else:
            space.lens = BLENDER_MAX_LENS
            r3d.view_distance = max(MIN_DIST, min(MAX_DIST, ref_dist * (BLENDER_MAX_LENS / new_vl)))

        # Snap back to the initial lens-zoom anchor when zooming out near start values.
        if (
            delta < 0.0
            and new_vl <= BLENDER_MAX_LENS
            and abs(new_vl - anchor_lens) <= ANCHOR_SNAP_LENS_TOLERANCE
            and abs(r3d.view_distance - anchor_dist) <= ANCHOR_SNAP_DIST_TOLERANCE
        ):
            _svpt_state["virtual_lens"] = anchor_lens
            space.lens = anchor_lens
            r3d.view_distance = anchor_dist

    else:
        if _svpt_state["camera_backend_active"]:
            deactivate_camera_backend(context)

        new_dist = dist / factor
        new_dist = max(MIN_DIST, min(MAX_DIST, new_dist))

        offset = r3d.view_location - pivot
        new_offset = offset / factor
        r3d.view_location = pivot + new_offset

        r3d.view_distance = new_dist

    return {'FINISHED'}


SCROLL_DAMPING = 0.78        # velocity multiplied each tick (lower = faster stop)
SCROLL_TIMER_INTERVAL = 0.016  # ~60fps timer


class VIEW3D_OT_svpt_scroll_zoom(bpy.types.Operator):
    # Smooth inertia-based scroll zoom, not so sure it's completed yet!!
    bl_idname = "view3d.svpt_scroll_zoom"
    bl_label = "SVPT Scroll Zoom"

    delta: bpy.props.FloatProperty()

    def invoke(self, context, event):
        s = context.window_manager.svpt_settings
        r3d, _ = get_r3d(context)
        if not r3d or not s.enabled:
            return {'PASS_THROUGH'}

        # If smooth scroll is disabled, use instant zoom
        if not s.smooth_scroll:
            return _apply_svpt_zoom(context, event, self.delta)

        # Accumulate velocity
        _svpt_state["scroll_velocity"] += self.delta
        _svpt_state["scroll_ctrl"] = event.ctrl
        _svpt_state["scroll_shift"] = event.shift

        # Start modal only if not already running
        if not _svpt_state["scroll_modal_running"]:
            _svpt_state["scroll_modal_running"] = True
            self._timer = context.window_manager.event_timer_add(
                SCROLL_TIMER_INTERVAL, window=context.window
            )
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        return {'FINISHED'}

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        velocity = _svpt_state["scroll_velocity"]

        if abs(velocity) < 0.001:
            # Done — stop modal
            _svpt_state["scroll_velocity"] = 0.0
            _svpt_state["scroll_modal_running"] = False
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        # Apply a small step from current velocity
        step = velocity * (1.0 - SCROLL_DAMPING)
        _svpt_state["scroll_velocity"] *= SCROLL_DAMPING

        # Build a fake event-like object for modifier keys
        class _FakeEvent:
            ctrl = _svpt_state["scroll_ctrl"]
            shift = _svpt_state["scroll_shift"]
            mouse_region_x = event.mouse_region_x
            mouse_region_y = event.mouse_region_y

        _apply_svpt_zoom(context, _FakeEvent(), step)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        _svpt_state["scroll_velocity"] = 0.0
        _svpt_state["scroll_modal_running"] = False
        if hasattr(self, '_timer'):
            context.window_manager.event_timer_remove(self._timer)


class VIEW3D_OT_svpt_zoom(bpy.types.Operator):
    bl_idname = "view3d.svpt_zoom"
    bl_label = "SVPT Zoom"

    delta: bpy.props.FloatProperty()

    def invoke(self, context, event):
        self.event = event
        return self.execute(context)

    def execute(self, context):
        return _apply_svpt_zoom(context, self.event, self.delta)


class VIEW3D_OT_svpt_zoom_drag(bpy.types.Operator):
    bl_idname = "view3d.svpt_zoom_drag"
    bl_label = "SVPT Zoom Drag"

    def invoke(self, context, event):
        s = context.window_manager.svpt_settings
        r3d, _space = get_r3d(context)

        if not r3d or not s.enabled:
            return {'PASS_THROUGH'}

        self.trigger_button = event.type
        self.last_mouse_y = event.mouse_y
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        s = context.window_manager.svpt_settings
        r3d, _space = get_r3d(context)

        if not r3d or not s.enabled:
            return {'PASS_THROUGH'}

        if event.type == 'ESC':
            return {'CANCELLED'}

        if event.type == self.trigger_button and event.value == 'RELEASE':
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            dy = event.mouse_y - self.last_mouse_y
            self.last_mouse_y = event.mouse_y
            if dy:
                delta = dy * DRAG_PIXEL_TO_DELTA
                _apply_svpt_zoom(context, event, delta, use_speed_modifiers=False)

        return {'RUNNING_MODAL'}


class VIEW3D_OT_svpt_add_view_bookmark(bpy.types.Operator):
    # Add current view as a bookmark
    bl_idname = "view3d.svpt_add_view_bookmark"
    bl_label = "Add View Bookmark"
    
    def execute(self, context):
        s = context.window_manager.svpt_settings
        r3d, space = get_r3d(context)
        
        if not r3d or not space:
            self.report({'WARNING'}, "No active 3D viewport")
            return {'CANCELLED'}
        
        # Get bookmarks from scene (persistent storage)
        bookmarks = context.scene.svpt_view_bookmarks
        
        # Create new bookmark
        bookmark = bookmarks.bookmarks.add()
        bookmark.name = f"View {len(bookmarks.bookmarks)}"
        bookmark.lens = space.lens
        bookmark.distance = r3d.view_distance
        
        # Copy view_location (3D vector)
        bookmark.view_location[0] = r3d.view_location[0]
        bookmark.view_location[1] = r3d.view_location[1]
        bookmark.view_location[2] = r3d.view_location[2]
        
        # Copy view_rotation (quaternion - 4D)
        bookmark.view_rotation[0] = r3d.view_rotation[0]
        bookmark.view_rotation[1] = r3d.view_rotation[1]
        bookmark.view_rotation[2] = r3d.view_rotation[2]
        bookmark.view_rotation[3] = r3d.view_rotation[3]
        
        bookmark.view_perspective = r3d.view_perspective
        
        # Save view_matrix for accurate restoration
        view_matrix = r3d.view_matrix
        for i in range(4):
            for j in range(4):
                bookmark.view_matrix[i*4 + j] = view_matrix[i][j]

        # Save SVPT state
        bookmark.svpt_enabled = s.enabled
        bookmark.lens_zoom_enabled = s.lens_zoom
        bookmark.lens_zoom_backend = s.lens_zoom_backend
        
        # If CAMERA backend is active, save camera matrix
        if s.lens_zoom and s.lens_zoom_backend == 'CAMERA' and _svpt_state["camera_backend_active"]:
            cam_obj_name = _svpt_state["camera_object_name"]
            if cam_obj_name:
                cam_obj = bpy.data.objects.get(cam_obj_name)
                if cam_obj:
                    # Flatten 4x4 matrix to 16 floats
                    matrix = cam_obj.matrix_world
                    for i in range(4):
                        for j in range(4):
                            bookmark.camera_matrix[i*4 + j] = matrix[i][j]
        
        # Set as active
        bookmarks.active_index = len(bookmarks.bookmarks) - 1

        self.report({'INFO'}, f"View '{bookmark.name}' saved (Backend: {bookmark.lens_zoom_backend})")
        return {'FINISHED'}


class VIEW3D_OT_svpt_remove_view_bookmark(bpy.types.Operator):
    # Remove selected view bookmark
    bl_idname = "view3d.svpt_remove_view_bookmark"
    bl_label = "Remove View Bookmark"
    
    @classmethod
    def poll(cls, context):
        bookmarks = context.scene.svpt_view_bookmarks
        return len(bookmarks.bookmarks) > 0

    def execute(self, context):
        bookmarks = context.scene.svpt_view_bookmarks

        if bookmarks.active_index < len(bookmarks.bookmarks):
            name = bookmarks.bookmarks[bookmarks.active_index].name
            bookmarks.bookmarks.remove(bookmarks.active_index)

            # Adjust active index
            if bookmarks.active_index >= len(bookmarks.bookmarks):
                bookmarks.active_index = max(0, len(bookmarks.bookmarks) - 1)

            self.report({'INFO'}, f"View '{name}' removed")
        
        return {'FINISHED'}


class VIEW3D_OT_svpt_restore_view_bookmark(bpy.types.Operator):
    # Restore view from bookmark
    bl_idname = "view3d.svpt_restore_view_bookmark"
    bl_label = "Restore View Bookmark"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        s = context.window_manager.svpt_settings
        r3d, space = get_r3d(context)
        
        if not r3d or not space:
            self.report({'WARNING'}, "No active 3D viewport")
            return {'CANCELLED'}
        
        # Get bookmarks from scene
        bookmarks = context.scene.svpt_view_bookmarks

        if self.index >= len(bookmarks.bookmarks):
            return {'CANCELLED'}
        
        bookmark = bookmarks.bookmarks[self.index]

        # Restore SVPT state first
        s.enabled = bookmark.svpt_enabled
        s.lens_zoom = bookmark.lens_zoom_enabled
        s.lens_zoom_backend = bookmark.lens_zoom_backend
        
        # Restore lens and distance first
        space.lens = bookmark.lens
        r3d.view_distance = bookmark.distance
        r3d.view_perspective = bookmark.view_perspective
        
        # If restoring CAMERA backend, activate it FIRST and restore camera matrix
        if bookmark.lens_zoom_enabled and bookmark.lens_zoom_backend == 'CAMERA':
            import mathutils
            cam_obj = activate_camera_backend(context)
            if cam_obj:
                # Restore camera matrix from flattened array
                matrix = mathutils.Matrix()
                for i in range(4):
                    for j in range(4):
                        matrix[i][j] = bookmark.camera_matrix[i*4 + j]
                cam_obj.matrix_world = matrix
                cam_obj.data.lens = bookmark.lens

                # Ensure camera is set for rendering!!!
                context.scene.camera = cam_obj
                cam_obj.hide_render = False
                
                # Force update dependency graph for render
                context.view_layer.update()
                
                # Ensure viewport is in camera view
                r3d.view_perspective = 'CAMERA'
        else:
            # For VIEWPORT backend, restore view using view_matrix
            import mathutils
            view_matrix = mathutils.Matrix()
            for i in range(4):
                for j in range(4):
                    view_matrix[i][j] = bookmark.view_matrix[i*4 + j]

            r3d.view_matrix = view_matrix

        # Force viewport update
        context.area.tag_redraw()
        
        self.report({'INFO'}, f"View '{bookmark.name}' restored (Backend: {bookmark.lens_zoom_backend})")
        return {'FINISHED'}



