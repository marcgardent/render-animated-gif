# Render Animated Image (GIF & WebP)

A modern Blender extension to render animations directly into animated **WebP** (`loop=0`) and **GIF** image files from Blender.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Blender 4.2+](https://img.shields.io/badge/Blender-4.2%2B%20%7C%205.x-orange.svg)](https://www.blender.org)
[![Ko-fi](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffcc00?style=for-the-badge&logo=ko-fi&logoColor=black)](https://ko-fi.com/byebyelan)

---

## Features

- **Modern WebP Animation**:
  - Full 24-bit RGB color with 8-bit Alpha channel transparency.
  - Infinite looping (`loop=0`) by default, ideal for web, Discord stickers, and UI animations.
  - Significantly smaller file sizes and superior visual quality compared to GIF.
- **Classic Animated GIF**:
  - Universal compatibility with legacy platforms.
  - Custom palette generation and dithering modes for optimal color fidelity.
- **Dedicated Output Properties Panel**:
  - Configurable format switcher directly inside the Blender `Output` properties tab.
  - Real-time profile selectors and fine-tuning options.
  - One-click render button right from the properties panel.
- **Encoding Profiles**:
  - **WebP**:
    - `Balanced`: Lossy 75% quality, optimal balance between file size and visual fidelity.
    - `High Quality`: Lossy 90% quality for crisp details.
    - `Lossless`: 100% mathematically lossless, pixel-perfect for 2D, pixel art, and UI graphics.
    - `Compact`: Lossy 50% quality, minimized file size for web / chat stickers.
    - `Custom`: Complete control over lossless mode, quality slider, encoder presets (*photo, drawing, icon, text*), and compression effort (0–6).
  - **GIF**:
    - `High (2-Pass)`: Two-pass differential palette generation with Bayer dithering.
    - `Medium (1-Pass)`: Single-pass split palette generation.
    - `Low (Fast)`: Direct fast conversion without custom palette.
- **Top Bar Integration**:
  - Accessible via `Top Bar > Render > Render Animated Image (GIF/WebP)...`.
  - Backward compatibility aliases: `render.animated_loop` and `render.animation_gif`.

---

## Project Structure

```text
render-animated-gif/
├── src/                                  # Extension source code
│   ├── __init__.py                       # Extension entry point & registration
│   ├── blender_manifest.toml             # Blender extension manifest
│   ├── converters.py                     # FFmpeg WebP & GIF conversion routines
│   ├── operators.py                      # Modal render operator & file dialog
│   ├── properties.py                     # PropertyGroup definitions & scene settings
│   ├── ui.py                             # Output properties panel & menu integration
│   └── utils.py                          # FFmpeg detection & path helpers
├── tests/                                # Automated test suite
│   └── test_addon.py                     # Headless Blender end-to-end tests
├── scripts/                              # Packaging & dependency scripts
│   ├── build_package.py                  # Package builder (full / light)
│   └── download_wheels.py                # PyPI platform wheels downloader
├── Makefile                              # Build, install, test, and dev commands
├── LICENSE                               # GPL-3.0 License
└── README.md                             # Documentation
```

---

## Development & Makefile Commands

A complete `Makefile` is provided for build automation:

| Command | Description |
| :--- | :--- |
| `make help` | Display available targets and descriptions. |
| `make build` | Build the complete extension `.zip` package with bundled wheels. |
| `make build-light` | Build a lightweight `.zip` package (~23 KB, uses system FFmpeg). |
| `make install` | Build and install the `.zip` package into Blender's user repository. |
| `make install-dev` | Create a symbolic link directly into Blender for live development (hot reload). |
| `make unlink` | Remove the development symbolic link. |
| `make uninstall` | Uninstall the extension from Blender. |
| `make wheels` | Download imageio-ffmpeg platform wheels into `src/wheels/`. |
| `make validate` | Validate `src/blender_manifest.toml` using Blender CLI. |
| `make test` | Run the automated test suite in headless Blender. |
| `make clean` | Remove build artifacts, `.zip` archives, and Python cache files. |

---

## Requirements

- **Blender**: 4.2.0 or newer (fully tested on Blender 4.2+ and Blender 5.x LTS).
- **FFmpeg**: Bundled automatically via `imageio-ffmpeg` platform wheels, or detected from system `PATH`.

---

## License

This project is licensed under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)).
