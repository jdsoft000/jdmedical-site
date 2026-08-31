import fitz

doc = fitz.open()
page = doc.new_page()

# Draw J
shape_j = page.new_shape()
shape_j.draw_rect(fitz.Rect(50, 50, 150, 150))
shape_j.finish(color=(0.1, 0.45, 0.85), fill=(0.1, 0.45, 0.85))
shape_j.commit()

# Draw D
shape_d = page.new_shape()
shape_d.draw_rect(fitz.Rect(200, 50, 300, 150))
shape_d.finish(color=(0.0, 0.6, 0.55), fill=(0.0, 0.6, 0.55))
shape_d.commit()

doc.save("color_test.pdf")
print("Saved color_test.pdf")
