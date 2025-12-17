from __future__ import annotations

from PIL import Image
from ..constants import CANVAS_W, CANVAS_H
from ..utils.images import alpha_composite


def render_title_image(
    canvas: Image.Image,
    title_img: Image.Image,
    max_width_ratio: float,
    scale: float,
    y_position: int = None,
):
    """
    Render a title image inside the blurred band.

    Args:
        canvas: The main canvas to draw on.
        title_img: The title image to render.
        band_y: Y position of the band.
        band_height: Height of the band.
        max_width_ratio: Maximum width as ratio of canvas width.
        scale: Additional scaling factor for fine-tuning.

    Returns:
        Modified canvas with title image rendered.
    """

    # Calculate maximum width
    max_width = int(CANVAS_W * max_width_ratio)

    # Get original dimensions
    orig_width, orig_height = title_img.size

    # Calculate scaling to fit within max_width
    if orig_width > max_width:
        scaling_factor = max_width / orig_width
    else:
        scaling_factor = 1.0

    # Apply additional scale parameter
    scaling_factor *= scale

    # For Cleocatra-style: title should be very large and positioned low
    # Scale to fit width constraint
    target_width = int(CANVAS_W * 0.95)  # Very large title
    if orig_width > target_width:
        width_scale = target_width / orig_width
    else:
        width_scale = 1.0

    # Apply config scale
    width_scale *= scale

    # Calculate dimensions
    new_width = int(orig_width * width_scale)
    new_height = int(orig_height * width_scale)

    # Resize the title image
    title_img_scaled = title_img.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    x = (CANVAS_W - new_width) // 2

    # Use provided y_position (pixel value) or default to 83% down
    if y_position is not None:
        y = y_position
    else:
        title_center_y = int(CANVAS_H * 0.83)
        y = title_center_y - (new_height // 2)



    # Composite the title image onto the canvas
    alpha_composite(canvas, title_img_scaled, (x, y))

    return canvas
