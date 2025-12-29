"""
Asset type detection based on image characteristics.

Analyzes images to automatically classify them as:
- Background
- Character
- Title
- Provider Logo
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import logging

logger = logging.getLogger('thumbgen.asset_detector')


@dataclass
class ImageMetrics:
    """Metrics extracted from an image for classification."""
    path: Path
    width: int
    height: int
    aspect_ratio: float
    has_alpha: bool
    transparency_ratio: float  # 0.0 to 1.0
    file_size: int


@dataclass
class AssetScores:
    """Classification scores for different asset types."""
    background: float
    character: float
    title: float
    logo: float

    def get_winner(self) -> Tuple[str, float]:
        """Get the asset type with highest score."""
        scores = {
            'background': self.background,
            'character': self.character,
            'title': self.title,
            'logo': self.logo
        }
        winner = max(scores.items(), key=lambda x: x[1])
        return winner


@dataclass
class ClassifiedAssets:
    """Collection of classified assets."""
    backgrounds: List[Tuple[Path, float]]  # (path, confidence)
    characters: List[Tuple[Path, float]]
    titles: List[Tuple[Path, float]]
    logos: List[Tuple[Path, float]]
    unclassified: List[Tuple[Path, AssetScores]]  # (path, scores)


def analyze_image(path: Path) -> ImageMetrics:
    """
    Extract metrics from an image file.

    Args:
        path: Path to image file

    Returns:
        ImageMetrics with extracted properties
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
            aspect_ratio = width / height if height > 0 else 1.0
            has_alpha = img.mode in ('RGBA', 'LA', 'PA')
            file_size = path.stat().st_size

            # Calculate transparency ratio only if image has alpha channel
            if has_alpha:
                img_loaded = img.convert('RGBA')
                alpha_channel = img_loaded.split()[3]  # Get alpha channel
                alpha_data = list(alpha_channel.getdata())
                transparent_pixels = sum(1 for a in alpha_data if a < 128)  # < 50% opacity
                transparency_ratio = transparent_pixels / len(alpha_data)
            else:
                transparency_ratio = 0.0

            return ImageMetrics(
                path=path,
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                has_alpha=has_alpha,
                transparency_ratio=transparency_ratio,
                file_size=file_size
            )
    except Exception as e:
        logger.error(f"Failed to analyze image {path}: {e}")
        raise


def calculate_asset_scores(metrics: ImageMetrics) -> AssetScores:
    """
    Calculate classification scores based on image metrics.

    Args:
        metrics: Image metrics to analyze

    Returns:
        AssetScores with scores for each asset type (0-100)
    """
    # Import thresholds from constants
    from .constants import (
        ASSET_DETECTION_SCORE_DIFFERENTIAL,
        TRANSPARENCY_THRESHOLD_MIN,
        TRANSPARENCY_THRESHOLD_HIGH,
        BACKGROUND_MIN_DIMENSION,
        CHARACTER_MIN_HEIGHT,
        CHARACTER_MAX_HEIGHT,
        TITLE_MAX_HEIGHT,
        LOGO_MAX_DIMENSION,
        LANDSCAPE_RATIO,
        PORTRAIT_RATIO,
        SQUARE_MIN_RATIO,
        SQUARE_MAX_RATIO,
        TITLE_WIDE_RATIO
    )

    # Background scoring
    background_score = 0.0
    if metrics.transparency_ratio < TRANSPARENCY_THRESHOLD_MIN:  # Minimal transparency
        background_score += 40
    if metrics.aspect_ratio > LANDSCAPE_RATIO:  # Landscape
        background_score += 30
    if metrics.width >= BACKGROUND_MIN_DIMENSION or metrics.height >= BACKGROUND_MIN_DIMENSION:
        background_score += 20
    if 0.6 <= metrics.aspect_ratio <= 1.5:  # Near canvas ratio
        background_score += 10

    # Character scoring
    character_score = 0.0
    if metrics.has_alpha and metrics.transparency_ratio > TRANSPARENCY_THRESHOLD_HIGH:
        character_score += 50
    if metrics.aspect_ratio < PORTRAIT_RATIO:  # Portrait/vertical
        character_score += 25
    if CHARACTER_MIN_HEIGHT <= metrics.height <= CHARACTER_MAX_HEIGHT:
        character_score += 15
    if metrics.has_alpha and is_subject_centered(metrics):
        character_score += 10

    # Title scoring
    title_score = 0.0
    if metrics.has_alpha:
        title_score += 30
    if metrics.aspect_ratio > TITLE_WIDE_RATIO:  # Wide
        title_score += 30
    if metrics.height < TITLE_MAX_HEIGHT and metrics.width < 1200:
        title_score += 20
    if 0.15 <= metrics.transparency_ratio <= 0.85:  # Moderate transparency
        title_score += 20

    # Logo scoring
    logo_score = 0.0
    if metrics.has_alpha:
        logo_score += 35
    if metrics.width < LOGO_MAX_DIMENSION and metrics.height < LOGO_MAX_DIMENSION:
        logo_score += 35
    if SQUARE_MIN_RATIO <= metrics.aspect_ratio <= SQUARE_MAX_RATIO:  # Square-ish
        logo_score += 20
    # Simple composition check - small file size relative to dimensions suggests simple graphics
    expected_size = metrics.width * metrics.height * 4  # RGBA
    if expected_size > 0 and metrics.file_size / expected_size < 0.3:  # Highly compressed = simple
        logo_score += 10

    return AssetScores(
        background=background_score,
        character=character_score,
        title=title_score,
        logo=logo_score
    )


