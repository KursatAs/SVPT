import bpy


class SVPT_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    hud_x: bpy.props.IntProperty(
        name="HUD X",
        description="Horizontal position of the HUD on screen",
        default=20,
        min=0,
        max=2000,
    )

    hud_y: bpy.props.IntProperty(
        name="HUD Y",
        description="Vertical position of the HUD bottom line on screen",
        default=40,
        min=0,
        max=2000,
    )

    show_zoom_percentage: bpy.props.BoolProperty(
        name="Show Zoom Percentage",
        description="Display zoom level as percentage in viewport",
        default=True
    )

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="HUD Position:")
        row = box.row()
        row.prop(self, "hud_x")
        row.prop(self, "hud_y")
        
        box = layout.box()
        box.label(text="Viewport Overlays:")
        box.prop(self, "show_zoom_percentage")

