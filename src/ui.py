import bpy

if __package__:
    from .utils import is_ffmpeg_available
else:
    from utils import is_ffmpeg_available


class RENDER_PT_animated_export(bpy.types.Panel):
    """Panel in the Output properties tab to configure animated GIF and WebP exports."""
    bl_label = "Animated Image Export"
    bl_idname = "RENDER_PT_animated_export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'output'
    bl_order = 10

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.animated_image_settings

        # Check FFmpeg availability
        if not is_ffmpeg_available():
            box = layout.box()
            box.alert = True
            col = box.column(align=True)
            col.label(text="FFmpeg not found!", icon='ERROR')
            col.label(text="Please install FFmpeg or bundle imageio-ffmpeg.")
            return

        # Format selector (side-by-side segmented buttons)
        row = layout.row(align=True)
        row.prop(settings, "format", expand=True)

        layout.separator()

        # Destination file path
        box = layout.box()
        box.label(text="Output Destination:", icon='FILE_FOLDER')
        col = box.column(align=True)
        col.prop(settings, "filepath", text="File Path")

        layout.separator()

        # Format-specific profile & options
        if settings.format == 'WEBP':
            box = layout.box()
            box.label(text="WebP Settings:", icon='FILE_IMAGE')
            col = box.column(align=True)
            col.prop(settings, "webp_profile")

            if settings.webp_profile == 'CUSTOM':
                col.prop(settings, "webp_lossless")
                if not settings.webp_lossless:
                    col.prop(settings, "webp_quality")
                col.prop(settings, "webp_preset")
                col.prop(settings, "webp_compression")
            else:
                info_row = box.row()
                info_row.alignment = 'CENTER'
                if settings.webp_profile == 'BALANCED':
                    info_row.label(text="Quality: 75% | Lossy | Balanced size", icon='INFO')
                elif settings.webp_profile == 'HIGH':
                    info_row.label(text="Quality: 90% | Lossy | High fidelity", icon='INFO')
                elif settings.webp_profile == 'LOSSLESS':
                    info_row.label(text="Lossless | 100% pixel-perfect", icon='INFO')
                elif settings.webp_profile == 'COMPACT':
                    info_row.label(text="Quality: 50% | Lossy | Small file size", icon='INFO')
        else:  # GIF
            box = layout.box()
            box.label(text="GIF Settings:", icon='IMAGE_DATA')
            col = box.column(align=True)
            col.prop(settings, "gif_quality")

            info_row = box.row()
            info_row.alignment = 'CENTER'
            if settings.gif_quality == 'HIGH':
                info_row.label(text="2-pass palette generation (diff mode)", icon='INFO')
            elif settings.gif_quality == 'MEDIUM':
                info_row.label(text="Single-pass palettegen/paletteuse", icon='INFO')
            else:
                info_row.label(text="Fast direct conversion (standard palette)", icon='INFO')

        # General loop & resolution settings
        box = layout.box()
        box.label(text="General Settings:", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(settings, "scale")
        col.prop(settings, "loop_count")

        # Action Render button
        layout.separator()
        col = layout.column()
        col.scale_y = 1.3
        format_name = "WebP" if settings.format == 'WEBP' else "GIF"
        col.operator(
            "render.animated_image",
            text=f"Render Animated {format_name}",
            icon='RENDER_ANIMATION'
        )

        if settings.last_status:
            box = layout.box()
            status_icon = 'ERROR' if "failed" in settings.last_status.lower() or "error" in settings.last_status.lower() else 'CHECKMARK'
            box.label(text=settings.last_status, icon=status_icon)



def menu_func(self, context):
    self.layout.operator(
        "render.animated_image",
        text="Render Animated Image (GIF/WebP)",
        icon='RENDER_ANIMATION'
    )


classes = (
    RENDER_PT_animated_export,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_render.append(menu_func)


def unregister():
    try:
        bpy.types.TOPBAR_MT_render.remove(menu_func)
    except Exception:
        pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
