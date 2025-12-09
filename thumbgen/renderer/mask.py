"""
Rounded-corner mask generator for thumbgen.

This module creates a rounded-rectangle alpha mask (default radius: 26px)
and applies it to the entire thumbnail canvas. The mask ensures every
generated thumbnail has clean, consistent rounded corners.
"""

from __future__ import annotations

from typing import Tuple

from PIL import Image, ImageDraw

from ..constants import CANVAS_W, CANVAS_H, CORNER_RADIUS
from ..utils.images import apply_mask


def create_rounded_mask() -> Image.Image:
    """
    Create an L-mode rounded corner mask for the final thumbnail.

    Returns:
        A Pillow Image in "L" mode where:
        - 255 = fully opaque
        -   0 = fully transparent
    """
    mask = Image.new("L", (CANVAS_W, CANVAS_H), 0)
    draw = ImageDraw.Draw(mask)

    draw.rounded_rectangle(
        (0, 0, CANVAS_W, CANVAS_H),
        radius=CORNER_RADIUS,
        fill=255
    )

    return mask


def apply_rounded_corners(canvas: Image.Image) -> Image.Image:
    """
    Apply the rounded-corner mask to the final canvas.

    Args:
        canvas: Completed RGBA thumbnail image

    Returns:
        A new RGBA image with rounded corners applied.
    """
    mask = create_rounded_mask()
    return apply_mask(canvas, mask)
