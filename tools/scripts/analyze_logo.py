import cv2

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
h, w = img.shape
print(f"Image size: {w}x{h}")

crop = img[0:int(h*0.7), 0:w] # Upper 70% where the logo should be
crop_resized = cv2.resize(crop, (120, 60))

_, thresh = cv2.threshold(crop_resized, 127, 255, cv2.THRESH_BINARY_INV)

for y in range(thresh.shape[0]):
    line = ""
    for x in range(thresh.shape[1]):
        if thresh[y, x] > 128: line += "#"
        else: line += " "
    print(line)
