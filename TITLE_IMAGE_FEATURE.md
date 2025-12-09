# Title Image Feature

## Overview

The thumbnail generator now supports using an **image as the title** instead of text. This allows you to use custom logos, stylized text images, or any graphic as the main title of your thumbnail.

## How to Use

### 1. Add Title Image Configuration to `config.json`

In your game's `config.json` file, add a `title_image` block:

```json
{
  "title_lines": ["FALLBACK", "TEXT"],
  "subtitle": "",
  "provider_text": "",
  "output_filename": "my_game.png",
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf",

  "title_image": {
    "enabled": true,
    "path": "title.png",
    "max_width_ratio": 0.7,
    "scale": 1.0
  },

  "provider_logo": {
    "enabled": true,
    "path": "provider.png",
    "position": "bottom_right",
    "max_width_ratio": 0.25,
    "max_height_ratio": 0.12,
    "margin": 18,
    "opacity": 1.0,
    "invert_for_dark": true
  }
}
```

### 2. Configuration Options

#### `title_image` block:

- **`enabled`** (boolean, default: `false`): Set to `true` to use an image instead of text for the title
- **`path`** (string, default: `"title.png"`): Path to the title image file (relative to game directory)
  - **Supported formats**: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF
- **`max_width_ratio`** (float, default: `0.7`): Maximum width of the title as a ratio of canvas width (0.0 to 1.0)
- **`scale`** (float, default: `1.0`): Additional scaling factor for fine-tuning the size

### 3. Add Your Title Image

Place your title image file in the game directory alongside `background.png` and `character.png`.

**Supported formats:**
- PNG (recommended - supports transparency)
- JPG/JPEG
- WEBP
- BMP
- GIF
- TIFF

**Recommendations:**
- PNG with transparent background works best
- High resolution images scale down better
- White or light colors work best against the dark band

### 4. Generate the Thumbnail

Run the generator as usual:

```bash
# Generate one game
python -m thumbgen one "my_game"

# Generate all games
python -m thumbgen all
```

## Behavior

- **When `title_image.enabled = true` and the image exists**: The title image will be rendered instead of text
- **When `title_image.enabled = false` or image is missing**: Falls back to traditional text rendering using `title_lines`
- The title image is **centered horizontally and vertically** within the blur band
- The image is automatically scaled to fit within `max_width_ratio` while preserving aspect ratio

## Example Comparison

### Before (Text Title):
```json
{
  "title_lines": ["BIG BASS", "BONANZA 1000"]
}
```
Result: Two lines of text rendered with the specified font

### After (Image Title):
```json
{
  "title_lines": ["BIG BASS", "BONANZA 1000"],
  "title_image": {
    "enabled": true,
    "path": "title.png",
    "max_width_ratio": 0.7,
    "scale": 1.0
  }
}
```
Result: Custom title image rendered, `title_lines` acts as fallback if image is missing

## Tips

1. **Keep `title_lines` in your config** - it serves as a fallback if the image fails to load
2. **PNG is recommended** - supports transparency which blends better with the blur band
3. **Any common format works** - JPG, WEBP, BMP, GIF, TIFF are all supported (converted to RGBA automatically)
4. **Adjust `max_width_ratio`** - values between 0.6-0.8 work well for most cases
5. **Use `scale` for fine-tuning** - adjust between 0.8-1.2 for perfect sizing
6. **High resolution is better** - the script scales down smoothly but can't add detail

## Compatibility

This feature is **fully backward compatible**:
- Existing configs without `title_image` block will work unchanged
- Text rendering remains the default behavior
- All existing games continue to generate as before
