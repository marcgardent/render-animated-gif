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
    print("[1/5] Testing registration...")
    addon.register()
    scene = bpy.context.scene
    assert hasattr(scene, "animated_image_settings"), "animated_image_settings not found on scene!"
    assert hasattr(bpy.ops.render, "animated_image"), "render.animated_image operator not registered!"
    assert hasattr(bpy.ops.render, "animated_loop"), "render.animated_loop operator not registered!"
    assert hasattr(bpy.ops.render, "animation_gif"), "render.animation_gif operator not registered!"
    print("  -> Registration OK.")

    # 2. Test Scene Properties Configuration
    print("[2/5] Testing property configuration...")
    settings = scene.animated_image_settings
    settings.format = 'WEBP'
    settings.webp_profile = 'HIGH'
    settings.scale = 50
    settings.loop_count = 0
    assert settings.format == 'WEBP'
    assert settings.webp_profile == 'HIGH'

    settings.format = 'GIF'
    settings.gif_quality = 'HIGH'
    assert settings.format == 'GIF'
    assert settings.gif_quality == 'HIGH'
    print("  -> Properties configuration OK.")

    # Prepare minimal test scene
    scene.frame_start = 1
    scene.frame_end = 2
    scene.render.resolution_x = 32
    scene.render.resolution_y = 32

    with tempfile.TemporaryDirectory() as td:
        # 3. Test WebP Render (loop=0)
        print("[3/5] Testing WebP render with loop=0...")
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

        # 4. Test GIF Render
        print("[4/5] Testing GIF render...")
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

        # 5. Test Legacy Operator Compatibility
        print("[5/5] Testing legacy render.animation_gif operator...")
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
