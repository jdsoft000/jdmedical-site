import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path)

h, w, _ = img.shape
cy, cx = h//2, w//2
# The logo is above the text. Let's find the vertical column in the center of the image.
# We will print the BGR values along the center vertical line.

center_col = img[int(h*0.1):int(h*0.6), cx-10:cx+10]
# Average horizontally
avg_col = np.mean(center_col, axis=1)

for y in range(0, avg_col.shape[0], 5):
    b, g, r = avg_col[y]
    if max(b,g,r) > 100: # Ignore dark moire or background if it's white?
        pass
    print(f"y={y:03d}: B={b:03.0f} G={g:03.0f} R={r:03.0f}")

