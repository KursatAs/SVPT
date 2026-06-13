import blf
import bpy

from .utils import get_r3d
from .state import _svpt_state


def draw_hud():
    try:
        context = bpy.context
        s = context.window_manager.svpt_settings
        r3d, space = get_r3d(context)

        if not r3d or not space:
            return

        prefs = bpy.context.preferences.addons[__package__].preferences

        # Draw main HUD
        lines = [
            f"SVPT: {'ON' if s.enabled else 'OFF'}",
            f"Lens: {space.lens:.1f}",
            f"Dist: {r3d.view_distance:.3f}",
        ]

        if s.enabled:
            lines.extend([
                f"Lens Zoom: {'ON' if s.lens_zoom else 'OFF'}",
                f"Backend: {'CAMERA' if s.lens_zoom and s.lens_zoom_backend == 'CAMERA' else 'VIEWPORT'}",
                f"Pivot: {'ON' if s.use_mouse_pivot else 'OFF'}",
                f"Smooth Scroll: {'ON' if s.smooth_scroll else 'OFF'}",
            ])

        hud_x = prefs.hud_x
        hud_y = prefs.hud_y

        font_id = 0
        y = hud_y + 18 * (len(lines) - 1)

        def line(t, color=(1, 1, 1, 1)):
            nonlocal y
            blf.color(font_id, *color)
            blf.position(font_id, hud_x, y, 0)
            blf.draw(font_id, t)
            y -= 18

        for text in lines:
            line(text)

        # Draw zoom percentage overlay
        if prefs.show_zoom_percentage and s.enabled and s.lens_zoom:
            _draw_zoom_percentage(font_id, hud_x, y - 20, space, s)


    except Exception:
        pass


def _draw_zoom_percentage(font_id, x, y, space, settings):
    # Draw zoom percentage indicator
    try:
        # Calculate zoom percentage
        reference_lens = _svpt_state.get("lens_zoom_anchor_lens", 50.0)
        if reference_lens and reference_lens > 0:
            current_lens = space.lens
            zoom_percent = (current_lens / reference_lens) * 100.0

            blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            blf.position(font_id, x, y, 0)
            blf.draw(font_id, f"Zoom: {zoom_percent:.0f}%")
    except Exception:
        pass


