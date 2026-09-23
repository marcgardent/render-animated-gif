import os
import shutil
import tempfile
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, IntProperty, BoolProperty

if __package__:
    from .utils import get_ffmpeg_binary, ensure_extension
    from .converters import convert_video_to_animated_image
else:
    from utils import get_ffmpeg_binary, ensure_extension
    from converters import convert_video_to_animated_image


class AnimatedRenderBase:
    """Base mixin class implementing animated export operator logic."""
    bl_options = {'PRESET', 'REGISTER'}

    filepath: StringProperty(
        name="File Path",
        description="Path to save the exported animated image",
        subtype='FILE_PATH',
        default="//render.webp",
    )

    filter_glob: StringProperty(
        default="*.webp;*.gif",
        options={'HIDDEN'},
    )

    format: EnumProperty(
        name="Format",
        description="Choose animated image format",
        items=[
            ('WEBP', "WebP", "Modern animated WebP (24-bit color + alpha, smaller file size)"),
            ('GIF', "GIF", "Classic animated GIF (palette-based 256 colors)"),
        ],
        default='WEBP',
    )

    scale: IntProperty(
        name="Resolution %",
        description="Renders by a percentage of the current scene resolution",
        default=100,
        min=1,
        max=100,
        subtype='PERCENTAGE',
    )

    loop_count: IntProperty(
        name="Loop Count",
        description="Number of animation loops (0 = Infinite loop)",
        default=0,
        min=0,
        max=65535,
    )

    # GIF options
    gif_quality: EnumProperty(
        name="GIF Profile",
        description="Quality preset for animated GIF",
        items=[
            ('HIGH', "High (2-Pass)", "Two-pass palette generation with Bayer dithering"),
            ('MEDIUM', "Medium (1-Pass)", "Single-pass split palette generation"),
            ('LOW', "Low (Fast)", "Fast direct conversion without custom palette"),
        ],
        default='MEDIUM',
    )

    # WebP options
    webp_profile: EnumProperty(
        name="WebP Profile",
        description="Encoding profile for WebP",
        items=[
            ('BALANCED', "Balanced", "Lossy 75% quality, balanced size and quality"),
            ('HIGH', "High Quality", "Lossy 90% quality, low compression artifacts"),
            ('LOSSLESS', "Lossless", "100% mathematically lossless, pixel perfect"),
            ('COMPACT', "Compact", "Lossy 50% quality, smaller file size"),
            ('CUSTOM', "Custom", "Manual control over lossless, quality, and preset"),
        ],
        default='BALANCED',
    )

    webp_lossless: BoolProperty(
        name="Lossless",
        description="Enable lossless WebP encoding",
        default=False,
    )

    webp_quality: IntProperty(
        name="Quality",
        description="WebP lossy compression quality (0-100)",
        default=75,
        min=0,
        max=100,
        subtype='PERCENTAGE',
    )

    webp_preset: EnumProperty(
        name="Preset Tuning",
        description="Tune the WebP encoder for specific image types",
        items=[
            ('default', "Default", "Default libwebp configuration"),
            ('picture', "Picture", "Digital pictures, portraits, indoor scenes"),
            ('photo', "Photo", "Outdoor photographs with natural lighting"),
            ('drawing', "Drawing", "Hand or line drawings with high contrast"),
            ('icon', "Icon", "Small colorful graphics and icons"),
            ('text', "Text", "Text-heavy images"),
        ],
        default='default',
    )

    webp_compression: IntProperty(
        name="Compression Effort",
        description="Compression effort (0 = fastest, 6 = smallest file size)",
        default=4,
        min=0,
        max=6,
    )

    def invoke(self, context, event):
        # Sync initial state from scene settings
        if hasattr(context.scene, "animated_image_settings"):
            s = context.scene.animated_image_settings
            self.format = s.format
            self.scale = s.scale
            self.loop_count = s.loop_count
            self.gif_quality = s.gif_quality
            self.webp_profile = s.webp_profile
            self.webp_lossless = s.webp_lossless
            self.webp_quality = s.webp_quality
            self.webp_preset = s.webp_preset
            self.webp_compression = s.webp_compression

        # Suggest default filepath based on scene render path or default
        base_path = context.scene.render.filepath or "//render"
        self.filepath = ensure_extension(base_path, self.format)
        self.filter_glob = "*.webp" if self.format == 'WEBP' else "*.gif"

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def check(self, context):
        """Update file extension and filter if user changes format in file dialog."""
        target_ext = ".webp" if self.format == 'WEBP' else ".gif"
        current_ext = ".webp" if self.filepath.lower().endswith(".webp") else (
            ".gif" if self.filepath.lower().endswith(".gif") else ""
        )
        changed = False
        if current_ext and current_ext != target_ext:
            self.filepath = self.filepath[:-len(current_ext)] + target_ext
            self.filter_glob = f"*{target_ext}"
            changed = True
        elif not current_ext:
            self.filepath = self.filepath + target_ext
            self.filter_glob = f"*{target_ext}"
            changed = True
        return changed

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Format switcher
        row = layout.row(align=True)
        row.prop(self, "format", expand=True)

        if self.format == 'WEBP':
            box = layout.box()
            box.label(text="WebP Options:", icon='FILE_IMAGE')
            col = box.column(align=True)
            col.prop(self, "webp_profile")
            if self.webp_profile == 'CUSTOM':
                col.prop(self, "webp_lossless")
                if not self.webp_lossless:
                    col.prop(self, "webp_quality")
                col.prop(self, "webp_preset")
                col.prop(self, "webp_compression")
        else:
            box = layout.box()
            box.label(text="GIF Options:", icon='IMAGE_DATA')
            col = box.column(align=True)
            col.prop(self, "gif_quality")

        box = layout.box()
        box.label(text="General Settings:", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(self, "scale")
        col.prop(self, "loop_count")

    def execute(self, context):
        # Sync back to scene settings for consistency
        if hasattr(context.scene, "animated_image_settings"):
            s = context.scene.animated_image_settings
            s.format = self.format
            s.scale = self.scale
            s.loop_count = self.loop_count
            s.gif_quality = self.gif_quality
            s.webp_profile = self.webp_profile
            s.webp_lossless = self.webp_lossless
            s.webp_quality = self.webp_quality
            s.webp_preset = self.webp_preset
            s.webp_compression = self.webp_compression

        ffmpeg_exe = get_ffmpeg_binary()
        if not ffmpeg_exe:
            self.report({'ERROR'}, "FFmpeg not found. Please install FFmpeg or bundled imageio-ffmpeg.")
            return {'CANCELLED'}

        scene = context.scene

        # Save original render settings
        original_filepath = scene.render.filepath
        original_media_type = getattr(scene.render.image_settings, "media_type", None)
        original_format = scene.render.image_settings.file_format
        original_use_overwrite = scene.render.use_overwrite
        original_use_file_extension = scene.render.use_file_extension
        original_res_percentage = scene.render.resolution_percentage
        original_ffmpeg_codec = scene.render.ffmpeg.codec
        original_ffmpeg_format = scene.render.ffmpeg.format

        temp_dir = tempfile.mkdtemp(prefix="temp_anim_render_")
        temp_video_path = os.path.join(temp_dir, "render.mp4")

        try:
            # Configure temporary render settings
            scene.render.resolution_percentage = self.scale
            if hasattr(scene.render.image_settings, "media_type"):
                scene.render.image_settings.media_type = 'VIDEO'
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.codec = 'H264'
            scene.render.ffmpeg.format = 'MPEG4'
            scene.render.filepath = temp_video_path
            scene.render.use_overwrite = True
            scene.render.use_file_extension = True

            print(f"Rendering animation to temporary video ({temp_video_path})...")
            bpy.ops.render.render(animation=True)

            # Locate the rendered temporary video file
            if not os.path.exists(temp_video_path):
                candidates = [
                    os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
                    if f.endswith(('.mp4', '.mkv', '.avi'))
                ]
                if candidates:
                    temp_video_path = candidates[0]
                else:
                    self.report({'ERROR'}, "Rendering failed: temporary video file was not generated.")
                    return {'CANCELLED'}

            # Compute output path
            output_path = bpy.path.abspath(self.filepath)
            output_path = ensure_extension(output_path, self.format)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            print(f"Converting video to {self.format} (loop={self.loop_count})...")
            success, err_msg = convert_video_to_animated_image(
                ffmpeg_exe=ffmpeg_exe,
                input_video=temp_video_path,
                output_path=output_path,
                target_format=self.format,
                loop_count=self.loop_count,
                gif_quality=self.gif_quality,
                webp_profile=self.webp_profile,
                webp_lossless=self.webp_lossless,
                webp_quality=self.webp_quality,
                webp_preset=self.webp_preset,
                webp_compression=self.webp_compression,
                temp_dir=temp_dir,
            )

            if not success:
                self.report({'ERROR'}, f"Conversion failed: {err_msg}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Successfully saved animated {self.format} to: {output_path}")
            return {'FINISHED'}

        finally:
            # Restore original render settings
            scene.render.filepath = original_filepath
            if hasattr(scene.render.image_settings, "media_type") and original_media_type is not None:
                scene.render.image_settings.media_type = original_media_type
            scene.render.image_settings.file_format = original_format
            scene.render.use_overwrite = original_use_overwrite
            scene.render.use_file_extension = original_use_file_extension
            scene.render.resolution_percentage = original_res_percentage
            scene.render.ffmpeg.codec = original_ffmpeg_codec
            scene.render.ffmpeg.format = original_ffmpeg_format

            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)


