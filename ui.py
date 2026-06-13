import bpy


# UIList for view bookmarks
class SVPT_UL_view_bookmarks(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='CAMERA_DATA')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CAMERA_DATA')


class VIEW3D_PT_svpt(bpy.types.Panel):
    bl_label = "SVPT"
    bl_idname = "VIEW3D_PT_svpt"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SVPT'

    def draw(self, context):
        s = context.window_manager.svpt_settings
        layout = self.layout

        layout.prop(s, "enabled")
        layout.prop(s, "lens_zoom")
        if s.lens_zoom:
            layout.prop(s, "lens_zoom_backend")
        layout.prop(s, "use_mouse_pivot")
        layout.prop(s, "smooth_scroll")

        layout.separator()
        layout.prop(s, "manual_lens")

        # View Bookmarks section
        layout.separator()
        box = layout.box()
        row = box.row()
        row.label(text="View Bookmarks", icon='BOOKMARKS')

        # Get bookmarks from scene (persistent)
        bookmarks = context.scene.svpt_view_bookmarks

        row = box.row()
        row.template_list(
            "SVPT_UL_view_bookmarks",
            "",
            bookmarks,
            "bookmarks",
            bookmarks,
            "active_index",
            rows=3
        )

        col = row.column(align=True)
        col.operator("view3d.svpt_add_view_bookmark", icon='ADD', text="")
        col.operator("view3d.svpt_remove_view_bookmark", icon='REMOVE', text="")



