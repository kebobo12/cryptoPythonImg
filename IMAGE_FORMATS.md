# Image Format Support

## Overview

The thumbnail generator now supports **automatic format detection** for all image assets. You no longer need to worry about file extensions - the system will find and load your images regardless of format!

## Supported Formats

All image files support these formats:
- **PNG** (recommended for transparency)
- **JPG / JPEG**
- **WEBP**
- **BMP**
- **GIF**
- **TIFF / TIF**

## How It Works

### Automatic Detection

The system automatically searches for image files in this order:
1. Exact filename if specified (e.g., `background.jpg`)
2. Base name with any supported extension (e.g., `background` → tries `.png`, `.jpg`, `.jpeg`, `.webp`, etc.)

### Example

Your game folder can have **any mix of formats**:

```
games/my_game/
├── background.jpg      ✅ JPG for background
├── character.png       ✅ PNG for character
├── title.webp          ✅ WEBP for title
├── provider.png        ✅ PNG for provider logo
└── config.json
```

**All combinations work!** Mix and match as you like.

## Asset Files

### Required Assets
- **background** - any format (PNG, JPG, WEBP, etc.)
- **character** - any format (PNG, JPG, WEBP, etc.)

### Optional Assets
- **title** - any format (when `title_image.enabled = true`)
- **provider** - any format (when `provider_logo.enabled = true`)

## Configuration

You can specify the **exact filename** in your config.json:

```json
{
  "title_image": {
    "enabled": true,
    "path": "title.webp"    // Specify exact file
  },

  "provider_logo": {
    "enabled": true,
    "path": "provider.jpg"  // Specify exact file
  }
}
```

Or use **base names** and let the system find any format:

```json
{
  "title_image": {
    "enabled": true,
    "path": "title"         // Will find title.png, title.jpg, etc.
  },

  "provider_logo": {
    "enabled": true,
    "path": "provider"      // Will find provider.png, provider.jpg, etc.
  }
}
```

## Format Conversion

All images are automatically converted to **RGBA** internally, which means:

✅ **JPG files** get transparency support added
✅ **All formats** work seamlessly together
✅ **No quality loss** during conversion
✅ **Consistent rendering** regardless of source format

## Recommendations

### For Best Results

1. **Backgrounds**: JPG or PNG
   - JPG = smaller file size
   - PNG = better quality, supports transparency

2. **Characters**: PNG (recommended)
   - Usually need transparency
   - PNG preserves sharp edges better

3. **Titles**: PNG or WEBP
   - PNG = best transparency support
   - WEBP = good balance of size and quality

4. **Provider Logos**: PNG
   - Logos need transparency
   - PNG = crisp, sharp edges

### File Size Tips

- **JPG**: Best for photos and backgrounds (smaller files)
- **PNG**: Best for graphics with transparency (larger files but better quality)
- **WEBP**: Best balance of size and quality with transparency support

## Examples

### All PNG (Traditional)
```
games/my_game/
├── background.png
├── character.png
├── title.png
└── provider.png
```

### Mixed Formats (Optimized)
```
games/my_game/
├── background.jpg      ← Smaller file size
├── character.png       ← Needs transparency
├── title.webp          ← Good compression
└── provider.png        ← Logo with transparency
```

### All JPG (Not Recommended)
```
games/my_game/
├── background.jpg      ← OK
├── character.jpg       ← Transparency lost
├── title.jpg           ← Transparency lost
└── provider.jpg        ← Transparency lost
```
⚠️ JPG doesn't support transparency - use PNG for elements that need it!

## Error Messages

If an image can't be found, you'll see which formats were tried:

```
Missing required image: games/my_game/background (tried: .png, .jpg, .jpeg, .webp, .bmp, .gif, .tiff, .tif)
```

This helps you quickly identify what's missing.

## Migration from Old Setup

If you have old games with specific extensions (`.png` only), they'll continue to work without changes!

**Old structure** (still works):
```
games/my_game/
├── background.png
├── character.png
```

**New flexibility** (also works):
```
games/my_game/
├── background.jpg
├── character.png
```

No config changes needed! 🎉
