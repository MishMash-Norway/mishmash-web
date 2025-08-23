import os
from PIL import Image, ImageDraw

input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets/images/portraits/square'))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets/images/portraits/circle'))
os.makedirs(output_folder, exist_ok=True)

MAX_SIZE = 300

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path).convert("RGBA")
        size = min(img.size)
        # Center crop to square
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        right = left + size
        bottom = top + size
        img = img.crop((left, top, right, bottom))

        # Resize if necessary
        if size > MAX_SIZE:
            img = img.resize((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
            size = MAX_SIZE

        # Create mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        # Apply mask
        result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)

        out_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '.png')
        result.save(out_path)
        print(f"Saved: {out_path}")