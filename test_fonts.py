"""Test font rendering to verify fonts are different"""
from PIL import Image, ImageDraw, ImageFont

# Create test image
img = Image.new('RGBA', (400, 200), (255, 255, 255, 255))
draw = ImageDraw.Draw(img)

# Load both fonts
ama_font = ImageFont.truetype('fonts/ama_squiggly/AMA-Regular.ttf', 32)
gotham_font = ImageFont.truetype('fonts/pragmatic/Gotham Bold/Gotham Bold.otf', 32)

# Draw text with both fonts
draw.text((10, 10), "Pragmatic (AMA Font)", font=ama_font, fill=(0, 0, 0, 255))
draw.text((10, 60), "Pragmatic (Gotham Font)", font=gotham_font, fill=(0, 0, 0, 255))

# Save
img.save('test_font_comparison.png')
print("Saved test_font_comparison.png")
print(f"AMA font: {ama_font}")
print(f"Gotham font: {gotham_font}")
