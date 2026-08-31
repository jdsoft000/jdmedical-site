import fitz
import cv2
import numpy as np

logo_original_img = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(logo_original_img)
h_img, w_img = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]

s = 72 / 25.4
W = 1100 * s
H = 400 * s

cx = W / 2
cy = 180 * s
scale = s * 0.38

doc = fitz.open()
page = doc.new_page(width=W, height=H)

shape_j = page.new_shape()
shape_d = page.new_shape()

print("Processing contours:")
for i, c in enumerate(valid_contours):
    epsilon = 0.0005 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)
    bx = cv2.boundingRect(c)[0]
    print(f"Contour {i}: bx={bx}")
    
    if bx < 200:
        target_shape = shape_j
    else:
        target_shape = shape_d
        
    pts = []
    for pt in approx:
        x = pt[0][0] - w_img/2
        y = pt[0][1] - h_img/2
        pts.append(fitz.Point(cx + x*scale, cy + y*scale))
        
    target_shape.draw_line(pts[0], pts[0])
    last_pt = pts[0]
    for pt in pts[1:]:
        target_shape.draw_line(last_pt, pt)
        last_pt = pt
    target_shape.draw_line(last_pt, pts[0])

# Just fill with solid colors
shape_j.finish(color=(1,0,0), fill=(1,0,0)) # RED
shape_j.commit()
shape_d.finish(color=(0,1,0), fill=(0,1,0)) # GREEN
shape_d.commit()

doc.save("test_vector.pdf")
print("Saved test_vector.pdf")
