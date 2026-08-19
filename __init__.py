import bpy
import os
import subprocess
import tempfile
import shutil
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, IntProperty
import imageio_ffmpeg


class RENDER_OT_animation_gif(Operator):
    """Render animation and export as GIF"""
    bl_idname = "render.animation_gif"
    bl_label = "Render Animation as GIF"
    bl_description = "Renders Animation into a .GIF image file."
    bl_options = {'PRESET', 'REGISTER'}
    filename_ext = ".gif"

    filter_glob: StringProperty(default="*.gif", options={'HIDDEN'})

    filepath: StringProperty(
        name="File Path",
        description="Path to save the GIF file",
        subtype='FILE_PATH',
        default="//render.gif",
    )
    quality: EnumProperty(
        name="Quality",
        description="GIF quality",
        items=[
            ('LOW', "Low", "Smaller file, faster conversion"),
            ('MEDIUM', "Medium", "Balanced quality and file size"),
            ('HIGH', "High", "Best quality, larger file"),
        ],
        default='MEDIUM',
    )
    scale: IntProperty(
        name="Resolution %",
        description="Renders the .GIF by a percentage of the current scene's resolution.",
        default=100,
        min=1,
        max=100,
        subtype='PERCENTAGE',
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # --- Export Options ---
        box = layout.box()
        box.label(text="Export Options:", icon='RENDER_ANIMATION')
        col = box.column()
        col.prop(self, "quality")
        col.prop(self, "scale")

    def execute(self, context):
        scene = context.scene

        # Save original render settings
        original_filepath = scene.render.filepath
        original_format = scene.render.image_settings.file_format
        original_use_overwrite = scene.render.use_overwrite
        original_use_file_extension = scene.render.use_file_extension
        original_res_percentage = scene.render.resolution_percentage
        original_ffmpeg_codec = scene.render.ffmpeg.codec
        original_ffmpeg_format = scene.render.ffmpeg.format

        temp_dir = tempfile.mkdtemp(prefix="temp_gif_render_")
        temp_video_path = os.path.join(temp_dir, "render.mp4")

        try:
            # Apply resolution scale using resolution_percentage
            scene.render.resolution_percentage = self.scale

            # Set render settings for temporary video
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.codec = 'H264'
            scene.render.ffmpeg.format = 'MPEG4'
            scene.render.filepath = temp_video_path
            scene.render.use_overwrite = True
            scene.render.use_file_extension = True

            # Render animation
            print("Rendering animation to temporary video...")
            bpy.ops.render.render(animation=True)

            # Output path for final GIF
            output_path = bpy.path.abspath(self.filepath)
            if not output_path.lower().endswith(".gif"):
                output_path += ".gif"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Build FFmpeg command
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [ffmpeg_exe, "-y", "-i", temp_video_path]

            if self.quality == 'HIGH':
                # Two-pass palette generation
                palette_file = os.path.join(temp_dir, "palette.png")
                cmd_palette = [ffmpeg_exe, "-y", "-i", temp_video_path,
                               "-vf", "palettegen=stats_mode=diff", palette_file]
                subprocess.run(cmd_palette, capture_output=True, text=True)

                cmd += ["-i", palette_file,
                        "-lavfi", "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
                        "-loop", "0", output_path]
            elif self.quality == 'MEDIUM':
                # Single pass with palettegen/use
                cmd += ["-vf", "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                        "-loop", "0", output_path]
            else:  # LOW
                cmd += ["-loop", "0", output_path]

            print("Converting video to GIF with FFmpeg...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.report({'ERROR'}, f"FFmpeg failed: {result.stderr}")
                return {'CANCELLED'}

            self.report({'INFO'}, f"GIF saved to {output_path}")
            return {'FINISHED'}

        finally:
            # Restore original render settings
            scene.render.filepath = original_filepath
            scene.render.image_settings.file_format = original_format
            scene.render.use_overwrite = original_use_overwrite
            scene.render.use_file_extension = original_use_file_extension
            scene.render.resolution_percentage = original_res_percentage
            scene.render.ffmpeg.codec = original_ffmpeg_codec
            scene.render.ffmpeg.format = original_ffmpeg_format

            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)


def menu_func(self, context):
    self.layout.operator(RENDER_OT_animation_gif.bl_idname)


def register():
    bpy.utils.register_class(RENDER_OT_animation_gif)
    bpy.types.TOPBAR_MT_render.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_render.remove(menu_func)
    bpy.utils.unregister_class(RENDER_OT_animation_gif)


if __name__ == "__main__":
    register()