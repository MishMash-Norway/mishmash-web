import qrcode
from PIL import Image, ImageOps
import sys
import os

# Colors from your scheme
bg_color = "#A7A1F4"
border_color = "#C1F7AE"
qr_color = "#363644"

if len(sys.argv) < 2:
    print("Usage: python make_qr_code.py <url>")
    sys.exit(1)

data = sys.argv[1]

# Generate QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(data)
qr.make(fit=True)

img = qr.make_image(fill_color=qr_color, back_color=bg_color).convert("RGB")

# Add border
border_size = 20  # pixels
img_with_border = ImageOps.expand(img, border=border_size, fill=border_color)

img_with_border.save("qrcode_custom.png")
print("QR code saved as qrcode_custom.png")