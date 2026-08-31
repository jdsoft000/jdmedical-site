import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(img_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

valid_contours = []
for i, c in enumerate(contours):
    area = cv2.contourArea(c)
    if area > 1000:
        valid_contours.append((i, c, hierarchy[0][i]))
        print(f"Contour {i}: area={area}, hierarchy={hierarchy[0][i]}")

# Save the shape code
with open("draw_logo_code.py", "w") as f:
    f.write("def draw_clean_logo(page, cx, cy, scale=1.0):\n")
    f.write("    shape = page.new_shape()\n")
    for idx, c, hier in valid_contours:
        # Simplify contour
        epsilon = 0.0005 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        
        f.write("    # Contour\n")
        x, y = approx[0][0]
        f.write(f"    shape.draw_line(fitz.Point(cx + ({x - img.shape[1]/2})*scale, cy + ({y - img.shape[0]/2})*scale), fitz.Point(cx + ({x - img.shape[1]/2})*scale, cy + ({y - img.shape[0]/2})*scale))\n")
        f.write(f"    last_pt = fitz.Point(cx + ({x - img.shape[1]/2})*scale, cy + ({y - img.shape[0]/2})*scale)\n")
        
        for pt in approx[1:]:
            x, y = pt[0]
            f.write(f"    npt = fitz.Point(cx + ({x - img.shape[1]/2})*scale, cy + ({y - img.shape[0]/2})*scale)\n")
            f.write(f"    shape.draw_line(last_pt, npt)\n")
            f.write(f"    last_pt = npt\n")
        f.write("    shape.draw_line(last_pt, fitz.Point(cx + ({approx[0][0][0] - img.shape[1]/2})*scale, cy + ({approx[0][0][1] - img.shape[0]/2})*scale))\n".replace("{approx[0][0][0] - img.shape[1]/2}", str(approx[0][0][0] - img.shape[1]/2)).replace("{approx[0][0][1] - img.shape[0]/2}", str(approx[0][0][1] - img.shape[0]/2)))
        
        # If it has no parent, we commit with color depending on its X position
        if hier[3] == -1: # Outer contour
            # Get bounding box to check if it's left (J) or right (D)
            bx, by, bw, bh = cv2.boundingRect(c)
            color_str = "white" if bx < img.shape[1]/2 else "(0, 0.6, 0.55)" # Using teal for D
            
            # Wait, if it has children (holes), we shouldn't finish yet. 
            # PyMuPDF 'even-odd' fill rule automatically subtracts holes if we draw them in the same shape before finishing.
            # But wait, we need to finish J and D separately because they have different colors.
            pass

print("Generated code")