def is_subject_centered(metrics: ImageMetrics) -> bool:
    """
    Check if subject appears centered based on transparency distribution.

    A centered subject typically has more transparency on edges than center.
    This is a simplified heuristic.

    Args:
        metrics: Image metrics

    Returns:
        True if subject appears centered
    """
    # Simple heuristic: if transparency ratio is moderate (not too high, not too low)
    # it suggests a centered subject with transparent background
    return 0.30 <= metrics.transparency_ratio <= 0.70


def detect_asset_type(path: Path, min_confidence: float = 50.0) -> Tuple[Optional[str], float, AssetScores]:
    """
    Detect the asset type of an image.

    Args:
        path: Path to image file
        min_confidence: Minimum confidence score required (default: 50)

    Returns:
        Tuple of (asset_type, confidence, all_scores)
        asset_type will be None if confidence < min_confidence
    """
    metrics = analyze_image(path)
    scores = calculate_asset_scores(metrics)

    # Log detailed analysis
    logger.debug(f"Analyzing {path.name}:")
    logger.debug(f"  Dimensions: {metrics.width}x{metrics.height}")
    logger.debug(f"  Aspect: {metrics.aspect_ratio:.2f}")
    logger.debug(f"  Transparency: {metrics.transparency_ratio:.2%}")
    logger.debug(f"  Scores - BG:{scores.background:.0f} CH:{scores.character:.0f} "
                 f"TI:{scores.title:.0f} LG:{scores.logo:.0f}")

    asset_type, confidence = scores.get_winner()

    # Check if confidence meets minimum threshold
    if confidence < min_confidence:
        logger.warning(f"Low confidence ({confidence:.0f}) for {path.name}, requires manual classification")
        return (None, confidence, scores)

    logger.info(f"Classified {path.name} as {asset_type} (confidence: {confidence:.0f})")
    return (asset_type, confidence, scores)


def classify_game_assets(game_dir: Path, min_confidence: float = 50.0) -> ClassifiedAssets:
    """
    Scan a game directory and classify all images.

    Args:
        game_dir: Path to game directory
        min_confidence: Minimum confidence score required

    Returns:
        ClassifiedAssets with categorized images
    """
    from .constants import IMAGE_EXTENSIONS

    classified = ClassifiedAssets(
        backgrounds=[],
        characters=[],
        titles=[],
        logos=[],
        unclassified=[]
    )

    # Find all image files in the directory
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(game_dir.glob(f"*{ext}"))

    logger.info(f"Found {len(image_files)} images in {game_dir}")

    for img_path in image_files:
        try:
            asset_type, confidence, scores = detect_asset_type(img_path, min_confidence)

            if asset_type is None:
                # Low confidence - add to unclassified
                classified.unclassified.append((img_path, scores))
            elif asset_type == 'background':
                classified.backgrounds.append((img_path, confidence))
            elif asset_type == 'character':
                classified.characters.append((img_path, confidence))
            elif asset_type == 'title':
                classified.titles.append((img_path, confidence))
            elif asset_type == 'logo':
                classified.logos.append((img_path, confidence))

        except Exception as e:
            logger.error(f"Failed to classify {img_path}: {e}")
            # Add to unclassified with zero scores
            classified.unclassified.append((img_path, AssetScores(0, 0, 0, 0)))

    # Sort each category by confidence (highest first)
    classified.backgrounds.sort(key=lambda x: x[1], reverse=True)
    classified.characters.sort(key=lambda x: x[1], reverse=True)
    classified.titles.sort(key=lambda x: x[1], reverse=True)
    classified.logos.sort(key=lambda x: x[1], reverse=True)

    # Limit characters to max 3
    from .constants import MAX_CHARACTERS_AUTO_DETECT
    if len(classified.characters) > MAX_CHARACTERS_AUTO_DETECT:
        # Move extras to unclassified
        for char_path, conf in classified.characters[MAX_CHARACTERS_AUTO_DETECT:]:
            metrics = analyze_image(char_path)
            scores = calculate_asset_scores(metrics)
            classified.unclassified.append((char_path, scores))
        classified.characters = classified.characters[:MAX_CHARACTERS_AUTO_DETECT]

    logger.info(f"Classification complete: {len(classified.backgrounds)} BG, "
                f"{len(classified.characters)} CH, {len(classified.titles)} TI, "
                f"{len(classified.logos)} LG, {len(classified.unclassified)} unclassified")

    return classified
