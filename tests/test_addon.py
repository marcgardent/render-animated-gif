"""
Automated test suite for Render Animated Image (GIF & WebP) Blender extension.
Run via: blender --background --python test_addon.py
"""

import os
import sys
import tempfile
import struct
import subprocess

# Ensure src directory is in path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC_DIR)

import __init__ as addon
import bpy


def run_tests():
    print("\n" + "=" * 60)
    print("RUNNING EXTENSION TEST SUITE")
    print("=" * 60)

    # 1. Test Registration
    print("[1/6] Testing registration...")
    addon.register()
    scene = bpy.context.scene
    assert hasattr(scene, "animated_image_settings"), "animated_image_settings not found on scene!"
    assert hasattr(bpy.ops.render, "animated_image"), "render.animated_image operator not registered!"
    assert hasattr(bpy.ops.render, "animated_loop"), "render.animated_loop operator not registered!"
    assert hasattr(bpy.ops.render, "animation_gif"), "render.animation_gif operator not registered!"
    print("  -> Registration OK.")

    # 2. Test Scene Properties Configuration & Filepath Extension Sync
    print("[2/6] Testing property configuration and extension sync...")
    settings = scene.animated_image_settings
    assert hasattr(settings, "filepath"), "filepath property not found on animated_image_settings!"
    settings.filepath = "//render.webp"
    settings.format = 'GIF'
    assert settings.format == 'GIF'
    assert settings.filepath == "//render.gif", f"Expected //render.gif, got {settings.filepath}"

    settings.format = 'WEBP'
    assert settings.format == 'WEBP'
    assert settings.filepath == "//render.webp", f"Expected //render.webp, got {settings.filepath}"

    settings.webp_profile = 'HIGH'
    settings.scale = 50
    settings.loop_count = 0
    assert settings.webp_profile == 'HIGH'
    print("  -> Properties configuration and extension sync OK.")

    # Prepare minimal test scene
    scene.frame_start = 1
    scene.frame_end = 2
    scene.render.resolution_x = 32
    scene.render.resolution_y = 32

    with tempfile.TemporaryDirectory() as td:
        # 3. Test Direct Render via Scene Settings (Output panel workflow: just render!)
        print("[3/6] Testing direct render via scene settings (no modal, just render)...")
        scene_output = os.path.join(td, "scene_render.webp")
        settings.filepath = scene_output
        settings.format = 'WEBP'
        settings.webp_profile = 'BALANCED'
        settings.scale = 100
        settings.loop_count = 0

        # Invoke operator without arguments, exactly like clicking the button in Output panel
        res_direct = bpy.ops.render.animated_image()
        assert res_direct == {'FINISHED'}, f"Direct render failed: {res_direct}"
        assert os.path.exists(scene_output), "Direct render output file was not created!"
        assert os.path.getsize(scene_output) > 0, "Direct render output file is empty!"
        print(f"  -> Direct render via scene settings OK ({os.path.getsize(scene_output)} bytes).")

        # 4. Test WebP Render with Operator Parameter Overrides (loop=0)
        print("[4/6] Testing WebP render with operator overrides (loop=0)...")
        webp_path = os.path.join(td, "test_render.webp")
        res_webp = bpy.ops.render.animated_image(
            'EXEC_DEFAULT',
            filepath=webp_path,
            format='WEBP',
            webp_profile='BALANCED',
            scale=100,
            loop_count=0
        )
        assert res_webp == {'FINISHED'}, f"WebP render failed: {res_webp}"
        assert os.path.exists(webp_path), "WebP file was not created!"
        assert os.path.getsize(webp_path) > 0, "WebP file is empty!"

        # Verify ANIM chunk and loop_count == 0
        with open(webp_path, 'rb') as f:
            data = f.read()
        anim_pos = data.find(b'ANIM')
        assert anim_pos != -1, "ANIM chunk not found in generated WebP!"
        bg_color, loop_count = struct.unpack('<IH', data[anim_pos + 8:anim_pos + 14])
        assert loop_count == 0, f"Expected loop_count 0, got {loop_count}"
        print(f"  -> WebP render OK (file size: {os.path.getsize(webp_path)} bytes, loop_count={loop_count}).")

        # 5. Test GIF Render
        print("[5/6] Testing GIF render...")
        gif_path = os.path.join(td, "test_render.gif")
        res_gif = bpy.ops.render.animated_image(
            'EXEC_DEFAULT',
            filepath=gif_path,
            format='GIF',
            gif_quality='MEDIUM',
            scale=100,
            loop_count=0
        )
        assert res_gif == {'FINISHED'}, f"GIF render failed: {res_gif}"
        assert os.path.exists(gif_path), "GIF file was not created!"
        assert os.path.getsize(gif_path) > 0, "GIF file is empty!"
        print(f"  -> GIF render OK (file size: {os.path.getsize(gif_path)} bytes).")

        # 6. Test Legacy Operator Compatibility
        print("[6/6] Testing legacy render.animation_gif operator...")
        legacy_path = os.path.join(td, "legacy_render.gif")
        res_legacy = bpy.ops.render.animation_gif(
            'EXEC_DEFAULT',
            filepath=legacy_path,
            scale=100
        )
        assert res_legacy == {'FINISHED'}, f"Legacy render failed: {res_legacy}"
        assert os.path.exists(legacy_path), "Legacy GIF file was not created!"
        print("  -> Legacy operator OK.")

    # Clean unregistration
    addon.unregister()
    assert not hasattr(bpy.context.scene, "animated_image_settings"), "animated_image_settings not unregistered!"
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
