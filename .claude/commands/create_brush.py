"""
create_brush.py
Generates Procreate-compatible .brush packages from a JSON spec.

Usage:
  python create_brush.py spec.json
  cat spec.json | python create_brush.py

Dependencies: Pillow, numpy
  pip install Pillow numpy
"""

import io
import json
import math
import plistlib
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ---------------------------------------------------------------------------
# Shape generators
# ---------------------------------------------------------------------------

def make_ellipse_shape_png(
    size: int = 256,
    padding: int = 16,
    padding_x: int = None,
    padding_y: int = None,
    blur_radius: float = 10,
) -> bytes:
    """L-mode soft ellipse. White = full opacity in Procreate.

    padding_x / padding_y override padding for asymmetric (chisel) tips.
    """
    px = padding_x if padding_x is not None else padding
    py = padding_y if padding_y is not None else padding
    img = Image.new("L", (size, size), 0)
    ImageDraw.Draw(img).ellipse(
        [px, py, size - px, size - py], fill=255
    )
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def make_blob_shape_png(
    size: int = 256,
    base_radius: float = 88.0,
    harmonics: list = None,
    roughness: float = 4.0,
    wet_edge: bool = True,
    blur_radius: float = 5,
) -> bytes:
    """L-mode organic blob with optional wet-edge darkening at the boundary."""
    if harmonics is None:
        harmonics = [
            {"freq": 3,  "amp": 9.0, "phase": 0.0},
            {"freq": 7,  "amp": 6.0, "phase": 1.2},
            {"freq": 11, "amp": 4.0, "phase": 0.7},
            {"freq": 17, "amp": 3.0, "phase": 2.1},
        ]

    S = size
    cx = cy = S // 2
    rng = np.random.default_rng(123)

    x, y = np.meshgrid(
        np.arange(S, dtype=np.float32), np.arange(S, dtype=np.float32)
    )
    angle = np.arctan2(y - cy, x - cx)
    dist  = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    R = float(base_radius) + sum(
        h["amp"] * np.sin(h["freq"] * angle + h["phase"])
        for h in harmonics
    )
    R += rng.normal(0, roughness, (S, S))

    nd = dist / np.maximum(R, 1.0)

    if wet_edge:
        inner     = np.clip(1.0 - nd * 0.55, 0.0, 1.0)
        edge_ring = np.clip((nd - 0.65) / 0.35, 0.0, 1.0) * 0.55
        alpha     = np.clip(inner + edge_ring, 0.0, 1.0)
    else:
        alpha = np.clip(1.0 - nd, 0.0, 1.0)

    alpha[nd > 1.0] = 0.0

    img = Image.fromarray((alpha * 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Grain generator
# ---------------------------------------------------------------------------

def make_grain_png(
    size: int = 512,
    mean: float = 220,
    std: float = 25,
    blur: float = 0.7,
) -> bytes:
    """L-mode paper grain texture."""
    rng = np.random.default_rng(42)
    noise = np.clip(rng.normal(mean, std, (size, size)), 0, 255).astype(np.uint8)
    img = Image.fromarray(noise).filter(ImageFilter.GaussianBlur(blur))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Shared thumbnail generator
# ---------------------------------------------------------------------------

def make_thumbnail_png(
    shape_bytes: bytes,
    stroke_color: tuple = (58, 58, 58),
    stamp_alpha: int = 200,
    n_stamps: int = 12,
) -> bytes:
    """267×267 RGBA thumbnail with a simulated diagonal stroke."""
    thumb = Image.new("RGBA", (267, 267), (255, 255, 255, 255))
    shape = Image.open(io.BytesIO(shape_bytes)).convert("L")
    fill  = (*stroke_color, stamp_alpha)
    for i in range(n_stamps):
        t   = i / (n_stamps - 1)
        cx  = int(20 + t * 227)
        cy  = int(247 - t * 207)
        sz  = max(1, int(18 + 10 * math.sin(math.pi * t)))
        stamp = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        stamp.paste(Image.new("RGBA", (sz, sz), fill),
                    mask=shape.resize((sz, sz), Image.LANCZOS))
        thumb.alpha_composite(stamp, dest=(cx - sz // 2, cy - sz // 2))
    buf = io.BytesIO()
    thumb.save(buf, "PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Generic NSKeyedArchiver binary plist builder
# ---------------------------------------------------------------------------

def make_brush_archive(
    name: str,
    shape_filename: str,
    grain_filename: str,
    *,
    spacing: float          = 0.08,
    stream_line: float      = 0.30,
    jitter: float           = 0.015,
    tip_type: int           = 1,
    head_taper: bool        = True,
    tail_taper: bool        = True,
    grain_depth: float      = 0.60,
    grain_mode: int         = 0,
    blend_mode: int         = 0,
    opacity: float          = 0.85,
    flow: float             = 0.50,
    wet_edges: bool         = False,
    pressure_size: float    = 0.65,
    pressure_opacity: float = 0.45,
    maximum_size: float     = 0.15,
    minimum_size: float     = 0.02,
    uuid: str               = "brush-001",
) -> bytes:
    """Build a binary NSKeyedArchiver plist using the SilicaBrush format
    that Procreate actually expects."""
    import struct

    U = plistlib.UID

    # Color: 4 little-endian floats (RGBA) — black, full alpha
    color_bytes = struct.pack("<4f", 0.0, 0.0, 0.0, 1.0)

    objects = [
        "$null",                                                          # 0
        # 1: SilicaBrush instance (root)
        {
            "$class": U(4),
            "name": U(3),
            "color": U(2),
            "bundledShapePath": U(0),     # $null = use embedded Shape.png
            "bundledGrainPath": U(0),     # $null = use embedded Grain.png
            # Stroke path
            "plotSpacing": float(spacing),
            "plotJitter": float(jitter),
            "plotSmoothing": float(stream_line),
            "stamp": False,
            "oriented": False,
            # Shape
            "shapeRandomise": False,
            "shapeRotation": 0.0,
            "shapeScatter": 0.0,
            # Grain / texture
            "textureScale": float(grain_depth),
            "textureMovement": 1.0 if grain_mode == 0 else 0.0,
            "textureFilter": True,
            "textureRotation": 0.0,
            "textureZoom": 1.0,
            # Rendering
            "blendMode": int(blend_mode),
            "paintOpacity": float(opacity),
            "paintSize": float(maximum_size),
            # Dynamics — pressure
            "dynamicsPressureSize": float(pressure_size),
            "dynamicsPressureOpacity": float(pressure_opacity),
            # Dynamics — speed
            "dynamicsSpeedSize": 0.0,
            "dynamicsSpeedOpacity": 0.0,
            "dynamicsFalloff": 0.0,
            "dynamicsGlaze": False,
            "dynamicsMix": 0.0,
            # Size / opacity range
            "maxSize": 1.0,
            "minSize": float(minimum_size) / max(float(maximum_size), 0.001),
            "maxOpacity": 1.0,
            "minOpacity": 0.0,
            # Taper
            "taperStartLength": 0.3 if head_taper else 0.0,
            "taperEndLength": 0.3 if tail_taper else 0.0,
            "taperSize": 1.0,
            "taperOpacity": 1.0,
            # Secondary modes
            "eraseOpacity": 0.5,
            "eraseSize": 0.3,
            "smudgeOpacity": 0.5,
            "smudgeSize": 0.3,
        },
        color_bytes,                                                      # 2
        name,                                                             # 3
        {"$classname": "SilicaBrush", "$classes": ["SilicaBrush", "NSObject"]},  # 4
    ]

    archive = {
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": U(1)},
        "$objects": objects,
    }
    buf = io.BytesIO()
    plistlib.dump(archive, buf, fmt=plistlib.FMT_BINARY)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Generic brush builder
# ---------------------------------------------------------------------------

def build_brush(spec: dict) -> None:
    """Build a .brush file from a JSON spec dict."""
    name = spec["name"]
    output = spec.get("output", f"{name.lower()}.brush")

    # --- Shape ---
    shape_spec = spec["shape"]
    shape_type = shape_spec.get("type", "ellipse")
    if shape_type == "ellipse":
        shape = make_ellipse_shape_png(
            size=shape_spec.get("size", 256),
            padding=shape_spec.get("padding", 16),
            padding_x=shape_spec.get("padding_x"),
            padding_y=shape_spec.get("padding_y"),
            blur_radius=shape_spec.get("blur_radius", 10),
        )
    elif shape_type == "blob":
        shape = make_blob_shape_png(
            size=shape_spec.get("size", 256),
            base_radius=shape_spec.get("base_radius", 88.0),
            harmonics=shape_spec.get("harmonics"),
            roughness=shape_spec.get("roughness", 4.0),
            wet_edge=shape_spec.get("wet_edge", True),
            blur_radius=shape_spec.get("blur_radius", 5),
        )
    else:
        raise ValueError(f"Unknown shape type: {shape_type!r}. Expected 'ellipse' or 'blob'.")

    # --- Grain ---
    grain_spec = spec.get("grain", {})
    grain = make_grain_png(
        size=grain_spec.get("size", 512),
        mean=grain_spec.get("mean", 220),
        std=grain_spec.get("std", 25),
        blur=grain_spec.get("blur", 0.7),
    )

    # --- Thumbnail ---
    thumb_spec = spec.get("thumbnail", {})
    stroke_color = tuple(thumb_spec.get("stroke_color", [58, 58, 58]))
    thumb = make_thumbnail_png(
        shape,
        stroke_color=stroke_color,
        stamp_alpha=thumb_spec.get("stamp_alpha", 200),
        n_stamps=thumb_spec.get("n_stamps", 12),
    )

    # --- Archive ---
    archive = make_brush_archive(
        name, "Shape.png", "Grain.png",
        spacing=spec.get("spacing", 0.08),
        stream_line=spec.get("stream_line", 0.30),
        jitter=spec.get("jitter", 0.015),
        tip_type=spec.get("tip_type", 1),
        head_taper=spec.get("head_taper", True),
        tail_taper=spec.get("tail_taper", True),
        grain_depth=spec.get("grain_depth", 0.60),
        grain_mode=spec.get("grain_mode", 0),
        blend_mode=spec.get("blend_mode", 0),
        opacity=spec.get("opacity", 0.85),
        flow=spec.get("flow", 0.50),
        wet_edges=spec.get("wet_edges", False),
        pressure_size=spec.get("pressure_size", 0.65),
        pressure_opacity=spec.get("pressure_opacity", 0.45),
        maximum_size=spec.get("maximum_size", 0.15),
        minimum_size=spec.get("minimum_size", 0.02),
        uuid=spec.get("uuid", "brush-001"),
    )

    print(f"Building {output} ...")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Brush.archive",           archive)
        zf.writestr("Shape.png",               shape)
        zf.writestr("Grain.png",               grain)
        zf.writestr("QuickLook/Thumbnail.png", thumb)

    total = sum(len(b) for b in [archive, shape, grain, thumb])
    print(f"  {output}: {total:,} bytes uncompressed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        with open(path) as f:
            spec = json.load(f)
    else:
        spec = json.load(sys.stdin)

    build_brush(spec)
    print("\nDone!")


if __name__ == "__main__":
    main()
