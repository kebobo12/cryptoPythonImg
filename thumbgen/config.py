"""
Configuration loading and validation for thumbgen.

This module defines the schema for per-game `config.json` files, validates
their contents, and provides structured configuration objects used by the
pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import (
    DEFAULT_CHARACTER_HEIGHT_RATIO,
    DEFAULT_FONT_PATH,
)
from .errors import InvalidConfigError


# ------------------------------------------------------------
# Data models
# ------------------------------------------------------------

class ProviderLogoConfig:
    """
    Configuration for provider logo placement.

    Attributes:
        enabled: Whether the provider logo should be rendered.
        path: Path to the provider logo file.
        position: One of: "top_left", "top_right", "bottom_left", "bottom_right".
        max_width_ratio: Max width relative to canvas width.
        max_height_ratio: Max height relative to canvas height.
        margin: Pixel margin from edges.
        opacity: Opacity multiplier (0.0–1.0).
        invert_for_dark: Whether to invert the logo if placed on a dark band.
    """

    def __init__(
        self,
        enabled: bool = False,
        path: str = "provider.png",
        position: str = "bottom_right",
        max_width_ratio: float = 0.28,
        max_height_ratio: float = 0.12,
        margin: int = 12,
        opacity: float = 1.0,
        invert_for_dark: bool = True,
    ) -> None:
        self.enabled = enabled
        self.path = path
        self.position = position
        self.max_width_ratio = max_width_ratio
        self.max_height_ratio = max_height_ratio
        self.margin = margin
        self.opacity = opacity
        self.invert_for_dark = invert_for_dark


class TitleImageConfig:
    """
    Configuration for using an image as the title instead of text.

    Attributes:
        enabled: Whether to use an image for the title.
        path: Path to the title image file (supports PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF).
        max_width_ratio: Max width relative to canvas width.
        scale: Additional scaling factor for fine-tuning (default 1.0).
    """

    def __init__(
        self,
        enabled: bool = False,
        path: str = "title.png",
        max_width_ratio: float = 0.7,
        scale: float = 1.0,
    ) -> None:
        self.enabled = enabled
        self.path = path
        self.max_width_ratio = max_width_ratio
        self.scale = scale


class GameConfig:
    """
    Validated configuration object for a single game's thumbnail settings.
    """

    def __init__(
        self,
        title_lines: List[str],
        subtitle: str,
        provider_text: str,
        output_filename: str,
        character_height_ratio: float,
        font_path: str,
        provider_logo: ProviderLogoConfig,
        title_image: TitleImageConfig,
        layout: str = "default",
        title_text: Optional[str] = None,
        band_color: Optional[tuple] = None,
    ) -> None:
        self.title_lines = title_lines
        self.subtitle = subtitle
        self.provider_text = provider_text
        self.output_filename = output_filename
        self.character_height_ratio = character_height_ratio
        self.font_path = font_path
        self.provider_logo = provider_logo
        self.title_image = title_image

        # NEW FIELDS
        self.layout = layout                  # "default", "crypto", etc.
        self.title_text = title_text          # For crypto layout
        self.band_color = band_color          # RGB color for crypto band, None = auto-detect

# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _validate_title_lines(value: Any, folder_name: str = None) -> List[str]:
    # If title_lines not provided or empty, use folder name
    if value is None or (isinstance(value, list) and len(value) == 0):
        if folder_name:
            return [folder_name]
        raise InvalidConfigError("`title_lines` must be provided or folder name must be available.")

    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise InvalidConfigError("`title_lines` must be a list of strings.")

    return value


def _validate_provider_logo(block: Any) -> ProviderLogoConfig:
    if not isinstance(block, dict):
        return ProviderLogoConfig()  # default disabled

    return ProviderLogoConfig(
        enabled=block.get("enabled", False),
        path=block.get("path", "provider.png"),
        position=block.get("position", "bottom_right"),
        max_width_ratio=float(block.get("max_width_ratio", 0.28)),
        max_height_ratio=float(block.get("max_height_ratio", 0.12)),
        margin=int(block.get("margin", 12)),
        opacity=float(block.get("opacity", 1.0)),
        invert_for_dark=bool(block.get("invert_for_dark", True)),
    )


def _validate_title_image(block: Any) -> TitleImageConfig:
    if not isinstance(block, dict):
        return TitleImageConfig()  # default disabled

    return TitleImageConfig(
        enabled=block.get("enabled", False),
        path=block.get("path", "title.png"),
        max_width_ratio=float(block.get("max_width_ratio", 0.7)),
        scale=float(block.get("scale", 1.0)),
    )


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def load_config(path: Path) -> GameConfig:
    """
    Load and validate a game's config.json file.

    Args:
        path: Path to a config.json file.

    Returns:
        GameConfig: A validated configuration object.

    Raises:
        InvalidConfigError: If the file is missing, unreadable,
                            or contains invalid fields.
    """
    if not path.exists():
        raise InvalidConfigError(f"Config file not found: {path}")

    try:
        raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidConfigError(f"Invalid JSON in {path}: {exc}") from exc

    # Get folder name for auto-title
    folder_name = path.parent.name

    title_lines = _validate_title_lines(raw.get("title_lines"), folder_name)
    subtitle = raw.get("subtitle", "")
    provider_text = raw.get("provider_text", "")
    output_filename = raw.get("output_filename", f"{path.parent.name}.png")

    character_height_ratio = float(
        raw.get("character_height_ratio", DEFAULT_CHARACTER_HEIGHT_RATIO)
    )
    font_path = raw.get("font_path", DEFAULT_FONT_PATH)

    provider_logo = _validate_provider_logo(raw.get("provider_logo", {}))
    title_image = _validate_title_image(raw.get("title_image", {}))

    # Load layout and title_text for crypto mode
    layout = raw.get("layout", "default")
    title_text = raw.get("title_text", None)

    # Load band_color for crypto mode - can be RGB array like [10, 20, 50]
    band_color_raw = raw.get("band_color", None)
    band_color = None
    if band_color_raw and isinstance(band_color_raw, list) and len(band_color_raw) == 3:
        band_color = tuple(band_color_raw)

    return GameConfig(
        title_lines=title_lines,
        subtitle=subtitle,
        provider_text=provider_text,
        output_filename=output_filename,
        character_height_ratio=character_height_ratio,
        font_path=font_path,
        provider_logo=provider_logo,
        title_image=title_image,
        layout=layout,
        title_text=title_text,
        band_color=band_color,
    )
