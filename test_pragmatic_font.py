"""Test rendering Pragmatic with Gotham Bold"""
from PIL import Image, ImageDraw, ImageFont

# Create test image
img = Image.new('RGBA', (400, 100), (0, 128, 0, 255))  # Green background
draw = ImageDraw.Draw(img)

# Load Gotham Bold
gotham_font = ImageFont.truetype('fonts/pragmatic/Gotham Bold/Gotham Bold.otf', 28)

# Draw "Pragmatic" with Gotham Bold
draw.text((50, 30), "Pragmatic", font=gotham_font, fill=(255, 255, 255, 255))

# Save
img.save('test_pragmatic_gotham.png')
print("Saved test_pragmatic_gotham.png")
print(f"Font object: {gotham_font}")
print(f"Font family: {gotham_font.getname()}")
