import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path)

# Save a cropped, enhanced version to a new file so I can view it clearly if needed, 
# or I'll just write a script to generate a clean SVG based on the exact edges.
# Actually, let's use OpenCV to extract the exact contours of the logo and save as SVG!

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

# The logo is in the upper half.
h, w = thresh.shape
thresh = thresh[int(h*0.1):int(h*0.65), :]

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Sort contours by area
contours = sorted(contours, key=cv2.contourArea, reverse=True)

# The two largest contours should be the J and D.
svg_path = r"c:\Users\HOME\Desktop\extracted_logo.svg"
with open(svg_path, "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {int(h*0.55)}">\n')
    for i in range(min(2, len(contours))):
        c = contours[i]
        color = "blue" if i == 0 else "cyan"
        f.write(f'<path fill="{color}" d="M ')
        for pt in c:
            f.write(f"{pt[0][0]},{pt[0][1]} ")
        f.write('Z"/>\n')
    f.write('</svg>')
print("Done")
