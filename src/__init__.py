bl_info = {
    "name": "Render Animated Image (GIF / WebP)",
    "author": "byebyeLAN",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "Top Bar > Render > Render Animated Image (GIF/WebP)... & Output Properties",
    "description": "Render animation directly into animated WebP (loop=0) or GIF formats.",
    "warning": "",
    "doc_url": "https://extensions.blender.org/add-ons/import-psd-as-mesh-planes/",
    "category": "Render",
}

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(converters)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    if __package__:
        from . import utils
        from . import converters
        from . import properties
        from . import operators
        from . import ui
    else:
        import utils
        import converters
        import properties
        import operators
        import ui


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()