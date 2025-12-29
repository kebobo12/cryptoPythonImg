"""
Shared image utilities for the thumbgen rendering pipeline.

These helpers wrap common Pillow operations in clean, typed functions that
improve readability and maintain consistency across rendering modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image


# ------------------------------------------------------------
# Resizing helpers
# ------------------------------------------------------------

def resize_lanczos(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """
    Resize an image using high-quality LANCZOS filtering.

    Args:
        image: Source image
        size: (width, height) target size

    Returns:
        A new resized RGBA image.
    """
    return image.resize(size, Image.LANCZOS)


# ------------------------------------------------------------
# Alpha compositing
# ------------------------------------------------------------

def alpha_composite(base: Image.Image, overlay: Image.Image, pos: tuple):
    """
    Safely composite overlay onto base at position, clipping to base bounds.

    Args:
        base: Base RGBA image (modified in-place)
        overlay: Overlay RGBA image
        pos: (x, y) position tuple
    """
    x, y = pos

    # Calculate overlap region
    src_x = max(0, -x)
    src_y = max(0, -y)
    dst_x = max(0, x)
    dst_y = max(0, y)

    width = min(overlay.width - src_x, base.width - dst_x)
    height = min(overlay.height - src_y, base.height - dst_y)

    # Only composite if there's a valid region
    if width > 0 and height > 0:
        # Crop overlay to region that fits within base
        cropped_overlay = overlay.crop((src_x, src_y, src_x + width, src_y + height))
        base.alpha_composite(cropped_overlay, dest=(dst_x, dst_y))


# ------------------------------------------------------------
# Mask application
# ------------------------------------------------------------

def apply_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    """
    Apply an alpha mask to an image.

    Args:
        image: RGBA image
        mask: L-mode image representing alpha channel

    Returns:
        A new RGBA image with mask applied.
    """
    output = image.copy()
    output.putalpha(mask)
    return output


# ------------------------------------------------------------
# Safe PNG saving
# ------------------------------------------------------------

def save_png(image: Image.Image, path: Path) -> None:
    """
    Save an RGBA image as PNG with optimal quality settings.

    Args:
        image: RGBA image to save
        path: Output file path
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", compress_level=6, optimize=False)


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def crop_box(x: int, y: int, w: int, h: int) -> Tuple[int, int, int, int]:
    """
    Helper to build a Pillow crop box.

    Args:
        x, y: top-left coordinates
        w, h: width and height

    Returns:
        4-tuple (left, top, right, bottom)
    """
    return (x, y, x + w, y + h)
