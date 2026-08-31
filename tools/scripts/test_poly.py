import fitz
import cv2

logo_original_img = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(logo_original_img)
h_img, w_img = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

doc = fitz.open()
page = doc.new_page()

shape_j = page.new_shape()
shape_d = page.new_shape()

for c in contours:
    bx = cv2.boundingRect(c)[0]
    target_shape = shape_j if bx < 200 else shape_d
        
    pts = []
    for pt in c:
        pts.append(fitz.Point(100 + pt[0][0]*0.5, 100 + pt[0][1]*0.5))
        
    target_shape.draw_poly(pts)

shape_j.finish(color=(1,0,0), fill=(1,0,0), even_odd=False)
shape_j.commit()

shape_d.finish(color=(0,1,0), fill=(0,1,0), even_odd=False)
shape_d.commit()

doc.save("test_draw_poly.pdf")
print("Saved test_draw_poly.pdf")
