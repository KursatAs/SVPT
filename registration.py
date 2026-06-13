import bpy

from .hud import draw_hud
from .operators import (
    VIEW3D_OT_svpt_zoom,
    VIEW3D_OT_svpt_zoom_drag,
    VIEW3D_OT_svpt_scroll_zoom,
    VIEW3D_OT_svpt_add_view_bookmark,
    VIEW3D_OT_svpt_remove_view_bookmark,
    VIEW3D_OT_svpt_restore_view_bookmark,
)
from .preferences import SVPT_Preferences
from .properties import SVPT_Settings, SVPT_ViewBookmark, SVPT_ViewBookmarkCollection
from .state import _svpt_state
from .ui import VIEW3D_PT_svpt, SVPT_UL_view_bookmarks
from .utils import deactivate_camera_backend


addon_keymaps = []
_draw_handle = None

# Deferred initialization: set manual_lens to current viewport focal length.
def _init_manual_lens():
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            bpy.context.window_manager.svpt_settings.manual_lens = space.lens
                            return
    except Exception:
        pass


def register():
    global _draw_handle

    bpy.utils.register_class(SVPT_Preferences)
    bpy.utils.register_class(SVPT_ViewBookmark)
    bpy.utils.register_class(SVPT_ViewBookmarkCollection)
    bpy.utils.register_class(SVPT_Settings)
    bpy.types.WindowManager.svpt_settings = bpy.props.PointerProperty(type=SVPT_Settings)
    bpy.types.Scene.svpt_view_bookmarks = bpy.props.PointerProperty(type=SVPT_ViewBookmarkCollection)

    # Defer initialization to after Blender context is fully available
    bpy.app.timers.register(_init_manual_lens, first_interval=0.1)

    bpy.utils.register_class(VIEW3D_OT_svpt_zoom)
    bpy.utils.register_class(VIEW3D_OT_svpt_zoom_drag)
    bpy.utils.register_class(VIEW3D_OT_svpt_scroll_zoom)
    bpy.utils.register_class(VIEW3D_OT_svpt_add_view_bookmark)
    bpy.utils.register_class(VIEW3D_OT_svpt_remove_view_bookmark)
    bpy.utils.register_class(VIEW3D_OT_svpt_restore_view_bookmark)
    bpy.utils.register_class(SVPT_UL_view_bookmarks)
    bpy.utils.register_class(VIEW3D_PT_svpt)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        for key, d, ctrl, shift in [
            ('WHEELINMOUSE', 1, False, False),
            ('WHEELINMOUSE', 1, True, False),
            ('WHEELINMOUSE', 1, False, True),
            ('WHEELINMOUSE', 1, True, True),
            ('WHEELOUTMOUSE', -1, False, False),
            ('WHEELOUTMOUSE', -1, True, False),
            ('WHEELOUTMOUSE', -1, False, True),
            ('WHEELOUTMOUSE', -1, True, True),
            ('NUMPAD_PLUS', 1, False, False),
            ('NUMPAD_PLUS', 1, True, False),
            ('NUMPAD_PLUS', 1, False, True),
            ('NUMPAD_PLUS', 1, True, True),
            ('NUMPAD_MINUS', -1, False, False),
            ('NUMPAD_MINUS', -1, True, False),
            ('NUMPAD_MINUS', -1, False, True),
            ('NUMPAD_MINUS', -1, True, True),
        ]:
            kmi = km.keymap_items.new("view3d.svpt_scroll_zoom", key, 'PRESS', ctrl=ctrl, shift=shift)
            kmi.properties.delta = d

        km.keymap_items.new("view3d.svpt_zoom_drag", 'MIDDLEMOUSE', 'PRESS', ctrl=True, shift=False)
        km.keymap_items.new("view3d.svpt_zoom_drag", 'MIDDLEMOUSE', 'PRESS', ctrl=True, shift=True)
        km.keymap_items.new("view3d.svpt_zoom_drag", 'RIGHTMOUSE', 'PRESS', alt=True)

        addon_keymaps.append(km)

    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        draw_hud, (), 'WINDOW', 'POST_PIXEL'
    )


def unregister():
    global _draw_handle

    if _svpt_state["camera_backend_active"]:
        deactivate_camera_backend(bpy.context)

    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)

    bpy.utils.unregister_class(VIEW3D_PT_svpt)
    bpy.utils.unregister_class(SVPT_UL_view_bookmarks)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_restore_view_bookmark)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_remove_view_bookmark)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_add_view_bookmark)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_scroll_zoom)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_zoom_drag)
    bpy.utils.unregister_class(VIEW3D_OT_svpt_zoom)

    del bpy.types.Scene.svpt_view_bookmarks
    del bpy.types.WindowManager.svpt_settings
    bpy.utils.unregister_class(SVPT_Settings)
    bpy.utils.unregister_class(SVPT_ViewBookmarkCollection)
    bpy.utils.unregister_class(SVPT_ViewBookmark)
    bpy.utils.unregister_class(SVPT_Preferences)

    if _draw_handle:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')

