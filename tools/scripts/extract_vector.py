import cv2
import numpy as np

img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_KakaoTalk_20260703_045155155-381529e7-f7c6-4d9b-a1a8-691051f93d2a.png"
img = cv2.imread(img_path)
h, w, _ = img.shape
img_crop = img[int(h*0.1):int(h*0.65), :]

# Blur to remove moire
blurred = cv2.GaussianBlur(img_crop, (15, 15), 0)
hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

# Dark Blue
mask_blue = cv2.inRange(hsv, np.array([90, 50, 20]), np.array([140, 255, 120]))
# Cyan
mask_cyan = cv2.inRange(hsv, np.array([80, 50, 50]), np.array([100, 255, 255]))

def get_svg_path(mask, color, offset_x=0, offset_y=0, scale=1.0):
    # Find largest contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: return ""
    c = max(contours, key=cv2.contourArea)
    
    # Smooth contour
    epsilon = 0.005 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)
    
    path = f'<path fill="{color}" d="M '
    for pt in approx:
        x = (pt[0][0] - w/2) * scale + offset_x
        y = (pt[0][1] - img_crop.shape[0]/2) * scale + offset_y
        path += f"{x:.1f},{y:.1f} "
    path += 'Z"/>\n'
    
    # Also find holes (internal contours)
    contours_all, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is not None:
        for i in range(len(contours_all)):
            if hierarchy[0][i][3] != -1: # has parent -> hole
                hole = contours_all[i]
                if cv2.contourArea(hole) > 500:
                    approx_hole = cv2.approxPolyDP(hole, epsilon, True)
                    path += f'<path fill="#000000" d="M ' # We will just use even-odd fill rule or mask it
                    for pt in approx_hole:
                        x = (pt[0][0] - w/2) * scale + offset_x
                        y = (pt[0][1] - img_crop.shape[0]/2) * scale + offset_y
                        path += f"{x:.1f},{y:.1f} "
                    path += 'Z"/>\n'
    return path

svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">\n'
# To do holes properly in standard SVG without masks, we can use fill-rule="evenodd"
svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">\n<g fill-rule="evenodd">\n'

def get_svg_path_evenodd(mask, color, offset_x=0, offset_y=0, scale=1.0):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: return ""
    
    # Find the largest external contour
    main_idx = -1
    max_area = 0
    for i in range(len(contours)):
        if hierarchy[0][i][3] == -1: # external
            area = cv2.contourArea(contours[i])
            if area > max_area:
                max_area = area
                main_idx = i
                
    if main_idx == -1: return ""
    
    path = f'<path fill="{color}" d="'
    
    def add_contour(idx):
        nonlocal path
        c = contours[idx]
        epsilon = 0.002 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, epsilon, True)
        path += "M "
        for pt in approx:
            x = (pt[0][0] - w/2) * scale + offset_x
            y = (pt[0][1] - img_crop.shape[0]/2) * scale + offset_y
            path += f"{x:.1f},{y:.1f} "
        path += "Z "
        
    add_contour(main_idx)
    
    # Add holes
    for i in range(len(contours)):
        if hierarchy[0][i][3] == main_idx: # hole of main contour
            if cv2.contourArea(contours[i]) > 1000:
                add_contour(i)
                
    path += '"/>\n'
    return path

svg += get_svg_path_evenodd(mask_blue, "#FFFFFF", offset_x=200, offset_y=150, scale=0.7)
svg += get_svg_path_evenodd(mask_cyan, "#00E5E5", offset_x=200, offset_y=150, scale=0.7)
svg += '</g>\n</svg>'

with open("temp_logo.svg", "w") as f:
    f.write(svg)
print("Saved exact vector logo from image to temp_logo.svg")
