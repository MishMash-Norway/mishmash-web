import os
from PIL import Image

def convert_folder_to_greyscale(input_folder, output_folder, preserve_transparency=False):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(input_folder, filename)
            img = Image.open(img_path)
            if preserve_transparency and img.mode in ('RGBA', 'LA'):
                # Split alpha channel
                alpha = img.getchannel('A')
                # Convert RGB to greyscale
                greyscale = img.convert('L')
                # Merge greyscale and alpha
                img = Image.merge('LA', (greyscale, alpha)).convert('RGBA')
            else:
                img = img.convert('L')
            out_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '_greyscale.png')
            img.save(out_path)
            print(f"Saved: {out_path}")

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../assets/images/portraits'))
folders = ['square', 'circle']

for folder in folders:
    input_folder = os.path.join(base_dir, folder)
    output_folder = os.path.join(base_dir, folder + '_greyscale')
    preserve_transparency = (folder == 'circle')
    convert_folder_to_greyscale(input_folder, output_folder, preserve_transparency=preserve_transparency)
