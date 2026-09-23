import os
import subprocess


def convert_video_to_gif(ffmpeg_exe, input_video, output_path, quality='MEDIUM', loop_count=0, temp_dir=None):
    """Convert a temporary video to an animated GIF using FFmpeg."""
    cmd = [ffmpeg_exe, "-y", "-i", input_video]

    if quality == 'HIGH' and temp_dir:
        palette_file = os.path.join(temp_dir, "palette.png")
        cmd_palette = [
            ffmpeg_exe, "-y", "-i", input_video,
            "-vf", "palettegen=stats_mode=diff", palette_file
        ]
        res_pal = subprocess.run(cmd_palette, capture_output=True, text=True)
        if res_pal.returncode != 0:
            return False, f"FFmpeg palettegen failed: {res_pal.stderr}"

        cmd += [
            "-i", palette_file,
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-loop", str(loop_count),
            output_path
        ]
    elif quality == 'MEDIUM':
        cmd += [
            "-vf", "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", str(loop_count),
            output_path
        ]
    else:  # LOW
        cmd += [
            "-loop", str(loop_count),
            output_path
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"FFmpeg GIF encoding failed: {result.stderr}"

    return True, ""


def convert_video_to_webp(ffmpeg_exe, input_video, output_path, profile='BALANCED',
                          lossless=False, quality=75, preset='default', compression=4,
                          loop_count=0):
    """Convert a temporary video to an animated WebP image using FFmpeg libwebp encoder."""
    # Resolve profile presets
    if profile == 'BALANCED':
        lossless = False
        quality = 75
        preset = 'default'
        compression = 4
    elif profile == 'HIGH':
        lossless = False
        quality = 90
        preset = 'default'
        compression = 5
    elif profile == 'LOSSLESS':
        lossless = True
        quality = 100
        preset = 'default'
        compression = 4
    elif profile == 'COMPACT':
        lossless = False
        quality = 50
        preset = 'default'
        compression = 6

    cmd = [
        ffmpeg_exe, "-y", "-i", input_video,
        "-c:v", "libwebp",
        "-loop", str(loop_count),
    ]

    if lossless:
        cmd += ["-lossless", "1"]
    else:
        cmd += ["-lossless", "0", "-quality", str(max(0, min(100, quality)))]

    if preset and preset != 'default':
        cmd += ["-preset", preset]

    cmd += ["-compression_level", str(max(0, min(6, compression)))]
    cmd += [output_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"FFmpeg WebP encoding failed: {result.stderr}"

    return True, ""


def convert_video_to_animated_image(ffmpeg_exe, input_video, output_path,
                                    target_format='WEBP', loop_count=0,
                                    gif_quality='MEDIUM',
                                    webp_profile='BALANCED', webp_lossless=False,
                                    webp_quality=75, webp_preset='default',
                                    webp_compression=4, temp_dir=None):
    """Dispatcher function to convert video into the chosen format."""
    if target_format.upper() == 'WEBP':
        return convert_video_to_webp(
            ffmpeg_exe=ffmpeg_exe,
            input_video=input_video,
            output_path=output_path,
            profile=webp_profile,
            lossless=webp_lossless,
            quality=webp_quality,
            preset=webp_preset,
            compression=webp_compression,
            loop_count=loop_count,
        )
    else:
        return convert_video_to_gif(
            ffmpeg_exe=ffmpeg_exe,
            input_video=input_video,
            output_path=output_path,
            quality=gif_quality,
            loop_count=loop_count,
            temp_dir=temp_dir,
        )
