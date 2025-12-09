from __future__ import annotations
from PIL import Image, ImageFilter, ImageDraw, ImageFont

from ..constants import CANVAS_W, CANVAS_H, DEFAULT_FONT_PATH
from ..utils.images import alpha_composite


# -------------------------------------------------------------
# Background Blur + Fade
# -------------------------------------------------------------
def crypto_blur_background(bg: Image.Image) -> Image.Image:
    # Scale background to cover canvas while preserving aspect ratio
    # This prevents stretching and shows more background content
    bg_ratio = bg.width / bg.height
    canvas_ratio = CANVAS_W / CANVAS_H

    if bg_ratio > canvas_ratio:
        # Background is wider - fit to height
        new_h = CANVAS_H
        new_w = int(bg.width * (CANVAS_H / bg.height))
    else:
        # Background is taller - fit to width
        new_w = CANVAS_W
        new_h = int(bg.height * (CANVAS_W / bg.width))

    # Resize preserving aspect ratio
    bg_resized = bg.resize((new_w, new_h), Image.LANCZOS).convert("RGBA")

    # Center crop to canvas size
    left = (new_w - CANVAS_W) // 2
    top = (new_h - CANVAS_H) // 2
    bg_cropped = bg_resized.crop((left, top, left + CANVAS_W, top + CANVAS_H))

    # No blur - keep background sharp and clear
    # Just apply a subtle gradient for text contrast
    fade = Image.new("RGBA", (CANVAS_W, CANVAS_H))
    draw = ImageDraw.Draw(fade)

    for y in range(CANVAS_H):
        # Very subtle gradient - from 0 at top to 80 at bottom
        alpha = int(80 * (y / CANVAS_H))
        draw.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(bg_cropped, fade)


# -------------------------------------------------------------
# Multi-line centered text helper
# -------------------------------------------------------------
def draw_centered_lines(canvas, lines, y_start, font_ratio, fill, font_path=None):
    draw = ImageDraw.Draw(canvas)
    current_y = y_start

    for line in lines:
        size = int(CANVAS_H * font_ratio)
        font = ImageFont.truetype(font_path or DEFAULT_FONT_PATH, size)

        # Use textbbox instead of deprecated textsize
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        x = (CANVAS_W - w) // 2
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += h + int(CANVAS_H * 0.01)


# -------------------------------------------------------------
# MAIN RENDERER - Pragmatic Play style
# -------------------------------------------------------------
def render_crypto_card(background, character, title_lines, provider, font_path=None, band_color=None):
    # 1) Background - heavily blurred with strong dark gradient
    canvas = crypto_blur_background(background)

    # Use provided font path or fallback
    if not font_path:
        font_path = DEFAULT_FONT_PATH

    # 2) Character - VERY LARGE, centered, dominant element
    # Scale to fill canvas consistently - use both width and height constraints
    max_width = int(CANVAS_W * 0.95)  # Allow 95% of canvas width
    max_height = int(CANVAS_H * 0.85)  # Allow 85% of canvas height

    # Calculate scale factors for both dimensions
    width_scale = max_width / character.width
    height_scale = max_height / character.height

    # Use the larger scale to ensure character fills the space
    scale = max(width_scale, height_scale)

    w = int(character.width * scale)
    h = int(character.height * scale)

    cx = (CANVAS_W - w) // 2
    cy = int(CANVAS_H * 0.02)  # Start very near top

    resized = character.resize((w, h), Image.LANCZOS)

    # Strong glow behind character for depth
    glow = resized.filter(ImageFilter.GaussianBlur(50))
    glow = glow.point(lambda p: int(p * 0.7))  # Brighter glow

    alpha_composite(canvas, glow, (cx - 20, cy - 20))
    alpha_composite(canvas, resized, (cx, cy))

    # 3) BOTTOM BLUR BAND - 33% of screen with gradient fade
    band_start_y = int(CANVAS_H * 0.67)  # Start at 67% down (33% of screen)
    band_height = CANVAS_H - band_start_y

    # Extract and blur the band area
    band_section = canvas.crop((0, band_start_y, CANVAS_W, CANVAS_H))
    blurred_band = band_section.filter(ImageFilter.GaussianBlur(25))

    # Create gradient mask for smooth transition
    mask = Image.new("L", (CANVAS_W, band_height))
    mask_draw = ImageDraw.Draw(mask)

    transition_height = int(band_height * 0.2)  # 20% of band for transition

    for y in range(band_height):
        if y < transition_height:
            # Fade from sharp to blurred
            alpha = int(255 * (y / transition_height))
        else:
            # Fully blurred
            alpha = 255
        mask_draw.line([(0, y), (CANVAS_W, y)], fill=alpha)

    # Composite blurred band with mask
    canvas.paste(blurred_band, (0, band_start_y), mask)

    # Determine band color: use most common color if not specified
    if band_color is None:
        # Get most common color from bottom 33% of image
        bottom_section = canvas.crop((0, band_start_y, CANVAS_W, CANVAS_H))
        # Resize to small size for faster color analysis
        small = bottom_section.resize((50, 50), Image.LANCZOS)
        # Get colors
        colors = small.getcolors(2500)  # Get up to 2500 colors
        if colors:
            # Find most common color (excluding very dark/black pixels)
            colors = sorted(colors, key=lambda x: x[0], reverse=True)
            for count, color in colors:
                if isinstance(color, int):  # Grayscale
                    if color > 20:  # Skip very dark
                        band_color = (color, color, color)
                        break
                else:  # RGB/RGBA
                    r, g, b = color[:3]
                    if r + g + b > 60:  # Skip very dark
                        band_color = (r, g, b)
                        break

        # Fallback to black if no suitable color found
        if band_color is None:
            band_color = (0, 0, 0)

    # Create dark gradient overlay: fade from top to bottom
    dark_overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw_dark = ImageDraw.Draw(dark_overlay)

    for y in range(band_start_y, CANVAS_H):
        relative_y = y - band_start_y
        progress = relative_y / band_height

        # Smooth curve: starts at 0%, peaks at middle, fades to nearly 0% at bottom
        # Using a sine-like curve for smooth fade
        if progress < 0.5:
            # First half: 0% -> 90% (rise)
            alpha = int(230 * (progress * 2))  # 0 to 230
        else:
            # Second half: 90% -> 5% (fall)
            fade_progress = (progress - 0.5) * 2  # 0 to 1
            alpha = int(230 * (1 - fade_progress * 0.95))  # 230 to 12 (5% of 255)

        # Use black for darkening
        draw_dark.line([(0, y), (CANVAS_W, y)], fill=(0, 0, 0, alpha))

    canvas = Image.alpha_composite(canvas, dark_overlay)

    # 4) TITLE TEXT - 15% of image height, positioned lower
    text_y = int(CANVAS_H * 0.68)  # Lower position

    draw_centered_lines(
        canvas,
        title_lines,
        y_start=text_y,
        font_ratio=0.15,  # 15% of total image height
        fill=(255, 255, 255, 255),
        font_path=font_path
    )

    # 5) PROVIDER TEXT - much closer to title with minimal gap
    if provider:
        draw_centered_lines(
            canvas,
            [provider],
            y_start=int(CANVAS_H * 0.88),  # Close to title, minimal gap
            font_ratio=0.048,
            fill=(255, 255, 255, 235),
            font_path=font_path
        )

    return canvas
