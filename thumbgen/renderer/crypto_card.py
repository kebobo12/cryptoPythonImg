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
# Dynamic text sizing and measurement
# -------------------------------------------------------------
def measure_text_block(lines, font_ratio, font_path, line_gap_ratio=0.01):
    """
    Measure total height and max width of a text block.
    Returns (total_height, max_width, [(line, font, bbox), ...])
    """
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = int(CANVAS_H * font_ratio)
    font = ImageFont.truetype(font_path or DEFAULT_FONT_PATH, size)

    total_height = 0
    max_width = 0
    line_data = []

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        max_width = max(max_width, w)
        total_height += h

        if i < len(lines) - 1:  # Add gap between lines
            total_height += int(CANVAS_H * line_gap_ratio)

        line_data.append((line, font, bbox, w, h))

    return total_height, max_width, line_data


def draw_text_block(canvas, line_data, y_start, fill):
    """
    Draw a block of text with pre-calculated font and dimensions.
    """
    draw = ImageDraw.Draw(canvas)
    current_y = y_start

    for line, font, _bbox, w, h in line_data:
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

    # 4) DYNAMIC TEXT SIZING - Calculate dimensions and adjust to fit
    # Available space: from 68% to 95% of canvas (blur band area)
    text_area_start = int(CANVAS_H * 0.68)
    text_area_end = int(CANVAS_H * 0.95)
    available_height = text_area_end - text_area_start
    available_width = int(CANVAS_W * 0.95)  # 95% width max

    # Starting font ratios
    title_font_ratio = 0.15
    provider_font_ratio = 0.048
    min_gap = int(CANVAS_H * 0.02)  # Minimum gap between title and provider

    # Iterate to find sizes that fit
    max_iterations = 10
    for iteration in range(max_iterations):
        # Measure title
        title_h, title_w, title_data = measure_text_block(
            title_lines, title_font_ratio, font_path
        )

        # Measure provider if exists
        if provider:
            provider_h, provider_w, provider_data = measure_text_block(
                [provider], provider_font_ratio, font_path
            )
            total_height = title_h + min_gap + provider_h
            max_text_width = max(title_w, provider_w)
        else:
            total_height = title_h
            max_text_width = title_w

        # Check if fits
        fits_height = total_height <= available_height
        fits_width = max_text_width <= available_width

        if fits_height and fits_width:
            break

        # Reduce font sizes
        if not fits_width:
            # Width is the issue - reduce both proportionally
            scale = available_width / max_text_width
            title_font_ratio *= scale * 0.95  # 95% to add margin
            provider_font_ratio *= scale * 0.95

        if not fits_height:
            # Height is the issue - reduce both proportionally
            scale = available_height / total_height
            title_font_ratio *= scale * 0.95
            provider_font_ratio *= scale * 0.95

        # Safety: don't go too small
        title_font_ratio = max(title_font_ratio, 0.06)
        provider_font_ratio = max(provider_font_ratio, 0.03)

    # Final measurement with adjusted sizes
    title_h, title_w, title_data = measure_text_block(
        title_lines, title_font_ratio, font_path
    )

    # Position title - centered vertically in available space
    if provider:
        provider_h, provider_w, provider_data = measure_text_block(
            [provider], provider_font_ratio, font_path
        )
        total_content_height = title_h + min_gap + provider_h
        # Center the entire block vertically
        title_y = text_area_start + (available_height - total_content_height) // 2
        provider_y = title_y + title_h + min_gap
    else:
        # Center title alone
        title_y = text_area_start + (available_height - title_h) // 2

    # 5) RENDER TEXT
    draw_text_block(canvas, title_data, title_y, (255, 255, 255, 255))

    if provider:
        draw_text_block(canvas, provider_data, provider_y, (255, 255, 255, 235))

    return canvas
