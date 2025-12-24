# Thumbnail Generator - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Single Game Mode](#single-game-mode)
3. [Bulk Processing Mode](#bulk-processing-mode)
4. [Advanced Settings](#advanced-settings)
5. [Asset Management](#asset-management)
6. [Provider Fonts](#provider-fonts)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Launching the Application

Run the web UI launcher script:
```bash
python run_webui.py
```

The application will automatically:
- Start the Flask server on `http://127.0.0.1:5000`
- Open your default web browser
- Load all available games from the `Thumbnails` folder

### Understanding the Interface

The web UI has two main modes:
- **Single Game Mode**: Generate thumbnails one game at a time with live preview
- **Bulk Processing Mode**: Generate thumbnails for multiple games automatically

Switch between modes using the mode selector at the top of the page.

---

## Single Game Mode

### Basic Workflow

1. **Select a Game**
   - Use the search box to quickly find games by typing part of the name or provider
   - Choose a game from the dropdown menu (shows up to 8 games at once)
   - Games are organized by provider: `[Provider] Game Name`
   - The search filters games in real-time as you type

2. **Configure Settings**
   - Adjust text size, blur effects, and other visual options
   - See changes in real-time with the live preview

3. **Generate Thumbnail**
   - Click "Generate Thumbnail" button
   - The final image is saved to the `output` folder
   - Preview appears automatically after generation
   - Click "Open Output Folder" to quickly access generated thumbnails

### Title Options

**Text Mode** (Default)
- Displays the game name as text
- Uses AMA Regular font by default
- Can be customized with a different font using the "Custom Font" option

**Image Mode**
- Uses a pre-made title image (from `Title` folder)
- Useful for games with custom logos or stylized titles
- If multiple title images exist, a dropdown appears to select which one

### Provider Options

**Text Mode**
- Displays provider name as text
- Uses provider-specific font (Hacksaw → Anton, Pragmatic → Gotham Bold)

**Logo Mode**
- Displays provider logo image (from `Provider Logo` folder)
- If multiple logos exist, a dropdown appears to select which one

**None**
- Hides provider information completely

### Live Preview

The preview updates automatically when you change:
- Text scale slider
- Text offset slider
- Blur settings
- Title/Provider modes
- Font selections
- Asset selections (background, character, title, logo)

**Note**: Preview updates are debounced (200ms delay) to prevent excessive rendering.

---

## Bulk Processing Mode

### How It Works

Bulk mode processes all games in the `Thumbnails` folder automatically:
1. Scans all provider folders
2. Processes each game with the selected settings
3. Shows progress with status indicators
4. Allows editing individual games before processing

### Bulk Settings

Configure settings that apply to ALL games:

**Blur Options**
- Enable/disable blur effect
- Choose automatic or manual color
- Set custom band color (manual mode only)

**Title Mode**
- Text: Use game name text
- Image: Use title images (if available)

**Provider Mode**
- Text: Use provider name text
- Logo: Use provider logos (if available)
- None: Hide provider

**Custom Font** (Optional)
- Apply the same font to all games
- Override provider-specific fonts

### Processing Games

1. **Start Bulk Processing**
   - Click "Start Bulk Processing"
   - Games are processed one by one
   - Status updates appear next to each game

2. **Edit Individual Games**
   - Click "Edit" button next to any game
   - Opens that game in single mode
   - Customize settings specifically for that game
   - Changes apply only to that game during bulk processing

3. **Monitoring Progress**
   - ⏳ Processing: Currently being generated
   - ✓ Completed: Successfully generated
   - ✗ Failed: Error occurred (check console for details)

### Status Indicators

- **[Provider] Game Name** - Not yet processed
- **⏳ [Provider] Game Name** - Currently processing
- **✓ [Provider] Game Name** - Successfully completed
- **✗ [Provider] Game Name** - Failed (error details in console)

---

## Advanced Settings

### Text Scale

**Purpose**: Adjust the size of all text elements
**Range**: 0.5× to 2.0×
**Default**: 1.0×

**Use Cases**:
- Increase for better readability
- Decrease for longer game titles
- Fine-tune to match design requirements

### Text Offset

**Purpose**: Vertically adjust text position
**Range**: -100px to +100px
**Default**: 0px

**Use Cases**:
- Move text up (negative values)
- Move text down (positive values)
- Align text with specific background elements

### Blur Settings

**Enable Blur**: Adds a blurred band at the bottom for text readability

**Blur Scale**:
- Range: 0.5× to 2.0×
- Controls blur intensity

**Blur Mode**:
- **Automatic**: System chooses optimal color
- **Manual**: You select custom color with color picker

### Asset Selectors

When multiple assets are available, dropdown selectors appear:

**Background Selector**
- Choose which background image to use
- Always visible when multiple backgrounds exist

**Character Selector**
- Choose which character image to use
- Always visible when multiple characters exist

**Title Selector**
- Choose which title image to use
- Only visible when in Image mode AND multiple titles exist

**Logo Selector**
- Choose which provider logo to use
- Only visible when in Logo mode AND multiple logos exist

**Asset Priority**:
Files are sorted alphabetically (case-insensitive), so:
- `background.png` appears before `Christmas Carol Megaways.png`
- First file alphabetically is selected by default

---

## Asset Management

### Folder Structure

#### New Structure (Recommended) elements can be named whatever, but system will auto grab the first one in folder
```
Thumbnails/
  Provider/
    GameName/
      Backgrounds/
        background.png
        alt_background.jpg
      Character/
        character1.png
        character2.png
        character3.png
      Title/
        title.png
        title_alt.png
      Provider Logo/
        logo.png
      config.json
```

#### Old Structure (Still Supported)
```
Thumbnails/
  Provider/
    GameName/
      background.png
      character.png
      title.png
      logo.png
      config.json
```

### Asset File Types

Supported image formats:
- PNG (recommended)
- JPG/JPEG
- WebP
- BMP
- GIF
- TIFF/TIF

### Asset Requirements

**Background**:
- Recommended size: 440×590 pixels
- Fills the entire canvas

**Character**:
- Transparent background (PNG) recommended
- Up to 3 characters can be used
- Automatically positioned and scaled

**Title** (Image mode):
- Transparent background (PNG) recommended
- Replaces text title

**Provider Logo** (Logo mode):
- Transparent background (PNG) recommended
- Appears at the bottom of the card

### Multiple Assets

You can provide multiple versions of any asset:
- Place multiple files in the respective folders
- Use descriptive filenames
- Select from dropdown in the UI
- First file alphabetically is used by default

---

## Provider Fonts

### Default Provider Fonts

The system automatically applies provider-specific fonts:

**Hacksaw Gaming**:
- Font: Anton
- Used for: Provider text only

**Pragmatic Play**:
- Font: Gotham Bold
- Used for: Provider text only

**Wicked Games**:
- Font: AMA Regular
- Used for: Provider text only

**Other Providers**:
- Font: AMA Regular (default)
- Used for: Provider text only

**Note**: Title text always uses AMA Regular by default, regardless of provider. Use the "Custom Font" option to change the title font.

### Font Priority

**For Title Text:**
1. **Custom Font** (if "Custom Font" checkbox enabled and font selected)
   - Overrides the default AMA Regular font
2. **AMA Regular** (default)
   - Used when no custom font is selected

**For Provider Text:**
- Always uses the provider-specific font (e.g., Anton for Hacksaw, Gotham Bold for Pragmatic)
- Falls back to AMA Regular if no provider mapping exists

### Adding Custom Fonts

1. Place font files in the `fonts` folder
2. Fonts appear automatically in the font dropdown
3. Enable "Custom Font" checkbox
4. Select your font from the dropdown

**Supported Font Formats**:
- TTF (TrueType Font)
- OTF (OpenType Font)

### Managing Provider Fonts

**Adding New Provider Font**:
1. Place font file in appropriate subfolder (e.g., `fonts/provider_name/`)
2. Add mapping in `thumbgen/constants.py`:
   ```python
   PROVIDER_FONTS = {
       "PROVIDER NAME": "fonts/provider_name/font.ttf",
   }
   ```

**Removing Provider Font**:
- Use the "Remove Provider Font" button in the UI
- Or manually remove from `thumbgen/constants.py`

---

## Troubleshooting

### Preview Not Updating

**Problem**: Live preview doesn't refresh when changing settings

**Solutions**:
- Hard refresh browser: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Check browser console for errors (F12)

### Asset Errors When Switching Games

**Problem**: Error messages about wrong asset filenames

**Cause**: Browser cache showing old JavaScript

**Solution**:
- Hard refresh: `Ctrl+F5`
- The latest code fix prevents this issue

### Font Not Applying

**Problem**: Selected font doesn't appear in preview or saved thumbnail

**Checklist**:
- ✓ "Custom Font" checkbox is enabled
- ✓ Font is selected in dropdown
- ✓ Font file exists in `fonts` folder
- ✓ Refresh browser after adding new fonts

### Image Not Found Errors

**Problem**: "Specified background 'X' not found" error

**Causes**:
- File was deleted or moved
- Incorrect folder structure
- Case sensitivity issues (Windows vs Linux)

**Solutions**:
- Verify file exists in correct folder
- Check folder structure matches requirements
- Ensure folder names match exactly (including spaces)

### Permission Denied Errors

**Problem**: "Permission denied" when loading character

**Cause**: Trying to load a folder instead of a file

**Solution**:
- Ensure `Character` folder contains image files
- Remove any nested folders
- Files should be directly in `Character` folder, not in subfolders

### Bulk Processing Stuck

**Problem**: Bulk processing stops or hangs

**Solutions**:
- Check console for error messages
- Refresh page and restart
- Process games individually to identify problematic game
- Check that all required assets exist

### Preview Different from Saved Image

**Problem**: Live preview looks different from final saved thumbnail

**Cause**: Font mismatch or caching issue

**Solutions**:
- Verify font settings match between preview and generation
- Clear preview cache by switching games
- Check that provider fonts are correctly configured

---

## Tips and Best Practices

### Organizing Assets

1. **Use Descriptive Filenames**:
   - `background.png` (default)
   - `background_winter.png` (seasonal variant)
   - `character_happy.png`, `character_sad.png` (expressions)

2. **Keep Files Organized**:
   - Use the new folder structure (`Backgrounds/`, `Character/`, etc.)
   - Delete unused assets to avoid clutter

3. **Optimize Images**:
   - PNG for images with transparency
   - JPG for photographs
   - Keep file sizes reasonable (<2MB per image)

### Performance Tips

1. **Live Preview**:
   - Preview updates are debounced (200ms)
   - Rapid changes are batched for efficiency

2. **Bulk Processing**:
   - Close unnecessary browser tabs
   - Process in smaller batches for large collections
   - Monitor console for progress details

3. **Asset Caching**:
   - First load of each game is cached
   - Switching back to same game is faster
   - Cache is cleared when using custom asset selections

### Quality Control

1. **Use Live Preview**:
   - Verify text positioning before generating
   - Test different blur settings
   - Check character alignment

2. **Consistent Settings**:
   - Document your preferred settings
   - Use bulk mode for consistency across games
   - Save custom fonts in organized subfolders

3. **Naming Conventions**:
   - Follow alphabetical naming for default selections
   - Use prefixes for sorting (e.g., `01_background.png`, `02_background_alt.png`)

---

## Keyboard Shortcuts

Currently, the web UI does not have keyboard shortcuts. All interactions are mouse/touch-based.

---

## Output

### Output Location

Generated thumbnails are saved to:
```
output/
  game_name.png
```

**Quick Access**: Click the "Open Output Folder" button in single game mode to open the output directory in your file explorer.

### Output Format

- **Format**: PNG
- **Size**: 440×590 pixels (later we wiill support other formats)
- **Color Mode**: RGBA (with transparency)

### Filename Convention

Filenames are automatically generated from game names:
- Spaces converted to underscores
- Special characters removed
- Lowercase
- Example: "Christmas Carol Megaways" → `christmas_carol_megaways.png`

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the browser console (F12) for error messages
2. Verify your folder structure matches the requirements
3. Ensure all asset files are in correct formats
4. Try processing a simple game first to isolate the issue

For additional support, refer to the project repository or contact the developer (pls dont).
