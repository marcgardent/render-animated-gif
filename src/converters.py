import os
import subprocess


def run_ffmpeg_with_progress(cmd, total_frames=None, progress_callback=None, progress_offset=0.0, progress_scale=1.0):
    """Run an FFmpeg command while parsing progress output and calling progress_callback."""
    if not progress_callback:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0, res.stderr

    has_progress = "-progress" in cmd
    if not has_progress:
        full_cmd = cmd[:-1] + ["-progress", "pipe:1", cmd[-1]]
    else:
        full_cmd = cmd

    process = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        if line.startswith("frame="):
            try:
                frame_num = int(line.split("=")[1].strip())
                if total_frames and total_frames > 0:
                    raw_pct = min(1.0, max(0.0, frame_num / total_frames))
                    scaled_pct = progress_offset + (raw_pct * progress_scale)
                    progress_callback(scaled_pct)
            except Exception:
                pass

    process.wait()
    stderr = process.stderr.read()
    return process.returncode == 0, stderr


def convert_video_to_gif(ffmpeg_exe, input_video, output_path, quality='MEDIUM', loop_count=0, temp_dir=None,
                         total_frames=None, progress_callback=None):
    """Convert a temporary video to an animated GIF using FFmpeg with live progress tracking."""
    if quality == 'HIGH' and temp_dir:
        palette_file = os.path.join(temp_dir, "palette.png")
        cmd_palette = [
            ffmpeg_exe, "-y", "-i", input_video,
            "-vf", "palettegen=stats_mode=diff", palette_file
        ]
        ok, err = run_ffmpeg_with_progress(
            cmd_palette, total_frames=total_frames, progress_callback=progress_callback,
            progress_offset=0.0, progress_scale=0.5
        )
        if not ok:
            return False, f"FFmpeg palettegen failed: {err}"

        cmd = [
            ffmpeg_exe, "-y", "-i", input_video,
            "-i", palette_file,
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-loop", str(loop_count),
            output_path
        ]
        ok, err = run_ffmpeg_with_progress(
            cmd, total_frames=total_frames, progress_callback=progress_callback,
            progress_offset=0.5, progress_scale=0.5
        )
        if not ok:
            return False, f"FFmpeg GIF encoding failed: {err}"
        return True, ""

    elif quality == 'MEDIUM':
        cmd = [
            ffmpeg_exe, "-y", "-i", input_video,
            "-vf", "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", str(loop_count),
            output_path
        ]
    else:  # LOW
        cmd = [
            ffmpeg_exe, "-y", "-i", input_video,
            "-loop", str(loop_count),
            output_path
        ]

    ok, err = run_ffmpeg_with_progress(
        cmd, total_frames=total_frames, progress_callback=progress_callback,
        progress_offset=0.0, progress_scale=1.0
    )
    if not ok:
        return False, f"FFmpeg GIF encoding failed: {err}"

    return True, ""


def convert_video_to_webp(ffmpeg_exe, input_video, output_path, profile='BALANCED',
                          lossless=False, quality=75, preset='default', compression=4,
                          loop_count=0, total_frames=None, progress_callback=None):
    """Convert a temporary video to an animated WebP image using FFmpeg libwebp encoder with live progress tracking."""
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

    ok, err = run_ffmpeg_with_progress(
        cmd, total_frames=total_frames, progress_callback=progress_callback,
        progress_offset=0.0, progress_scale=1.0
    )
    if not ok:
        return False, f"FFmpeg WebP encoding failed: {err}"

    return True, ""


def convert_video_to_animated_image(ffmpeg_exe, input_video, output_path,
                                    target_format='WEBP', loop_count=0,
                                    gif_quality='MEDIUM',
                                    webp_profile='BALANCED', webp_lossless=False,
                                    webp_quality=75, webp_preset='default',
                                    webp_compression=4, temp_dir=None,
                                    total_frames=None, progress_callback=None):
    """Dispatcher function to convert video into the chosen format with progress tracking."""
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
            total_frames=total_frames,
            progress_callback=progress_callback,
        )
    else:
        return convert_video_to_gif(
            ffmpeg_exe=ffmpeg_exe,
            input_video=input_video,
            output_path=output_path,
            quality=gif_quality,
            loop_count=loop_count,
            temp_dir=temp_dir,
            total_frames=total_frames,
            progress_callback=progress_callback,
        )
