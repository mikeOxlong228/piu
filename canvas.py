import math
import random
from collections import deque

from PyQt5.QtCore import QPoint, Qt, QRect, QSize
from PyQt5.QtGui import QMouseEvent, QPainter, QPen, QPixmap, QFontMetrics
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog, QSizePolicy, QColorDialog, QFontDialog

from functions import *
from global_variables import *
from text_item import TextItem


class Canvas(QWidget):
    def __init__(self, w=CANVAS_W, h=CANVAS_H):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create a tiny temporary image; will resize dynamically
        self.image = QImage(1, 1, QImage.Format_ARGB32)
        self.image.fill(QColor("white"))

        self.temp = QImage()
        self.drawing = False

        self.start_point = QPoint()
        self.end_point = QPoint()

        self.pen_color = QColor("black")
        self.pen_width = 8
        self.eraser_color = QColor(255, 255, 255)

        self.tool = "brush"

        self.text_color = QColor("black")
        self.text_font = QFont("Arial", 20)
        self.text_items = []
        self.selected_text_item = None

        self.dragging_text = False
        self.drag_offset = QPoint()
        self.text_moved = False

        self.undo_stack = deque(maxlen=UNDO_LIMIT)
        self.redo_stack = deque(maxlen=UNDO_LIMIT)

        self.push_undo()  # initial state

    # ------------------------------------------------------------------
    # -------------------------- UNDO / REDO ---------------------------
    # ------------------------------------------------------------------

    def push_undo(self):
        self.undo_stack.append((
            image_copy(self.image),
            [item.copy() for item in self.text_items]
        ))
        self.redo_stack.clear()

    def restore_state(self, state):
        img, items = state
        self.image = image_copy(img)
        self.text_items = [i.copy() for i in items]
        self.selected_text_item = None

    def undo(self):
        if len(self.undo_stack) > 1:
            state = self.undo_stack.pop()
            self.redo_stack.append(state)
            self.restore_state(self.undo_stack[-1])
            self.update()
        else:
            QMessageBox.information(self, "Undo", "No more undo steps.")

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.restore_state(state)
            self.update()
        else:
            QMessageBox.information(self, "Redo", "No more redo steps.")

    # ------------------------------------------------------------------
    # --------------------------- SETTINGS -----------------------------
    # ------------------------------------------------------------------

    def set_tool(self, t):
        self.tool = t

    def set_color(self, c):
        self.pen_color = c

    def set_pen_width(self, w):
        self.pen_width = w

    # ------------------------------------------------------------------
    # -------------------------- MOUSE EVENTS --------------------------
    # ------------------------------------------------------------------

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() != Qt.LeftButton:
            return

        if self.tool == "bucket":
            self.image = flood_fill(self.image, ev.x(), ev.y(), self.pen_color)
            self.push_undo()
            self.update()
            return

        if self.tool == "text_select":
            for item in reversed(self.text_items):
                if item.bounding_rect.contains(ev.pos()):
                    self.selected_text_item = item
                    self.dragging_text = True
                    self.drag_offset = ev.pos() - item.pos
                    self.text_moved = False
                    self.update()
                    return
            self.selected_text_item = None
            self.update()
            return

        if self.tool in ("line", "rect", "ellipse"):
            self.start_point = ev.pos()
            self.end_point = ev.pos()
            self.temp = image_copy(self.image)
            self.drawing = True
            return

        if self.tool == "text":
            self.add_text_dialog(ev.pos())
            return

        self.drawing = True
        self.start_point = ev.pos()
        self.draw_point(ev.pos())
        self.update()

    def mouseMoveEvent(self, ev: QMouseEvent):
        pos = ev.pos()

        if self.dragging_text and self.selected_text_item:
            self.text_moved = True
            self.selected_text_item.pos = pos - self.drag_offset

            fm = QFontMetrics(self.selected_text_item.font)
            w = fm.horizontalAdvance(self.selected_text_item.text)
            h = fm.height()

            top_left = QPoint(
                self.selected_text_item.pos.x(),
                self.selected_text_item.pos.y() - fm.ascent()
            )
            self.selected_text_item.bounding_rect = QRect(top_left, QSize(w, h))

            self.update()
            return

        if not self.drawing:
            return

        if self.tool == "brush":
            self.draw_line(self.start_point, pos, self.pen_color, self.pen_width)
            self.start_point = pos

        elif self.tool == "airbrush":
            self.airbrush_point(pos, self.pen_color, self.pen_width)

        elif self.tool == "eraser":
            self.draw_line(self.start_point, pos, self.eraser_color, self.pen_width)
            self.start_point = pos

        elif self.tool in ("line", "rect", "ellipse"):
            self.end_point = pos
            self.image = image_copy(self.temp)
            self.draw_shape_preview(self.start_point, self.end_point)

        self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if self.dragging_text:
            if self.text_moved:
                self.push_undo()
            self.dragging_text = False
            self.text_moved = False
            self.update()
            return

        if not self.drawing:
            return

        if self.tool in ("line", "rect", "ellipse"):
            self.draw_shape_final(self.start_point, ev.pos())

        self.drawing = False
        self.push_undo()
        self.update()

    def mouseDoubleClickEvent(self, ev):
        if self.tool != "text_select":
            return

        for item in reversed(self.text_items):
            if item.bounding_rect and item.bounding_rect.contains(ev.pos()):
                self.selected_text_item = item
                self.show_text_properties_dialog(item)
                self.push_undo()
                self.update()
                return

    def show_text_properties_dialog(self, item: TextItem):
        # Edit text
        text, ok = QInputDialog.getText(self,"Edit Text", "Text:", text=item.text)
        if not ok:
            return

        # Edit font
        font, ok = QFontDialog.getFont(item.font, self, "Select Font")
        if not ok:
            return

        # Edit color
        color = QColorDialog.getColor(item.color, self, "Select Text Color")
        if not color.isValid():
            return

        # Apply changes
        item.text = text
        item.font = font
        item.color = color

        # Recalculate bounding rect
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(text)
        h = fm.height()

        top_left = QPoint(item.pos.x(), item.pos.y() - fm.ascent())
        item.bounding_rect = QRect(top_left, QSize(w, h))

    # ------------------------------------------------------------------
    # ---------------------------- PAINT -------------------------------
    # ------------------------------------------------------------------

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

        for item in self.text_items:
            painter.setPen(QPen(item.color))
            painter.setFont(item.font)
            painter.drawText(item.pos, item.text)

        if self.selected_text_item:
            pen = QPen(Qt.red, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.selected_text_item.bounding_rect)

    # ------------------------------------------------------------------
    # --------------------------- DRAWING ------------------------------
    # ------------------------------------------------------------------

    def draw_point(self, pos):
        painter = QPainter(self.image)
        pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPoint(pos)
        painter.end()

    def draw_line(self, p1, p2, color, width):
        painter = QPainter(self.image)
        pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()

    def airbrush_point(self, pos, color, width):
        radius = width * 1.6
        painter = QPainter(self.image)
        pen = QPen(color)
        painter.setPen(pen)

        for _ in range(int(radius * 3)):
            r = random.random() ** 0.5 * radius
            t = random.random() * math.pi * 2
            painter.drawPoint(
                pos.x() + int(r * math.cos(t)),
                pos.y() + int(r * math.sin(t))
            )

        painter.end()

    # ------------------------------------------------------------------
    # ---------------------------- SHAPES ------------------------------
    # ------------------------------------------------------------------

    def draw_shape_preview(self, p1, p2):
        painter = QPainter(self.image)
        pen = QPen(self.pen_color, self.pen_width)
        painter.setPen(pen)
        rect = QRect(p1, p2)

        if self.tool == "line":
            painter.drawLine(p1, p2)
        elif self.tool == "rect":
            painter.drawRect(rect)
        elif self.tool == "ellipse":
            painter.drawEllipse(rect)

        painter.end()

    def draw_shape_final(self, p1, p2):
        self.draw_shape_preview(p1, p2)


    # ------------------------------------------------------------------
    # -------------------------- TEXT ----------------------------------
    # ------------------------------------------------------------------

    def add_text_dialog(self, pos):
        text, ok = QInputDialog.getText(self, "Insert Text", "Enter text:")
        if ok and text:
            self.text_items.append( TextItem(text, pos, self.text_color, self.text_font) )
            self.push_undo()
            self.update()

    # ------------------------------------------------------------------
    # -------------------------- FILTERS -------------------------------
    # ------------------------------------------------------------------

    def apply_brightness(self, delta):
        arr = qimage_to_numpy(self.image).astype(np.int16)

        arr[..., :3] += delta
        np.clip(arr, 0, 255, out=arr)

        self.image = numpy_to_qimage(arr.astype(np.uint8))
        self.push_undo()
        self.update()

    def apply_contrast(self, factor):
        arr = qimage_to_numpy(self.image).astype(np.float32)

        arr[..., :3] = (arr[..., :3] - 128.0) * factor + 128.0
        np.clip(arr, 0, 255, out=arr)

        self.image = numpy_to_qimage(arr.astype(np.uint8))
        self.push_undo()
        self.update()

    def apply_blur(self, radius=3):
        k = box_blur_kernel(radius)
        factor = 1.0 / (radius * radius)
        self.image = apply_kernel(self.image, k, factor=factor, offset=0)
        self.push_undo()
        self.update()

    def apply_sharpen(self):
        k = sharpen_kernel()
        self.image = apply_kernel(self.image, k, factor=1.0, offset=0)
        self.push_undo()
        self.update()


    # ------------------------------------------------------------------
    # ----------------------- IMAGE IO ---------------------------------
    # ------------------------------------------------------------------

    def load_image(self, path):
        loaded = QImage(path)
        if loaded.isNull():
            QMessageBox.critical(self, "Load", "Failed to load image")
            return

        self.image = QImage(self.width(), self.height(), QImage.Format_ARGB32)
        self.image.fill(QColor("white"))

        painter = QPainter(self.image)
        pix = QPixmap.fromImage(loaded).scaled(
            self.width(),
            self.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        x = (self.width() - pix.width()) // 2
        y = (self.height() - pix.height()) // 2
        painter.drawPixmap(x, y, pix)
        painter.end()

        self.push_undo()
        self.update()

    def save_image(self, path):
        final = image_copy(self.image)
        painter = QPainter(final)

        for item in self.text_items:
            painter.setPen(QPen(item.color))
            painter.setFont(item.font)
            painter.drawText(item.pos, item.text)

        painter.end()

        if not final.save(path):
            QMessageBox.critical(self, "Save", "Failed to save image")

    # ------------------------------------------------------------------
    # --------------------------- OTHERS -------------------------------
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        new_size = event.size()
        if new_size.width() > self.image.width() or new_size.height() > self.image.height():
            new_img = QImage(new_size, QImage.Format_ARGB32)
            new_img.fill(QColor("white"))

            painter = QPainter(new_img)
            painter.drawImage(0, 0, self.image)
            painter.end()

            self.image = new_img
            self.update()

        super().resizeEvent(event)

    def set_canvas_size(self, w, h):
        new_img = QImage(max(1, w), max(1, h), QImage.Format_ARGB32)
        new_img.fill(QColor("white"))

        # Copy existing painting
        painter = QPainter(new_img)
        painter.drawImage(0, 0, self.image)
        painter.end()

        self.image = new_img

        # Update widget minimum size to allow scrolling
        self.setMinimumSize(w, h)
        self.update()

