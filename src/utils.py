import os
import shutil
import subprocess
import bpy


def get_ffmpeg_binary():
    """Locate FFmpeg executable: first tries imageio_ffmpeg, then system PATH."""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except (ImportError, Exception):
        pass

    # Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # Common Linux / Unix paths
    for candidate in ("/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/snap/bin/ffmpeg"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None


def is_ffmpeg_available():
    """Check if a valid FFmpeg executable is available."""
    return get_ffmpeg_binary() is not None


def ensure_extension(filepath, target_format):
    """Ensure the filepath ends with the correct extension for the selected format."""
    ext = ".webp" if str(target_format).upper() == 'WEBP' else ".gif"
    if not filepath:
        return f"//render{ext}"
    if filepath.endswith("/") or filepath.endswith("\\"):
        return f"{filepath}render{ext}"
    lower_path = filepath.lower()
    if lower_path.endswith(".gif") or lower_path.endswith(".webp"):
        base = filepath.rsplit(".", 1)[0]
        return base + ext
    return filepath + ext

