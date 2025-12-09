"""
Advanced provider logo rendering module for thumbgen.

This component handles:
- Loading and scaling provider logos
- Automatic placement in one of four corners
- Configurable margin and opacity
- Optional inversion for dark backgrounds to improve contrast
- Graceful fallback when provider logo is missing

The logo is always drawn AFTER the text block to avoid overlap issues.
"""

from __future__ import annotations

from typing import Tuple

from PIL import Image, ImageOps

from .config import GameConfig
from .errors import ProviderLogoError
from .constants import CANVAS_W, CANVAS_H


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _invert_if_needed(logo: Image.Image, invert: bool) -> Image.Image:
    """
    Optionally invert the logo for contrast on dark bands.

    Args:
        logo: Source logo image
        invert: Whether inversion is requested

    Returns:
        A new logo image (inverted if enabled)
    """
    if not invert:
        return logo

    # Pillow's invert works only on RGB or L mode images
    rgb_logo = logo.convert("RGB")
    inverted = ImageOps.invert(rgb_logo).convert("RGBA")
    return inverted


def _scale_logo(
    logo: Image.Image,
    cfg: GameConfig
) -> Image.Image:
    """
    Scale the provider logo according to width/height constraints.

    Args:
        logo: Source provider logo image
        cfg: GameConfig object

    Returns:
        Scaled RGBA image
    """
    pl = cfg.provider_logo

    max_w = int(CANVAS_W * pl.max_width_ratio)
    max_h = int(CANVAS_H * pl.max_height_ratio)

    w, h = logo.size

    # Determine scale factor
    scale = min(max_w / w, max_h / h)
    new_size = (int(w * scale), int(h * scale))

    return logo.resize(new_size, Image.LANCZOS)


def _compute_position(
    canvas_size: Tuple[int, int],
    logo_size: Tuple[int, int],
    position: str,
    margin: int
) -> Tuple[int, int]:
    """
    Compute placement coordinates for the provider logo.

    Args:
        canvas_size: (canvas_width, canvas_height)
        logo_size: (logo_width, logo_height)
        position: One of four supported positions
        margin: Pixel margin from edges

    Returns:
        (x, y) top-left coordinate for placement
    """
    cw, ch = canvas_size
    lw, lh = logo_size

    if position == "top_left":
        return (margin, margin)

    if position == "top_right":
        return (cw - lw - margin, margin)

    if position == "bottom_left":
        return (margin, ch - lh - margin)

    if position == "bottom_right":
        return (cw - lw - margin, ch - lh - margin)

    raise ProviderLogoError(f"Invalid provider logo position: {position}")


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def render_provider_logo(
    canvas: Image.Image,
    logo: Image.Image,
    cfg: GameConfig
) -> Image.Image:
    """
    Draw the provider logo on the final canvas using advanced placement rules.

    Args:
        canvas: Completed canvas after background/character/band/text
        logo: Provider logo image (already loaded)
        cfg: Validated game configuration

    Returns:
        Modified canvas with provider logo composited.
    """

    pl = cfg.provider_logo

    # Step 1: Optional inversion for dark backgrounds
    logo = _invert_if_needed(logo, pl.invert_for_dark)

    # Step 2: Scaling
    scaled = _scale_logo(logo, cfg)

    # Step 3: Compute final placement
    x, y = _compute_position(
        canvas_size=(CANVAS_W, CANVAS_H),
        logo_size=scaled.size,
        position=pl.position,
        margin=pl.margin
    )

    # Step 4: Apply opacity
    if pl.opacity < 1.0:
        alpha = scaled.split()[3]
        alpha = alpha.point(lambda a: int(a * pl.opacity))
        scaled.putalpha(alpha)

    # Step 5: Composite onto canvas
    canvas.alpha_composite(scaled, dest=(x, y))

    return canvas
