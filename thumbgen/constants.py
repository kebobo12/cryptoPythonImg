"""
Global constants for the thumbgen rendering system.

These values define the standard visual style and default processing
parameters for all generated thumbnails. They can be overridden in config.json
on a per-game basis if needed.
"""

from typing import Tuple

# -----------------------------------------------------------
# Canvas specifications
# -----------------------------------------------------------

CANVAS_SIZE: Tuple[int, int] = (440, 590)  # Standard casino card dimensions
#CANVAS_SIZE: Tuple[int, int] = (300, 300)  # Old square format

CANVAS_W: int = CANVAS_SIZE[0]
CANVAS_H: int = CANVAS_SIZE[1]

# Rounded corner radius (pixels)
CORNER_RADIUS: int = 26

# -----------------------------------------------------------
# Bottom band (blur & gradient overlay)
# -----------------------------------------------------------

# Percentage (0–1) of the canvas height reserved for the bottom band
BAND_HEIGHT_RATIO: float = 0

# Gaussian blur strength applied to the band
BLUR_STRENGTH: int = 0

# Darkening gradient alpha values (0–255)
DARKEN_TOP_ALPHA: int = 0
DARKEN_BOTTOM_ALPHA: int = 190

# Vertical offset inside band before first text line (0–1)
TEXT_GROUP_TOP_OFFSET_RATIO: float = 0.10

# Gap between text lines (ratio of canvas height)
LINE_GAP_RATIO: float = 0.02

# -----------------------------------------------------------
# Character placement defaults
# -----------------------------------------------------------

# Default character height ratio if not specified in config.json
DEFAULT_CHARACTER_HEIGHT_RATIO: float = 0.72

# Vertical anchor point: character bottom aligns to this fraction of canvas height
CHAR_BOTTOM_ANCHOR_RATIO: float = 0.58

# Horizontal spacing between multiple characters (as ratio of canvas width)
CHAR_SPACING_RATIO: float = 0.05  # 5% spacing between characters

# Minimum margin from canvas edges (as ratio of canvas width)
CHAR_MARGIN_RATIO: float = 0.05  # 5% margin from edges

# Maximum total width for all characters (as ratio of canvas width)
CHAR_MAX_WIDTH_RATIO: float = 0.90  # Characters use max 90% of canvas width

# -----------------------------------------------------------
# Font configuration
# -----------------------------------------------------------

# Default font path (use AMA-Regular as default)
from pathlib import Path
_project_root = Path(__file__).parent.parent
DEFAULT_FONT_PATH: str = str(_project_root / "fonts/ama_squiggly/AMA-Regular.ttf")

# Text size ratios relative to canvas height
TITLE_FONT_RATIO: float = 0.11
SUBTITLE_FONT_RATIO: float = 0.07
PROVIDER_FONT_RATIO: float = 0.06

# Text shadow offset
TEXT_SHADOW_OFFSET: Tuple[int, int] = (2, 2)
SHADOW_ALPHA: int = 150  # 0–255
WHITE_ALPHA: int = 255   # 0–255

# -----------------------------------------------------------
# Provider-specific fonts (crypto layout)
# -----------------------------------------------------------

# Mapping of provider names to their specific fonts
# Provider names are normalized (uppercase, no special chars)
def _get_provider_font_map():
    """Get provider fonts map with absolute paths."""
    from pathlib import Path

    # Find the project root (where fonts/ directory is)
    # This file is in thumbgen/constants.py, so go up one level
    project_root = Path(__file__).parent.parent

    return {
        "HACKSAW GAMING": str(project_root / "fonts/hacksaw/anton.ttf"),
        "HACKSAW": str(project_root / "fonts/hacksaw/anton.ttf"),
        "PRAGMATIC PLAY": str(project_root / "fonts/pragmatic/Gotham Bold/Gotham Bold.otf"),
        "PRAGMATIC": str(project_root / "fonts/pragmatic/Gotham Bold/Gotham Bold.otf"),
        "WICKED GAMES": str(project_root / "fonts/ama_squiggly/AMA-Regular.ttf"),
    }

PROVIDER_FONTS = _get_provider_font_map()

def get_provider_font(provider_name: str, fallback: str = None) -> str:
    """
    Resolve provider font with a UI-first approach.

    Priority:
    1) If caller supplies a fallback (e.g., UI provider font or custom font), use it.
    2) Otherwise, fall back to DEFAULT_FONT_PATH.
    """
    if fallback is None:
        fallback = DEFAULT_FONT_PATH

    return fallback