class RENDER_OT_animated_image(Operator, AnimatedRenderBase):
    """Render animation and export as animated WebP or GIF"""
    bl_idname = "render.animated_image"
    bl_label = "Render Animated Image"
    bl_description = "Render animation and export as an animated WebP or GIF loop"


class RENDER_OT_animated_loop(Operator, AnimatedRenderBase):
    """Render animation and export as animated loop (WebP or GIF)"""
    bl_idname = "render.animated_loop"
    bl_label = "Render Animated Loop"
    bl_description = "Render animation and export as an animated WebP or GIF loop"


class RENDER_OT_animation_gif(Operator, AnimatedRenderBase):
    """Legacy compatibility operator: render animation directly as GIF"""
    bl_idname = "render.animation_gif"
    bl_label = "Render Animation as GIF"
    bl_description = "Renders animation into a .GIF image file (legacy operator)"

    format: EnumProperty(
        name="Format",
        items=[('GIF', "GIF", "Classic animated GIF")],
        default='GIF',
    )
    filepath: StringProperty(
        name="File Path",
        subtype='FILE_PATH',
        default="//render.gif",
    )
    filter_glob: StringProperty(
        default="*.gif",
        options={'HIDDEN'},
    )


classes = (
    RENDER_OT_animated_image,
    RENDER_OT_animated_loop,
    RENDER_OT_animation_gif,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
