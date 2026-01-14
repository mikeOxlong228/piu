import numpy as np
from PyQt5.QtGui import QColor, QImage, QFont


def qimage_to_numpy(img: QImage):
    img = img.convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()
    ptr = img.bits()
    ptr.setsize(h * w * 4)
    arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
    return arr


def numpy_to_qimage(arr: np.ndarray):
    h, w, _ = arr.shape
    img = QImage(arr.data, w, h, QImage.Format_ARGB32)
    return img.copy()


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
    arr = qimage_to_numpy(src_img).astype(np.float32)
    k = np.array(kernel, dtype=np.float32)
    kh, kw = k.shape
    pad = kh // 2

    padded = np.pad(arr, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    out = np.zeros_like(arr)

    for y in range(kh):
        for x in range(kw):
            out += padded[y:y+arr.shape[0], x:x+arr.shape[1]] * k[y, x]

    out = out * factor + offset
    np.clip(out, 0, 255, out=out)

    return numpy_to_qimage(out.astype(np.uint8))


def flood_fill(img: QImage, x: int, y: int, new_color: QColor):
    # Convert image to safe BGRA NumPy array
    img = img.convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()

    ptr = img.bits()
    ptr.setsize(h * w * 4)
    arr = np.frombuffer(ptr, dtype=np.uint8).copy()  # Copy to avoid Qt memory issues
    arr = arr.reshape((h, w, 4))

    # BGRA channel order
    new_val = np.array([new_color.blue(),
                        new_color.green(),
                        new_color.red(),
                        new_color.alpha()],
                        dtype=np.uint8 )

    target_val = arr[y, x].copy()

    if np.array_equal(target_val, new_val):
        return img

    mask = np.all(arr == target_val, axis=2)
    filled = np.zeros((h, w), dtype=bool)

    # Stack-based flood fill
    stack = [(y, x)]
    while stack:
        cy, cx = stack.pop()
        if cy < 0 or cy >= h or cx < 0 or cx >= w:
            continue
        if not mask[cy, cx] or filled[cy, cx]:
            continue

        filled[cy, cx] = True
        stack.extend([
            (cy+1, cx), (cy-1, cx),
            (cy, cx+1), (cy, cx-1)
        ])

    # Write new color safely
    arr[filled] = new_val

    # Return a new QImage
    out_img = QImage(arr.data, w, h, QImage.Format_ARGB32)
    return out_img.copy()


def box_blur_kernel(size):
    k = [[1.0 for _ in range(size)] for __ in range(size)]
    return k

def sharpen_kernel():
    return [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ]