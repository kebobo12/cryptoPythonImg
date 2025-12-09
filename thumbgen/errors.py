"""
Custom exception classes for the thumbgen system.

These exceptions allow the pipeline, loader, and CLI to report clear,
structured errors that are easier to debug and catch.
"""


class ThumbgenError(Exception):
    """
    Base class for all thumbgen-related errors.
    """
    pass


class InvalidConfigError(ThumbgenError):
    """
    Raised when config.json is missing required fields
    or contains invalid values.
    """
    pass


class MissingAssetError(ThumbgenError):
    """
    Raised when required assets such as background.png or character.png
    cannot be found for a game.
    """
    pass


class FontLoadError(ThumbgenError):
    """
    Raised when the configured font file cannot be loaded.
    """
    pass


class ProcessingError(ThumbgenError):
    """
    Raised when a general processing error occurs during rendering.
    """
    pass


class ProviderLogoError(ThumbgenError):
    """
    Raised when provider logo loading or placement fails.
    """
    pass
