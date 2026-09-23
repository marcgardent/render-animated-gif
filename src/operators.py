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
        description="Path to save the exported animated image (leave empty to use Scene output path)",
        subtype='FILE_PATH',
        options={'PATH_SUPPORTS_BLEND_RELATIVE'},
        default="",
    )

    format: EnumProperty(
        name="Format",
        description="Choose animated image format",
        items=[
            ('AUTO', "Auto", "Use Scene Settings"),
            ('WEBP', "WebP", "Modern animated WebP (24-bit color + alpha, smaller file size)"),
            ('GIF', "GIF", "Classic animated GIF (palette-based 256 colors)"),
        ],
        default='AUTO',
    )

    scale: IntProperty(
        name="Resolution %",
        description="Renders by a percentage of the current scene resolution (0 to use Scene settings)",
        default=0,
        min=0,
        max=100,
        subtype='PERCENTAGE',
    )

    loop_count: IntProperty(
        name="Loop Count",
        description="Number of animation loops (-1 to use Scene settings, 0 = Infinite loop)",
        default=-1,
        min=-1,
        max=65535,
    )

    # GIF options
    gif_quality: EnumProperty(
        name="GIF Profile",
        description="Quality preset for animated GIF",
        items=[
            ('AUTO', "Auto", "Use Scene Settings"),
            ('HIGH', "High (2-Pass)", "Two-pass palette generation with Bayer dithering"),
            ('MEDIUM', "Medium (1-Pass)", "Single-pass split palette generation"),
            ('LOW', "Low (Fast)", "Fast direct conversion without custom palette"),
        ],
        default='AUTO',
    )

    # WebP options
    webp_profile: EnumProperty(
        name="WebP Profile",
        description="Encoding profile for WebP",
        items=[
            ('AUTO', "Auto", "Use Scene Settings"),
            ('BALANCED', "Balanced", "Lossy 75% quality, balanced size and quality"),
            ('HIGH', "High Quality", "Lossy 90% quality, low compression artifacts"),
            ('LOSSLESS', "Lossless", "100% mathematically lossless, pixel perfect"),
            ('COMPACT', "Compact", "Lossy 50% quality, smaller file size"),
            ('CUSTOM', "Custom", "Manual control over lossless, quality, and preset"),
        ],
        default='AUTO',
    )

    webp_lossless: BoolProperty(
        name="Lossless",
        description="Enable lossless WebP encoding",
        default=False,
    )

    webp_quality: IntProperty(
        name="Quality",
        description="WebP lossy compression quality (-1 to use Scene settings, 0-100)",
        default=-1,
        min=-1,
        max=100,
        subtype='PERCENTAGE',
    )

    webp_preset: EnumProperty(
        name="Preset Tuning",
        description="Tune the WebP encoder for specific image types",
        items=[
            ('AUTO', "Auto", "Use Scene Settings"),
            ('default', "Default", "Default libwebp configuration"),
            ('picture', "Picture", "Digital pictures, portraits, indoor scenes"),
            ('photo', "Photo", "Outdoor photographs with natural lighting"),
            ('drawing', "Drawing", "Hand or line drawings with high contrast"),
            ('icon', "Icon", "Small colorful graphics and icons"),
            ('text', "Text", "Text-heavy images"),
        ],
        default='AUTO',
    )

    webp_compression: IntProperty(
        name="Compression Effort",
        description="Compression effort (-1 to use Scene settings, 0 = fastest, 6 = smallest file size)",
        default=-1,
        min=-1,
        max=6,
    )

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        ffmpeg_exe = get_ffmpeg_binary()
        if not ffmpeg_exe:
            self.report({'ERROR'}, "FFmpeg not found. Please install FFmpeg or bundled imageio-ffmpeg.")
            return {'CANCELLED'}

        scene = context.scene
        s = getattr(scene, "animated_image_settings", None)

        # Resolve format
        if self.format != 'AUTO':
            target_format = self.format
        elif s:
            target_format = s.format
        else:
            target_format = 'WEBP'

        # Resolve destination file path
        if self.filepath:
            target_filepath = self.filepath
        elif s and s.filepath:
            target_filepath = s.filepath
        elif scene.render.filepath:
            target_filepath = scene.render.filepath
        else:
            target_filepath = "//render"

        output_path = bpy.path.abspath(target_filepath)
        output_path = ensure_extension(output_path, target_format)

        # Resolve scale and loop count
        scale = self.scale if self.scale > 0 else (s.scale if s else 100)
        loop_count = self.loop_count if self.loop_count >= 0 else (s.loop_count if s else 0)

        # Resolve GIF quality
        gif_quality = self.gif_quality if self.gif_quality != 'AUTO' else (s.gif_quality if s else 'MEDIUM')

        # Resolve WebP profile & options
        if self.webp_profile != 'AUTO':
            webp_profile = self.webp_profile
            webp_lossless = self.webp_lossless
            webp_quality = self.webp_quality if self.webp_quality >= 0 else (s.webp_quality if s else 75)
            webp_preset = self.webp_preset if self.webp_preset != 'AUTO' else (s.webp_preset if s else 'default')
            webp_compression = self.webp_compression if self.webp_compression >= 0 else (s.webp_compression if s else 4)
        elif s:
            webp_profile = s.webp_profile
            webp_lossless = s.webp_lossless
            webp_quality = s.webp_quality
            webp_preset = s.webp_preset
            webp_compression = s.webp_compression
        else:
            webp_profile = 'BALANCED'
            webp_lossless = False
            webp_quality = 75
            webp_preset = 'default'
            webp_compression = 4

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
            scene.render.resolution_percentage = scale
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

            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            print(f"Converting video to {target_format} (loop={loop_count})...")
            success, err_msg = convert_video_to_animated_image(
                ffmpeg_exe=ffmpeg_exe,
                input_video=temp_video_path,
                output_path=output_path,
                target_format=target_format,
                loop_count=loop_count,
                gif_quality=gif_quality,
                webp_profile=webp_profile,
                webp_lossless=webp_lossless,
                webp_quality=webp_quality,
                webp_preset=webp_preset,
                webp_compression=webp_compression,
                temp_dir=temp_dir,
            )

            if not success:
                self.report({'ERROR'}, f"Conversion failed: {err_msg}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Successfully saved animated {target_format} to: {output_path}")
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
        options={'PATH_SUPPORTS_BLEND_RELATIVE'},
        default="",
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
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
