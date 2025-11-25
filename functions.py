from PyQt5.QtGui import QColor, QImage, QFont


def clamp(v, a=0, b=255):
    return max(a, min(b, v))

def qcolor_to_tuple(c: QColor):
    return c.red(), c.green(), c.blue(), c.alpha()

def tuple_to_qcolor(t):
    return QColor(t[0], t[1], t[2], t[3] if len(t) > 3 else 255)

def image_copy(img: QImage) -> QImage:
    return img.copy()

def set_text_font(self, font: QFont):
    self.text_font = font

def set_text_color(self, color: QColor):
    self.text_color = color

def apply_kernel(src_img: QImage, kernel, factor=1.0, offset=0):
    w, h = src_img.width(), src_img.height()
    dst = QImage(w, h, QImage.Format_ARGB32)
    half = len(kernel)//2
    # convert kernel 2D list to access
    for y in range(h):
        for x in range(w):
            r = g = b = a = 0.0
            for ky in range(len(kernel)):
                for kx in range(len(kernel[0])):
                    sx = x + (kx - half)
                    sy = y + (ky - half)
                    if 0 <= sx < w and 0 <= sy < h:
                        c = src_img.pixelColor(sx, sy)
                        kval = kernel[ky][kx]
                        r += c.red() * kval
                        g += c.green() * kval
                        b += c.blue() * kval
                        a += c.alpha() * kval
            r = clamp(int(r * factor + offset))
            g = clamp(int(g * factor + offset))
            b = clamp(int(b * factor + offset))
            a = clamp(int(a * factor + offset))
            dst.setPixelColor(x, y, QColor(r, g, b, a))
    return dst

def box_blur_kernel(size):
    k = [[1.0 for _ in range(size)] for __ in range(size)]
    return k

def sharpen_kernel():
    return [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ]