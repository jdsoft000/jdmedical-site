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
cv2.imwrite("d_part.png", d_part)
print("Saved d_part.png")
