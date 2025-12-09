# Quick Start: Using Title Images

## What's New?

You can now use **custom images as titles** instead of text in your thumbnails!

## 30-Second Setup

### Step 1: Add Configuration

Edit your game's `config.json` and add:

```json
"title_image": {
  "enabled": true,
  "path": "title.png"
}
```

### Step 2: Add Your Image

Place your title image in your game folder (same location as `background.png`).

**Supported formats:** PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF

### Step 3: Generate

Run your thumbnail generator as usual!

## Complete Example

```json
{
  "title_lines": ["MY GAME", "TITLE"],
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
  }
}
```

## Options Explained

### Basic Options
- **`enabled`**: Set to `true` to use image instead of text
- **`path`**: Name of your title image file

### Advanced Options (Optional)
- **`max_width_ratio`**: Controls how wide the image can be (0.7 = 70% of canvas width)
  - Try values: 0.6, 0.7, 0.8
- **`scale`**: Fine-tune the size
  - Try values: 0.9 (smaller), 1.0 (default), 1.1 (larger)

## Tips

1. **PNG with transparency is best** - looks cleanest on the blur band
2. **All common formats supported** - JPG, WEBP, BMP, GIF, TIFF work too
3. **Use white/light colors** - contrasts well with dark band
4. **Keep title_lines** - used as fallback if image is missing
5. **High resolution** - the script scales it down smoothly

## Disable Title Image

To go back to text, just set:
```json
"title_image": {
  "enabled": false
}
```

Or remove the entire `title_image` block.

## Need Help?

See [TITLE_IMAGE_FEATURE.md](TITLE_IMAGE_FEATURE.md) for detailed documentation.
