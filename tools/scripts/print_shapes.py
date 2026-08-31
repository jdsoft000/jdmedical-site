import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

h, w = thresh.shape
thresh = thresh[int(h*0.1):int(h*0.65), :]

contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=cv2.contourArea, reverse=True)[:2]

for i, c in enumerate(contours):
    x, y, cw, ch = cv2.boundingRect(c)
    print(f"Contour {i}: x={x}, y={y}, w={cw}, h={ch}, area={cv2.contourArea(c)}")
    
    mask = cv2.drawContours(np.zeros_like(thresh), [c], -1, 255, -1)
    mask_crop = mask[y:y+ch, x:x+cw]
    mask_resized = cv2.resize(mask_crop, (20, 20))
    _, mask_bin = cv2.threshold(mask_resized, 127, 255, cv2.THRESH_BINARY)
    print("Shape:")
    for my in range(20):
        row = ""
        for mx in range(20):
            row += "#" if mask_bin[my, mx] > 0 else " "
        print(row)
    print()
