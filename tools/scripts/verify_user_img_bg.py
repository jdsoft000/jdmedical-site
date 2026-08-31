import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_K-001-b81fc5be-9d9a-467c-a5c5-ed573447e599.png"
img = cv2.imread(img_path)
h, w = img.shape[:2]
cx, cy = w//2, int(h * 0.45) 

bg_col = img[cy-20:cy+20, cx-100:cx-80]
print(f"BG Region Avg BGR: {np.mean(bg_col, axis=(0,1))}")
