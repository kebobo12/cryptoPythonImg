"""
Asset loading utilities for thumbgen.

This module handles:
- Loading validated game configuration
- Loading required images (background, character)
- Loading optional provider logo
- Loading fonts with graceful fallback

All file-system access and error checking is centralized here, making the
rendering pipeline clean and testable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageFont

from .config import GameConfig
from .errors import (
    MissingAssetError,
    FontLoadError,
    ProviderLogoError,
)


# ------------------------------------------------------------
# Image loading
# ------------------------------------------------------------

# Supported image extensions (order matters - PNG first as most common)
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif', '.tiff', '.tif']


def find_image_file(base_path: Path) -> Optional[Path]:
    """
    Find an image file with any supported extension.

    Args:
        base_path: Path without extension (e.g., "games/mygame/background")

    Returns:
        Path to the found image file, or None if not found.

    Example:
        find_image_file(Path("games/mygame/background"))
        # Returns: Path("games/mygame/background.jpg") if that exists
    """
    # First, check if the exact path exists (user specified full filename)
    if base_path.exists():
        return base_path

    # Get the directory and base name
    parent = base_path.parent
    stem = base_path.stem if base_path.suffix else base_path.name

    # Try each extension
    for ext in IMAGE_EXTENSIONS:
        candidate = parent / f"{stem}{ext}"
        if candidate.exists():
            return candidate

    return None


def load_image(path: Path, required: bool = True) -> Optional[Image.Image]:
    """
    Load an image from disk and convert it to RGBA.
    Auto-detects image format from extensions: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        path: The path to an image file (with or without extension).
        required: Whether missing file should raise an error.

    Returns:
        Image.Image or None if optional and missing.

    Raises:
        MissingAssetError: If required and file does not exist.
    """
    # Try to find the image with any supported extension
    found_path = find_image_file(path)

    if not found_path:
        if required:
            raise MissingAssetError(f"Missing required image: {path} (tried: {', '.join(IMAGE_EXTENSIONS)})")
        return None

    try:
        img = Image.open(found_path).convert("RGBA")
        return img
    except Exception as exc:
        raise MissingAssetError(f"Failed to load image {found_path}: {exc}") from exc


def load_background(game_dir: Path) -> Image.Image:
    """
    Load background image from the game directory.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF
    """
    return load_image(game_dir / "background", required=True)


def load_character(game_dir: Path) -> Image.Image:
    """
    Load character image from the game directory.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF
    """
    return load_image(game_dir / "character", required=True)


def load_characters(game_dir: Path) -> list[Image.Image]:
    """
    Load multiple character images (character1, character2, character3, etc.).
    Falls back to single character.png if numbered files don't exist.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Returns:
        List of character images (1-3 characters)
    """
    characters = []

    # Try to load character1, character2, character3...
    for i in range(1, 4):  # Support up to 3 characters
        char_path = game_dir / f"character{i}"
        img = load_image(char_path, required=False)
        if img:
            characters.append(img)
        else:
            break  # Stop at first missing numbered character

    # If no numbered characters found, fall back to single character.png
    if not characters:
        characters.append(load_character(game_dir))

    return characters


def load_provider_logo(game_dir: Path, cfg: GameConfig) -> Optional[Image.Image]:
    """
    Load provider logo if enabled in configuration.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        game_dir: Directory containing provider logo
        cfg: GameConfig object

    Returns:
        Optional Image.Image

    Raises:
        ProviderLogoError: If loading fails unexpectedly.
    """
    if not cfg.provider_logo.enabled:
        return None

    # Try to find the logo with any extension
    logo_base = game_dir / Path(cfg.provider_logo.path).stem
    logo_path = find_image_file(logo_base)

    if not logo_path:
        # If no base match, try the exact path from config
        logo_path = game_dir / cfg.provider_logo.path
        if not logo_path.exists():
            # Missing provider logo is NOT fatal — fallback to provider_text
            return None

    try:
        return Image.open(logo_path).convert("RGBA")
    except Exception as exc:
        raise ProviderLogoError(f"Failed to load provider logo {logo_path}: {exc}") from exc


def load_title_image(game_dir: Path, cfg: GameConfig) -> Optional[Image.Image]:
    """
    Load title image if enabled in configuration.
    Auto-detects format: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

    Args:
        game_dir: Directory containing title image
        cfg: GameConfig object

    Returns:
        Optional Image.Image (always converted to RGBA)

    Raises:
        MissingAssetError: If enabled but file doesn't exist or can't be loaded.
    """
    if not cfg.title_image.enabled:
        return None

    # Try to find the title image with any extension
    title_base = game_dir / Path(cfg.title_image.path).stem
    title_path = find_image_file(title_base)

    if not title_path:
        # If no base match, try the exact path from config
        title_path = game_dir / cfg.title_image.path
        if not title_path.exists():
            # Missing title image is NOT fatal — fallback to text title
            return None

    try:
        img = Image.open(title_path)
        # Convert to RGBA to ensure transparency support
        # Works with PNG, JPG, WEBP, BMP, GIF, TIFF, etc.
        return img.convert("RGBA")
    except Exception as exc:
        raise MissingAssetError(f"Failed to load title image {title_path}: {exc}") from exc


# ------------------------------------------------------------
# Font loading
# ------------------------------------------------------------

def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TrueType font.

    Args:
        font_path: Path to .ttf file.
        size: Font size in pixels.

    Returns:
        Loaded TrueTypeFont.

    Raises:
        FontLoadError: If font cannot be loaded.
    """
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception as exc:
        raise FontLoadError(f"Failed to load font '{font_path}': {exc}") from exc


# ------------------------------------------------------------
# Unified asset bundle
# ------------------------------------------------------------

class LoadedAssets:
    """
    Bundles all game assets after loading from disk.

    Attributes:
        background: Background image.
        character: Character image with transparency (deprecated, use characters).
        characters: List of character images (1-3).
        provider_logo: Optional provider logo.
        title_image: Optional title image to use instead of text.
    """
    def __init__(
        self,
        background: Image.Image,
        character: Image.Image,
        characters: list[Image.Image],
        provider_logo: Optional[Image.Image],
        title_image: Optional[Image.Image],
    ) -> None:
        self.background = background
        self.character = character  # Keep for backward compatibility
        self.characters = characters
        self.provider_logo = provider_logo
        self.title_image = title_image


def load_assets(game_dir: Path, cfg: GameConfig) -> LoadedAssets:
    """
    Load all image assets for a game in one call.

    Args:
        game_dir: Path to game directory
        cfg: Validated GameConfig

    Returns:
        LoadedAssets: container object with images
    """
    background = load_background(game_dir)
    characters = load_characters(game_dir)
    provider_logo = load_provider_logo(game_dir, cfg)
    title_image = load_title_image(game_dir, cfg)

    return LoadedAssets(
        background=background,
        character=characters[0],  # For backward compatibility
        characters=characters,
        provider_logo=provider_logo,
        title_image=title_image,
    )
