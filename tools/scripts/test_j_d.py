import fitz
import cv2

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

bright_blue = (0.1, 0.45, 0.85)
teal = (0.0, 0.6, 0.55)

for c in valid_contours:
    epsilon = 0.0005 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)
    
    bx = cv2.boundingRect(c)[0]
    
    if bx < 200:
        target_shape = shape_j
        print(f"Assigned bx={bx} to J")
    else:
        target_shape = shape_d
        print(f"Assigned bx={bx} to D")
        
    pts = []
    for pt in approx:
        x = pt[0][0] - w_img/2
        y = pt[0][1] - h_img/2
        pts.append(fitz.Point(cx + x*scale, cy + y*scale))
        
    start_pt = pts[0]
    last_pt = start_pt
    target_shape.draw_line(start_pt, start_pt) 
    for pt in pts[1:]:
        target_shape.draw_line(last_pt, pt)
        last_pt = pt
    target_shape.draw_line(last_pt, start_pt) 

shape_j.finish(color=bright_blue, fill=bright_blue, even_odd=True)
shape_j.commit()

shape_d.finish(color=teal, fill=teal, even_odd=True)
shape_d.commit()

doc.save("test_j_d.pdf")
print("Saved test_j_d.pdf")
