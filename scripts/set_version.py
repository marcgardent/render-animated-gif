#!/usr/bin/env python3
"""
Update version string in src/blender_manifest.toml and src/__init__.py.
"""

import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_DIR, "src")
MANIFEST_PATH = os.path.join(SRC_DIR, "blender_manifest.toml")
INIT_PATH = os.path.join(SRC_DIR, "__init__.py")


def set_version(new_version: str):
    # Strip leading 'v' if present (e.g., 'v2.0.0' -> '2.0.0')
    if new_version.startswith("v"):
        new_version = new_version[1:]

    # Validate semver format (X.Y.Z or X.Y)
    parts = new_version.split(".")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        print(f"Error: Invalid version format '{new_version}'. Expected semantic version like '2.0.0'.", file=sys.stderr)
        sys.exit(1)

    while len(parts) < 3:
        parts.append("0")

    version_tuple_str = f"({', '.join(parts)})"

    # 1. Update src/blender_manifest.toml
    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest file not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_content = f.read()

    new_manifest_content = re.sub(
        r'(?m)^version\s*=\s*["\'][^"\']+["\']',
        f'version = "{new_version}"',
        manifest_content,
        count=1
    )

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        f.write(new_manifest_content)

    print(f"  [OK] Updated {MANIFEST_PATH} -> version = \"{new_version}\"")

    # 2. Update src/__init__.py
    if not os.path.exists(INIT_PATH):
        print(f"Error: Init file not found at {INIT_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(INIT_PATH, "r", encoding="utf-8") as f:
        init_content = f.read()

    new_init_content = re.sub(
        r'("version"\s*:\s*)\([^)]+\)',
        f'\\g<1>{version_tuple_str}',
        init_content,
        count=1
    )

    with open(INIT_PATH, "w", encoding="utf-8") as f:
        f.write(new_init_content)

    print(f"  [OK] Updated {INIT_PATH} -> \"version\": {version_tuple_str}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: set_version.py <version>", file=sys.stderr)
        sys.exit(1)

    set_version(sys.argv[1].strip())
