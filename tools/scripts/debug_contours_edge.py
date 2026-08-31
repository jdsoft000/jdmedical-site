import cv2

logo_original_img = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
img = cv2.imread(logo_original_img)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]

for i, c in enumerate(valid_contours):
    x, y, w, h = cv2.boundingRect(c)
    print(f"Contour {i}: x={x}, w={w}, right_edge={x+w}")
