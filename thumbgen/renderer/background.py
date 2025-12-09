"""
Background rendering module for thumbgen.

This component is responsible for:
- Fitting the background image into the final 332×460 canvas
- Applying an upward center bias (to preserve headroom/sky)
- Ensuring the output is an RGBA canvas ready for further compositing
"""

from __future__ import annotations

from typing import Tuple

from PIL import Image, ImageOps

from ..constants import CANVAS_W, CANVAS_H


def render_background(bg: Image.Image) -> Image.Image:
    """
    Fit the background image into the fixed canvas size using high-quality
    resizing, applying an upward centering bias.

    The bias keeps more of the upper area visible (e.g., sky, glowing effects),
    which is consistent with modern casino promo card styling.

    Args:
        bg: Source background image (any size)

    Returns:
        A new RGBA image sized (332×460) with the background fitted inside.
    """
    canvas_size: Tuple[int, int] = (CANVAS_W, CANVAS_H)

    # Centering = (0.5, 0.35):
    #   - 0.5 = horizontal perfect center
    #   - 0.35 = vertical upward bias
    fitted = ImageOps.fit(
        bg,
        canvas_size,
        method=Image.LANCZOS,
        centering=(0.5, 0.00)

    )

    return fitted.convert("RGBA")
