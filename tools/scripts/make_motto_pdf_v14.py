import fitz
import cv2

output_path = r"c:\Users\HOME\Desktop\JD_Motto_Banner_Horizontal.pdf"
bg_img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\corporate_bg_horizontal.png"
logo_original_img = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\c__Users_HOME_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images______-c7c14dae-4c2c-4a9d-a936-86fdbe505422.png"
font_path = r"C:\Windows\Fonts\malgun.ttf"
font_bold_path = r"C:\Windows\Fonts\malgunbd.ttf"

img = cv2.imread(logo_original_img)
h_img, w_img = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
valid_contours = [c for c in contours if cv2.contourArea(c) > 1000]

s = 72 / 25.4
W = 1100 * s
H = 400 * s

doc = fitz.open()
page = doc.new_page(width=W, height=H)

try:
    page.insert_font(fontname="FB", fontfile=font_bold_path)
    page.insert_font(fontname="F0", fontfile=font_path)
except:
    pass

page.insert_image(fitz.Rect(0, 0, W, H), filename=bg_img_path, keep_proportion=False)

white = (1, 1, 1)
gray_color = (0.7, 0.7, 0.7)
light_cyan = (0.6, 0.9, 0.9) 
bright_blue = (0.1, 0.45, 0.85) 
teal = (0.0, 0.6, 0.55)         

cx = W / 2
cy = 180 * s
scale = s * 0.38

shape_j = page.new_shape()
shape_d = page.new_shape()

for c in valid_contours:
    epsilon = 0.0005 * cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, epsilon, True)
    
    bx = cv2.boundingRect(c)[0]
    
    # FIXED: Since J's x=96 and D's x=308, we split at x=200
    if bx < 200:
        target_shape = shape_j
    else:
        target_shape = shape_d
        
    pts = []
    for pt in approx:
        x = pt[0][0] - w_img/2
        y = pt[0][1] - h_img/2
        pts.append(fitz.Point(cx + x*scale, cy + y*scale))
        
    start_pt = pts[0]
    last_pt = start_pt
    target_shape.draw_line(start_pt, start_pt) 
    for pt in pts[1:]:
        target_shape.draw_line(last_pt, pt)
        last_pt = pt
    target_shape.draw_line(last_pt, start_pt) 

shape_j.finish(color=bright_blue, fill=bright_blue, even_odd=True)
shape_j.commit()

shape_d.finish(color=teal, fill=teal, even_odd=True)
shape_d.commit()

def mm_rect(x1, y1, x2, y2):
    return fitz.Rect(x1*s, y1*s, x2*s, y2*s)

page.insert_textbox(mm_rect(200, 40, 900, 90), "Technological Innovation", fontname="FB", fontsize=70, color=light_cyan, align=1)
page.insert_textbox(mm_rect(10, 160, 390, 210), "Trust Management", fontname="FB", fontsize=70, color=light_cyan, align=1)
page.insert_textbox(mm_rect(710, 160, 1090, 210), "Peak Performance", fontname="FB", fontsize=70, color=light_cyan, align=1)

page.insert_textbox(mm_rect(200, 290, 900, 330), "JD MEDICAL CO., LTD.", fontname="FB", fontsize=62, color=white, align=1)
page.insert_textbox(mm_rect(200, 340, 900, 370), "제 이 디 메 디 컬", fontname="FB", fontsize=40, color=gray_color, align=1)

doc.save(output_path, deflate=True)
print(f"Created {output_path}")
