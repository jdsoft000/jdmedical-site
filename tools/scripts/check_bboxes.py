import cv2

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(img_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

for i, c in enumerate(contours):
    area = cv2.contourArea(c)
    if area > 1000:
        bx, by, bw, bh = cv2.boundingRect(c)
        print(f"Contour {i}: area={area}, bbox=({bx}, {by}, {bw}, {bh}), hierarchy={hierarchy[0][i]}")
