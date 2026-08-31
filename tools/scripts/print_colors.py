import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path)

# Resize to something manageable
img = cv2.resize(img, (200, 150))
img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Cyan/Teal mask
lower_cyan = np.array([80, 50, 50])
upper_cyan = np.array([100, 255, 255])
mask_cyan = cv2.inRange(img_hsv, lower_cyan, upper_cyan)

# Dark Blue mask
lower_blue = np.array([100, 50, 20])
upper_blue = np.array([130, 255, 100])
mask_blue = cv2.inRange(img_hsv, lower_blue, upper_blue)

for name, mask in [("DARK BLUE", mask_blue), ("CYAN", mask_cyan)]:
    print(f"--- {name} ---")
    mask_small = cv2.resize(mask, (40, 20))
    _, mask_bin = cv2.threshold(mask_small, 127, 255, cv2.THRESH_BINARY)
    for y in range(20):
        row = ""
        for x in range(40):
            row += "#" if mask_bin[y, x] > 0 else " "
        print(row)
    print()
