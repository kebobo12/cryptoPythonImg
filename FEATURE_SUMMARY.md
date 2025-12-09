# Title Image Feature - Implementation Summary

## What Was Added

I've successfully added an option to use an **image as the title** instead of text in your thumbnail generator, while keeping text as the default option.

## Changes Made

### 1. Configuration Support ([thumbgen/config.py](thumbgen/config.py))
- Added `TitleImageConfig` class with properties:
  - `enabled`: Toggle between image and text title
  - `path`: Path to title image file
  - `max_width_ratio`: Maximum width as ratio of canvas (default: 0.7)
  - `scale`: Fine-tuning scale factor (default: 1.0)
- Added validation function `_validate_title_image()`
- Updated `GameConfig` to include `title_image` parameter

### 2. Asset Loading ([thumbgen/loader.py](thumbgen/loader.py))
- Added `load_title_image()` function to load the title image
- Updated `LoadedAssets` class to include `title_image` attribute
- Modified `load_assets()` to load title image when enabled

### 3. Image Rendering ([thumbgen/renderer/title_image.py](thumbgen/renderer/title_image.py))
- Created new renderer `render_title_image()` that:
  - Scales the image to fit within `max_width_ratio`
  - Applies additional `scale` parameter for fine-tuning
  - Centers the image horizontally and vertically within the blur band
  - Uses high-quality LANCZOS resampling for sharp results

### 4. Pipeline Integration ([thumbgen/pipeline.py](thumbgen/pipeline.py))
- Updated pipeline to conditionally use title image or text:
  - If `title_image.enabled = true` and image exists: renders image
  - Otherwise: falls back to traditional text rendering
- Fixed Unicode encoding issue in success message

## How to Use

### Basic Usage

Add this to your `config.json`:

```json
{
  "title_lines": ["FALLBACK", "TEXT"],
  "title_image": {
    "enabled": true,
    "path": "title.png",
    "max_width_ratio": 0.7,
    "scale": 1.0
  }
}
```

Then place your `title.png` file in the game directory.

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable title image rendering |
| `path` | string | `"title.png"` | Path to title image file |
| `max_width_ratio` | float | `0.7` | Max width as canvas ratio (0.0-1.0) |
| `scale` | float | `1.0` | Additional scaling multiplier |

## Features

✅ **Backward Compatible**: Existing configs work unchanged
✅ **Graceful Fallback**: Missing images fall back to text
✅ **High Quality**: Uses LANCZOS resampling for sharp images
✅ **Centered Positioning**: Auto-centers in blur band
✅ **Flexible Sizing**: Two-stage scaling (max_width + scale)
✅ **Transparent PNGs**: Full alpha channel support

## Testing

Run the test suite to verify everything works:

```bash
python test_title_image.py
```

The test verifies:
1. Configuration parsing works correctly
2. Backward compatibility with existing games
3. Thumbnail generation succeeds

## Files Created/Modified

### New Files
- `thumbgen/renderer/title_image.py` - Title image renderer
- `TITLE_IMAGE_FEATURE.md` - Feature documentation
- `example_config_with_title_image.json` - Example config
- `test_title_image.py` - Test suite

### Modified Files
- `thumbgen/config.py` - Added TitleImageConfig class
- `thumbgen/loader.py` - Added title image loading
- `thumbgen/pipeline.py` - Integrated title image rendering

## Example Workflow

1. **Create your title image** (e.g., in Photoshop/GIMP)
   - Use PNG format with transparency
   - White or light colors work best
   - High resolution recommended

2. **Place in game directory**
   ```
   games/my_game/
   ├── background.png
   ├── character.png
   ├── title.png         ← Your title image
   ├── provider.png
   └── config.json
   ```

3. **Enable in config.json**
   ```json
   {
     "title_image": {
       "enabled": true,
       "path": "title.png"
     }
   }
   ```

4. **Generate thumbnail**
   ```bash
   python -m thumbgen one "my_game"
   ```

## Notes

- Keep `title_lines` in your config as a fallback
- Test different `max_width_ratio` values (0.6-0.8 work well)
- Use `scale` for fine adjustments (0.8-1.2 range)
- High resolution images scale down better than up
