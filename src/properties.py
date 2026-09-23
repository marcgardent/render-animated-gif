import bpy
from bpy.props import EnumProperty, IntProperty, BoolProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup

if __package__:
    from .utils import ensure_extension
else:
    from utils import ensure_extension


def _update_format(self, context):
    if getattr(self, "filepath", None):
        self.filepath = ensure_extension(self.filepath, self.format)


class AnimatedImageSettings(PropertyGroup):
    """Configuration settings for animated image export (WebP / GIF)."""

    filepath: StringProperty(
        name="Output Path",
        description="Destination file path for animated image export",
        default="//render.webp",
        subtype='FILE_PATH',
        options={'PATH_SUPPORTS_BLEND_RELATIVE'},
    )

    format: EnumProperty(
        name="Format",
        description="Choose animated image format",
        items=[
            ('WEBP', "WebP", "Modern animated WebP: 24-bit RGB + Alpha, smaller file size, superior compression", 'FILE_IMAGE', 0),
            ('GIF', "GIF", "Classic animated GIF: 8-bit palette (256 colors max), universal compatibility", 'IMAGE_DATA', 1),
        ],
        default='WEBP',
        update=_update_format,
    )

    scale: IntProperty(
        name="Resolution %",
        description="Render resolution percentage of current scene",
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

    # --- GIF Settings ---
    gif_quality: EnumProperty(
        name="GIF Profile",
        description="Quality preset for animated GIF generation",
        items=[
            ('HIGH', "High (2-Pass)", "Two-pass palette generation with Bayer dithering for optimal color accuracy"),
            ('MEDIUM', "Medium (1-Pass)", "Single-pass split palette generation, balanced quality and speed"),
            ('LOW', "Low (Fast)", "Fast direct conversion without custom palette"),
        ],
        default='MEDIUM',
    )

    # --- WebP Settings ---
    webp_profile: EnumProperty(
        name="WebP Profile",
        description="Preset profile for animated WebP encoding",
        items=[
            ('BALANCED', "Balanced", "Lossy 75% quality, balanced size and visual quality"),
            ('HIGH', "High Quality", "Lossy 90% quality, sharp details and low compression artifacts"),
            ('LOSSLESS', "Lossless", "100% mathematically lossless, pixel-perfect for UI/2D/crisp graphics"),
            ('COMPACT', "Compact", "Lossy 50% quality, smaller file size for web / chat stickers"),
            ('CUSTOM', "Custom", "Manual control over lossless mode, quality slider, preset and compression effort"),
        ],
        default='BALANCED',
    )

    webp_lossless: BoolProperty(
        name="Lossless",
        description="Enable lossless WebP encoding (ignores quality slider)",
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
        description="Tune the WebP encoder for specific visual content",
        items=[
            ('default', "Default", "Default libwebp configuration"),
            ('picture', "Picture", "Digital pictures, portraits, indoor scenes"),
            ('photo', "Photo", "Outdoor photographs with natural lighting"),
            ('drawing', "Drawing", "Hand or line drawings with high contrast details"),
            ('icon', "Icon", "Small colorful graphics and icons"),
            ('text', "Text", "Text-heavy images"),
        ],
        default='default',
    )

    webp_compression: IntProperty(
        name="Compression Effort",
        description="Compression effort (0 = fastest, 6 = slowest/smallest file size)",
        default=4,
        min=0,
        max=6,
    )


classes = (
    AnimatedImageSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.animated_image_settings = PointerProperty(type=AnimatedImageSettings)


def unregister():
    if hasattr(bpy.types.Scene, "animated_image_settings"):
        del bpy.types.Scene.animated_image_settings
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
