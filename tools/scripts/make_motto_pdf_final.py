import fitz
import os

output_path = r"c:\Users\HOME\Desktop\JD_Motto_Banner_Horizontal.pdf"
bg_img_path = r"C:\Users\HOME\.cursor\projects\d-JD-MEDICAL\assets\corporate_bg_horizontal.png"
font_path = r"C:\Windows\Fonts\malgun.ttf"
font_bold_path = r"C:\Windows\Fonts\malgunbd.ttf"

# Conversion factor: mm to points
s = 72 / 25.4

# Canvas: 1100mm x 400mm
W = 1100 * s
H = 400 * s

doc = fitz.open()
page = doc.new_page(width=W, height=H)

# Register fonts
page.insert_font(fontname="F0", fontfile=font_path)
try:
    page.insert_font(fontname="FB", fontfile=font_bold_path)
except:
    page.insert_font(fontname="FB", fontfile=font_path)

# Insert Background to completely fill the canvas
page.insert_image(fitz.Rect(0, 0, W, H), filename=bg_img_path, keep_proportion=False)

# Colors
white = (1, 1, 1)
light_cyan = (0.6, 0.9, 0.9)
gray = (0.7, 0.7, 0.7)

# Helper for coordinates
def mm_rect(x1, y1, x2, y2):
    return fitz.Rect(x1*s, y1*s, x2*s, y2*s)

# SVG Logo String (Dark mode compatible colors: White and Bright Cyan)
svg_logo = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-160 -130 320 260" width="320" height="260">
    <path d="M -5 -120 L -110 -120 A 40 40 0 0 0 -150 -80 L -150 80 A 40 40 0 0 0 -110 120 L -5 120 L -5 -70 L -45 -70 L -45 80 L -110 80 L -110 -80 L -5 -80 Z" fill="#FFFFFF"/>
    <path d="M 5 120 L 110 120 A 40 40 0 0 0 150 80 L 150 -80 A 40 40 0 0 0 110 -120 L 5 -120 L 5 70 L 45 70 L 45 -80 L 110 -80 L 110 80 L 5 80 Z" fill="#00E5E5"/>
</svg>
"""

# Insert Logo (Center)
logo_rect = mm_rect(480, 120, 620, 230)
# We save the SVG to a temp file, then insert it
temp_svg = "temp_logo.svg"
with open(temp_svg, "w", encoding="utf-8") as f:
    f.write(svg_logo)
page.insert_image(logo_rect, filename=temp_svg)
os.remove(temp_svg)

# 1. Top Center ("기 술 혁 신" + "Technological Innovation")
page.insert_textbox(mm_rect(200, 30, 900, 70), "기 술 혁 신", fontname="FB", fontsize=70, color=white, align=1)
page.insert_textbox(mm_rect(200, 75, 900, 110), "Technological Innovation", fontname="F0", fontsize=51, color=light_cyan, align=1)

# 2. Left Center ("신 뢰 경 영" + "Trust Management")
page.insert_textbox(mm_rect(20, 150, 420, 190), "신 뢰 경 영", fontname="FB", fontsize=70, color=white, align=1)
page.insert_textbox(mm_rect(20, 195, 420, 230), "Trust Management", fontname="F0", fontsize=51, color=light_cyan, align=1)

# 3. Right Center ("최 고 성 과" + "Peak Performance")
page.insert_textbox(mm_rect(680, 150, 1080, 190), "최 고 성 과", fontname="FB", fontsize=70, color=white, align=1)
page.insert_textbox(mm_rect(680, 195, 1080, 230), "Peak Performance", fontname="F0", fontsize=51, color=light_cyan, align=1)

# 4. Bottom Center ("JD MEDICAL CO., LTD." + "제 이 디 메 디 컬")
page.insert_textbox(mm_rect(200, 300, 900, 340), "JD MEDICAL CO., LTD.", fontname="FB", fontsize=62, color=white, align=1)
page.insert_textbox(mm_rect(200, 350, 900, 380), "제 이 디 메 디 컬", fontname="FB", fontsize=40, color=gray, align=1)

doc.save(output_path, deflate=True)
print(f"Created {output_path}")
