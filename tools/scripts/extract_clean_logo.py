import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(img_path)
h, w = img.shape[:2]

# Convert to grayscale and threshold
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Sort by x position to get J then D
contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

paths = []
for c in contours:
    if cv2.contourArea(c) < 1000:
        continue
    # Simplify contour
    epsilon = 0.0005 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)
    
    path_str = ""
    for pt in approx:
        # Center the coordinates around 0,0
        x = pt[0][0] - w/2
        y = pt[0][1] - h/2
        path_str += f"{x:.2f},{y:.2f} "
    paths.append(path_str)

with open("extracted_paths.txt", "w") as f:
    for p in paths:
        f.write(p + "\n")

print(f"Extracted {len(paths)} paths.")
print(f"Image dimensions: {w}x{h}")
