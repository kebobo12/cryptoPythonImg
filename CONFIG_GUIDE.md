# Configuration Guide

## Minimal Config (Recommended)

The simplest config that uses smart defaults:

```json
{
  "title_lines": ["MY GAME"],
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf",

  "title_image": {
    "enabled": true,
    "path": "title.png"
  },

  "provider_logo": {
    "enabled": true,
    "path": "provider.png",
    "position": "bottom_right"
  }
}
```

### What Gets Auto-Generated

- **`output_filename`** → `{folder_name}.png` (e.g., `my_game.png`)
- **`subtitle`** → `""` (empty)
- **`provider_text`** → `""` (empty)

## Full Config (All Options)

Complete config with all available options:

```json
{
  "title_lines": ["GAME", "TITLE"],
  "subtitle": "Optional subtitle",
  "provider_text": "Provider Name",
  "output_filename": "custom_name.png",
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

## Field Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title_lines` | array[string] | Title text (1-3 lines) | `["BIG BASS", "BONANZA"]` |
| `character_height_ratio` | float | Character height (0.5-0.9) | `0.74` |
| `font_path` | string | Path to TTF font file | `"C:/Windows/Fonts/arialbd.ttf"` |

### Optional Fields (Auto-Generated)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output_filename` | string | `{folder_name}.png` | Output file name |
| `subtitle` | string | `""` | Subtitle text below title |
| `provider_text` | string | `""` | Provider text (if no logo) |

### Title Image Block (Optional)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Use image instead of text |
| `path` | string | `"title.png"` | Image filename (any format) |
| `max_width_ratio` | float | `0.7` | Max width (0.0-1.0) |
| `scale` | float | `1.0` | Size multiplier |

### Provider Logo Block (Optional)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Show provider logo |
| `path` | string | `"provider.png"` | Logo filename (any format) |
| `position` | string | `"bottom_right"` | Corner placement |
| `max_width_ratio` | float | `0.28` | Max width (0.0-1.0) |
| `max_height_ratio` | float | `0.12` | Max height (0.0-1.0) |
| `margin` | integer | `12` | Edge margin (pixels) |
| `opacity` | float | `1.0` | Opacity (0.0-1.0) |
| `invert_for_dark` | boolean | `true` | Invert colors on dark band |

## Pro Tips

### 1. Omit `output_filename` for Auto-Naming

**Don't specify it:**
```json
{
  "title_lines": ["MY GAME"]
}
```
**Result:** `my_game.png` (uses folder name automatically)

### 2. Text Title (No Title Image)

**Omit the entire `title_image` block or set `enabled: false`:**
```json
{
  "title_lines": ["MY GAME", "TITLE"]
}
```

### 3. Use Any Image Format

**All these work:**
```json
"path": "title.png"     // PNG
"path": "title.jpg"     // JPG
"path": "title.webp"    // WEBP
"path": "title"         // Auto-detects any format!
```

### 4. Provider Logo Positions

Available positions:
- `"top_left"`
- `"top_right"`
- `"bottom_left"`
- `"bottom_right"` (default)

## Common Configurations

### 1. Text Title + Provider Logo
```json
{
  "title_lines": ["GAME", "NAME"],
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf",

  "provider_logo": {
    "enabled": true,
    "path": "provider.png"
  }
}
```

### 2. Image Title + Provider Logo
```json
{
  "title_lines": ["GAME", "NAME"],
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf",

  "title_image": {
    "enabled": true,
    "path": "title.png"
  },

  "provider_logo": {
    "enabled": true,
    "path": "provider.png"
  }
}
```

### 3. Text Title + No Logo
```json
{
  "title_lines": ["GAME", "NAME"],
  "provider_text": "Provider Name",
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf"
}
```

### 4. Image Title + Custom Sizing
```json
{
  "title_lines": ["FALLBACK"],
  "character_height_ratio": 0.74,
  "font_path": "C:/Windows/Fonts/arialbd.ttf",

  "title_image": {
    "enabled": true,
    "path": "title.png",
    "max_width_ratio": 0.8,
    "scale": 1.2
  }
}
```

## Validation Rules

### Title Lines
- ✅ Must be an array of strings
- ✅ Must have at least 1 line
- ✅ Typically 1-3 lines work best

### Character Height Ratio
- ✅ Float between 0.5 and 0.9
- 🎯 `0.74` is the sweet spot for most games

### Font Path
- ✅ Must be a valid path to a `.ttf` file
- 🪟 Windows: `C:/Windows/Fonts/`
- 🐧 Linux: `/usr/share/fonts/`

## Example Game Structure

```
games/my_game/
├── background.jpg          ← Any format
├── character.png           ← Any format
├── title.png              ← Optional (if title_image.enabled)
├── provider.png           ← Optional (if provider_logo.enabled)
└── config.json            ← This file
```

## Need Help?

- [TITLE_IMAGE_FEATURE.md](TITLE_IMAGE_FEATURE.md) - Title image details
- [IMAGE_FORMATS.md](IMAGE_FORMATS.md) - Format support info
- [QUICK_START_TITLE_IMAGE.md](QUICK_START_TITLE_IMAGE.md) - Quick start guide
