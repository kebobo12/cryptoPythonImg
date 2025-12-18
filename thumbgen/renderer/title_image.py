from __future__ import annotations

from PIL import Image
from ..constants import CANVAS_W, CANVAS_H
from ..utils.images import alpha_composite


def render_title_image(
    canvas: Image.Image,
    title_img: Image.Image,
    scale: float = 1.0,
    y_position: int = None,
    provider_height: int = 0,
):
    """
    Render a title image inside the blurred band.

    Args:
        canvas: The main canvas to draw on.
        title_img: The title image to render.
        scale: Additional scaling factor for fine-tuning.
        y_position: Optional Y position override (ignored if provider_height is set).
        provider_height: Height of provider text below title (for dynamic centering).

    Returns:
        Modified canvas with title image rendered.
    """

    # Auto-scale to fit within available area (same constraints as text title)
    available_width = int(CANVAS_W * 0.92)
    # Text area height: from 68% to 95% of canvas = 27% height available
    available_height = int(CANVAS_H * 0.27)

    # Get original dimensions
    orig_width, orig_height = title_img.size

    # Calculate scale factors for both dimensions
    width_scale = available_width / orig_width
    height_scale = available_height / orig_height

    # Use the smaller scale to ensure it fits in both dimensions
    final_scale = min(width_scale, height_scale)

    # Apply config scale parameter for fine-tuning
    final_scale *= scale

    # Calculate final dimensions
    new_width = int(orig_width * final_scale)
    new_height = int(orig_height * final_scale)

    # Resize the title image
    title_img_scaled = title_img.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    x = (CANVAS_W - new_width) // 2

    # Dynamic Y positioning based on provider text
    text_area_start = int(CANVAS_H * 0.68)
    text_area_end = int(CANVAS_H * 0.95)
    available_height_area = text_area_end - text_area_start

    if provider_height > 0:
        # Center both title image and provider text within the text area
        min_gap = int(CANVAS_H * 0.04)
        total_h = new_height + min_gap + provider_height
        y = text_area_start + (available_height_area - total_h) // 2
    elif y_position is not None:
        y = y_position
    else:
        # Center the title image alone in the text area
        y = text_area_start + (available_height_area - new_height) // 2



    # Composite the title image onto the canvas
    alpha_composite(canvas, title_img_scaled, (x, y))

    return canvas
