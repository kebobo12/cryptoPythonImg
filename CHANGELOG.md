# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **BETA: Custom Output Dimensions** - Bulk mode now supports custom canvas sizes with preset buttons (Square, 16:9) and live aspect ratio display
- Provider fonts support with JSON configuration for per-provider custom fonts
- Live preview updates during single game processing
- Title image support for logo-based thumbnails instead of text
- Provider logo display with configurable positioning

### Fixed
- Vertical line artifact on blur band (glow edge bleeding at canvas boundaries)
- Safe alpha compositing with boundary clipping to prevent edge artifacts
- Character glow rendering now uses padded canvas approach

### Changed
- Refactored rendering pipeline to support dynamic canvas dimensions
- Improved blur background handling with parameterized sizes
- Updated text measurement and drawing functions for flexible layouts

### Removed
- Old test scripts and development files
- Outdated configuration examples
- Legacy build scripts
- Python bytecode cache files from repository

## [1.0.0] - Initial Release

### Added
- Core thumbnail generation with background blur effects
- Character compositing with glow effects
- Title text rendering with custom fonts
- Provider text display
- Single game and bulk processing modes
- Web UI with Flask backend
- Asset management system
- Configurable blur bands and text positioning
