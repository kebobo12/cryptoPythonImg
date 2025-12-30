"""
thumbgen package entrypoint.

This module exposes a minimal public API for programmatic use:

- `generate_thumbnail`: High-level thumbnail generation function
- `load_config`: Validated config loader

All detailed rendering functionality is contained within subpackages.
"""

from .pipeline import generate_thumbnail
from .config import load_config

__all__ = [
    "generate_thumbnail",
    "load_config",
]
