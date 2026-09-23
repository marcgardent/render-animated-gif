#!/usr/bin/env python3
"""
Build package helper for Render Animated Image extension.
Supports building with bundled wheels or light build (no wheels).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_DIR, "src")


def build_package(light=False, output_dir="build"):
    output_dir_abs = os.path.abspath(output_dir)
    os.makedirs(output_dir_abs, exist_ok=True)

    if light:
        print("[BUILD] Creating lightweight extension package (without bundled wheels)...")
        with tempfile.TemporaryDirectory() as td:
            for item in os.listdir(SRC_DIR):
                if item == "wheels":
                    continue
                src = os.path.join(SRC_DIR, item)
                dst = os.path.join(td, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy(src, dst)

            # Copy LICENSE and README.md into package if present at project root
            for doc in ("LICENSE", "README.md"):
                doc_path = os.path.join(PROJECT_DIR, doc)
                if os.path.exists(doc_path) and not os.path.exists(os.path.join(td, doc)):
                    shutil.copy(doc_path, os.path.join(td, doc))

            # Remove wheels entry from manifest for lightweight package
            manifest_path = os.path.join(td, "blender_manifest.toml")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    content = f.read()

                content_no_whl = re.sub(r'wheels\s*=\s*\[[^\]]*\]', '', content)
                with open(manifest_path, "w", encoding="utf-8") as f:
                    f.write(content_no_whl)

            cmd = [
                "blender",
                "--command",
                "extension",
                "build",
                "--source-dir",
                td,
                "--output-dir",
                output_dir_abs,
            ]
            subprocess.run(cmd, check=True)
    else:
        print("[BUILD] Creating full extension package (with bundled wheels)...")
        wheels_dir = os.path.join(SRC_DIR, "wheels")
        if not os.path.isdir(wheels_dir) or not os.listdir(wheels_dir):
            print("[INFO] Wheels not found, downloading required platform wheels...")
            download_script = os.path.join(PROJECT_DIR, "scripts", "download_wheels.py")
            subprocess.run([sys.executable, download_script, wheels_dir], check=True)

        cmd = [
            "blender",
            "--command",
            "extension",
            "build",
            "--source-dir",
            SRC_DIR,
            "--output-dir",
            output_dir_abs,
        ]
        subprocess.run(cmd, check=True)

    print("[SUCCESS] Package built successfully in:", output_dir_abs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Blender extension package")
    parser.add_argument("--light", action="store_true", help="Build light package without wheels")
    parser.add_argument("--output-dir", default="build", help="Output directory for .zip archive")
    args = parser.parse_args()

    build_package(light=args.light, output_dir=args.output_dir)
