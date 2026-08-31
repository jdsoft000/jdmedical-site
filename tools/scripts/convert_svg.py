from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

drawing = svg2rlg("temp_logo.svg")
renderPM.drawToFile(drawing, "temp_logo.png", fmt="PNG", dpi=300)
print("Converted SVG to PNG")
