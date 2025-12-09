from __future__ import annotations
from typing import Tuple
from PIL import Image, ImageFilter, ImageDraw
from ..constants import CANVAS_W, CANVAS_H

BAND_HEIGHT_RATIO = 0.333  # 1/3 of screen
BLUR_STRENGTH = 60  # Much stronger blur
DARKEN_BOTTOM_ALPHA = 200  # Stronger darkening


def render_bottom_band(canvas: Image.Image):
    band_h = int(CANVAS_H * BAND_HEIGHT_RATIO)
    band_y = CANVAS_H - band_h

    # extract area
    band = canvas.crop((0, band_y, CANVAS_W, CANVAS_H))
    # heavy blur
    blurred = band.filter(ImageFilter.GaussianBlur(BLUR_STRENGTH))

    # strong gradient darkener
    gradient = Image.new("RGBA", (CANVAS_W, band_h))
    g = ImageDraw.Draw(gradient)

    for y in range(band_h):
        alpha = int((y / band_h) * DARKEN_BOTTOM_ALPHA)
        g.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, alpha))

    final_band = Image.alpha_composite(blurred, gradient)
    canvas.paste(final_band, (0, band_y))
    return canvas, band_y, band_h
