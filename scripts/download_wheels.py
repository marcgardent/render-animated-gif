#!/usr/bin/env python3
"""
Download bundled imageio-ffmpeg platform wheels from PyPI.
Used by the Blender Extension build process.
"""

import os
import sys
import json
import urllib.request

DEFAULT_WHEELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "wheels")
WHEELS_DIR = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WHEELS_DIR
PACKAGE_VERSION = "0.6.0"
PYPI_URL = f"https://pypi.org/pypi/imageio-ffmpeg/{PACKAGE_VERSION}/json"

TARGET_WHEELS = [
    "imageio_ffmpeg-0.6.0-py3-none-win_amd64.whl",
    "imageio_ffmpeg-0.6.0-py3-none-macosx_10_9_intel.macosx_10_9_x86_64.whl",
    "imageio_ffmpeg-0.6.0-py3-none-macosx_11_0_arm64.whl",
    "imageio_ffmpeg-0.6.0-py3-none-manylinux2014_x86_64.whl",
]


def download_wheels():
    os.makedirs(WHEELS_DIR, exist_ok=True)
    print(f"Fetching wheel metadata from {PYPI_URL}...")
    try:
        req = urllib.request.urlopen(PYPI_URL)
        data = json.loads(req.read().decode())
    except Exception as e:
        print(f"Error connecting to PyPI: {e}", file=sys.stderr)
        sys.exit(1)

    urls_by_filename = {
        item["filename"]: item["url"]
        for item in data.get("urls", [])
    }

    for filename in TARGET_WHEELS:
        dest_path = os.path.join(WHEELS_DIR, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            print(f"  [OK] {filename} already present.")
            continue

        if filename not in urls_by_filename:
            print(f"  [ERROR] {filename} not found on PyPI!", file=sys.stderr)
            sys.exit(1)

        url = urls_by_filename[filename]
        print(f"  [DOWNLOADING] {filename} ...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"  -> Saved {dest_path} ({os.path.getsize(dest_path)} bytes)")

    print("All required wheels are ready.")


if __name__ == "__main__":
    download_wheels()
