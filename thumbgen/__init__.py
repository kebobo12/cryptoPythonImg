"""
thumbgen package entrypoint.

This module exposes a minimal public API for programmatic use:

- `__version__`: The package version string
- `generate_thumbnail`: High-level thumbnail generation function
- `load_config`: Validated config loader

All detailed rendering functionality is contained within subpackages.
"""

from .version import __version__
from .pipeline import generate_thumbnail
from .config import load_config

__all__ = [
    "__version__",
    "generate_thumbnail",
    "load_config",
]
