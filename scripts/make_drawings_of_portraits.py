import os
from PIL import Image, ImageFilter, ImageOps

input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets/images/portraits/circle'))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets/images/portraits/circle_drawing'))
os.makedirs(output_folder, exist_ok=True)

def pencil_sketch(img):
    # Convert to greyscale
    grey = img.convert('L')
    # Invert image
    inverted = ImageOps.invert(grey)
    # Blur the inverted image
    blurred = inverted.filter(ImageFilter.GaussianBlur(10))
    # Dodge blend (sketch effect)
    def dodge(front, back):
        result = min(int(front * 255 / (256 - back)), 255)
        return result
    blended = Image.new('L', img.size)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            f = grey.getpixel((x, y))
            b = blurred.getpixel((x, y))
            blended.putpixel((x, y), dodge(f, b))
    return blended

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path).convert('RGBA')
        # Create sketch
        sketch = pencil_sketch(img)
        # Combine with original alpha channel
        alpha = img.getchannel('A')
        sketch_img = Image.merge('LA', (sketch, alpha)).convert('RGBA')
        out_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_drawing.png')
        sketch_img.save(out_path)
        print(f"Saved: {out_path}")
