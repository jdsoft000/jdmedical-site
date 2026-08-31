import fitz
import cv2
import numpy as np

pdf_path = r"c:\Users\HOME\Desktop\JD_Motto_Banner_Horizontal.pdf"
doc = fitz.open(pdf_path)
page = doc[0]

pix = page.get_pixmap(dpi=72)
img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
if pix.n == 4:
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
elif pix.n == 3:
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

h, w = img.shape[:2]
cx, cy = w // 2, int(h * 0.45) 

d_part = img[cy-50:cy+50, cx+50:cx+150]
teal_pixels = np.sum((d_part[:,:,0] > 100) & (d_part[:,:,1] > 100) & (d_part[:,:,2] < 50))
print(f"Teal pixels in D region: {teal_pixels}")

gray = cv2.cvtColor(d_part, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
thresh_small = cv2.resize(thresh, (40, 20))
print("\nASCII of D part:")
for y in range(20):
    row = ""
    for x in range(40):
        row += "#" if thresh_small[y, x] > 127 else "."
    print(row)
