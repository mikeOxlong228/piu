import math
import random
from collections import deque

from PyQt5.QtCore import QPoint, Qt, QRect, QSize
from PyQt5.QtGui import QMouseEvent, QPainter, QPen, QPixmap, QFontMetrics
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog, QColorDialog, QFontDialog

from functions import *
from global_variables import *
from text_item import TextItem


class Canvas(QWidget):
    def __init__(self, w=CANVAS_W, h=CANVAS_H):
        super().__init__()
        self.setFixedSize(w, h)
        self.image = QImage(w, h, QImage.Format_ARGB32)
        self.image.fill(QColor('white'))
        self.temp = QImage()
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.pen_color = QColor('black')
        self.pen_width = 8
        self.tool = 'brush'  # brush, airbrush, eraser, line, rect, ellipse, bucket
        self.eraser_color = QColor(255,255,255,255)
        self.undo_stack = deque([], maxlen=UNDO_LIMIT)
        self.redo_stack = deque([], maxlen=UNDO_LIMIT)
        self.push_undo()  # initial state
        self.text_color = QColor('black')
        self.text_font = QFont("Arial", 20)
        self.text_items = []
        self.selected_text_item = None
        self.selecting_text = False

    # ----- UNDO/REDO -----
    def push_undo(self):
        self.undo_stack.append(image_copy(self.image))
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            last = self.undo_stack.pop()
            self.redo_stack.append(last)
            self.image = image_copy(self.undo_stack[-1])
            self.update()
        else:
            QMessageBox.information(self, "Undo", "No more undo steps.")

    def redo(self):
        if self.redo_stack:
            img = self.redo_stack.pop()
            self.undo_stack.append(image_copy(img))
            self.image = image_copy(img)
            self.update()
        else:
            QMessageBox.information(self, "Redo", "No more redo steps.")

    # ----- SETTINGS -----
    def set_tool(self, t):
        self.tool = t

    def set_color(self, c: QColor):
        self.pen_color = c

    def set_pen_width(self, w):
        self.pen_width = w

    # ----- MOUSE EVENTS -----
    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() != Qt.LeftButton:
            return

        if self.tool == 'bucket':
            self.push_undo()
            self.flood_fill(ev.x(), ev.y(), self.pen_color)
            self.update()

        elif self.tool == 'text_select':
            for item in reversed(self.text_items):  # topmost first
                if item.bounding_rect and item.bounding_rect.contains(ev.pos()):
                    self.selected_text_item = item
                    self.show_text_properties_dialog(item)
                    self.update()
                    return
            # clicked empty space
            self.selected_text_item = None
            self.update()
            return

        elif self.tool in ('line', 'rect', 'ellipse'):
            self.start_point = ev.pos()
            self.end_point = ev.pos()
            self.drawing = True
            self.temp = image_copy(self.image)

        elif self.tool == 'text':
            self.start_point = ev.pos()
            self.add_text_dialog(ev.pos())

        else:  # brush, airbrush, eraser
            self.push_undo()
            self.drawing = True
            self.start_point = ev.pos()
            self.draw_point(ev.pos())
            self.update()

    def mouseMoveEvent(self, ev: QMouseEvent):
        if not self.drawing:
            return
        pos = ev.pos()
        if self.tool == 'brush':
            self.draw_line(self.start_point, pos, self.pen_color, self.pen_width)
            self.start_point = pos
        elif self.tool == 'airbrush':
            self.airbrush_point(pos, self.pen_color, self.pen_width)
        elif self.tool == 'eraser':
            self.draw_line(self.start_point, pos, self.eraser_color, self.pen_width)
            self.start_point = pos
        elif self.tool in ('line','rect','ellipse'):
            # update preview dynamically
            self.end_point = pos
            self.image = image_copy(self.temp)
            self.draw_shape_preview(self.start_point, self.end_point)
        self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if not self.drawing:
            return
        if self.tool in ('line','rect','ellipse'):
            self.end_point = ev.pos()
            self.push_undo()
            self.draw_shape_final(self.start_point, self.end_point)
        self.drawing = False
        self.update()

    # ----- PAINT -----
    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

        # draw all text items
        for item in self.text_items:
            painter.setPen(QPen(item.color))
            painter.setFont(item.font)
            painter.drawText(item.pos, item.text)

        # highlight selected text
        if self.selected_text_item:
            pen = QPen(Qt.red, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.selected_text_item.bounding_rect)

    # ----- BASIC DRAWING -----
    def draw_point(self, pos: QPoint):
        painter = QPainter(self.image)
        pen = QPen(self.pen_color)
        pen.setWidth(self.pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPoint(pos)
        painter.end()

    def draw_line(self, p1: QPoint, p2: QPoint, color: QColor, width: int):
        painter = QPainter(self.image)
        pen = QPen(color)
        pen.setWidth(width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()

    def airbrush_point(self, pos: QPoint, color: QColor, width: int):
        radius = width * 1.6
        painter = QPainter(self.image)
        pen = QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)
        density = int(radius * 3)
        for _ in range(density):
            r = random.random() ** 0.5 * radius
            theta = random.random() * math.pi * 2
            dx = int(r * math.cos(theta))
            dy = int(r * math.sin(theta))
            painter.drawPoint(pos.x() + dx, pos.y() + dy)
        painter.end()

    # ----- SHAPES -----
    def draw_shape_preview(self, p1: QPoint, p2: QPoint):
        painter = QPainter(self.image)
        pen = QPen(self.pen_color)
        pen.setWidth(self.pen_width)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        rect = QRect(p1, p2)
        if self.tool == 'line':
            painter.drawLine(p1, p2)
        elif self.tool == 'rect':
            painter.drawRect(rect)
        elif self.tool == 'ellipse':
            painter.drawEllipse(rect)
        painter.end()

    def draw_shape_final(self, p1: QPoint, p2: QPoint):
        # draw final shape on main image
        self.draw_shape_preview(p1, p2)

    # ----- FLOOD FILL -----
    def flood_fill(self, x, y, new_color: QColor):
        w, h = self.image.width(), self.image.height()
        target = self.image.pixelColor(x, y)
        if target == new_color:
            return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= w or cy < 0 or cy >= h:
                continue
            c = self.image.pixelColor(cx, cy)
            if c != target:
                continue
            self.image.setPixelColor(cx, cy, new_color)
            stack.append((cx+1, cy))
            stack.append((cx-1, cy))
            stack.append((cx, cy+1))
            stack.append((cx, cy-1))

    # ----- FILTERS -----
    def apply_brightness(self, delta):
        self.push_undo()
        w, h = self.image.width(), self.image.height()
        for y in range(h):
            for x in range(w):
                c = self.image.pixelColor(x, y)
                r = clamp(c.red() + delta)
                g = clamp(c.green() + delta)
                b = clamp(c.blue() + delta)
                self.image.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        self.update()

    def apply_contrast(self, factor):
        self.push_undo()
        w, h = self.image.width(), self.image.height()
        for y in range(h):
            for x in range(w):
                c = self.image.pixelColor(x, y)
                r = clamp(int((c.red() - 128) * factor + 128))
                g = clamp(int((c.green() - 128) * factor + 128))
                b = clamp(int((c.blue() - 128) * factor + 128))
                self.image.setPixelColor(x, y, QColor(r, g, b, c.alpha()))
        self.update()

    def apply_blur(self, radius=3):
        self.push_undo()
        k = box_blur_kernel(radius)
        factor = 1.0 / (radius * radius)
        self.image = apply_kernel(self.image, k, factor=factor, offset=0)
        self.update()

    def apply_sharpen(self):
        self.push_undo()
        k = sharpen_kernel()
        self.image = apply_kernel(self.image, k, factor=1.0, offset=0)
        self.update()

    # ----- TEXT -----

    def add_text_dialog(self, pos: QPoint):
        text, ok = QInputDialog.getText(self, "Insert Text", "Enter text:")
        if ok and text:
            self.push_undo()
            item = TextItem(text, pos, self.text_color, self.text_font)
            self.text_items.append(item)
            self.update()

    def show_text_properties_dialog(self, text_item):
        color = QColorDialog.getColor(text_item.color, self, "Select text color")
        if color.isValid():
            text_item.color = color

        font, ok = QFontDialog.getFont(text_item.font, self, "Select font")
        if ok:
            text_item.font = font

        # update bounding rect after font change
        fm = QFontMetrics(text_item.font)
        width = fm.horizontalAdvance(text_item.text)
        height = fm.height()
        text_item.bounding_rect = QRect(text_item.pos, QSize(width, height))

        self.update()

    # ----- IMAGE IO -----
    def load_image(self, path):
        loaded = QImage(path)
        if loaded.isNull():
            QMessageBox.critical(self, "Load", "Failed to load image")
            return
        self.push_undo()
        self.image = QImage(self.width(), self.height(), QImage.Format_ARGB32)
        self.image.fill(QColor('white'))
        painter = QPainter(self.image)
        pix = QPixmap.fromImage(loaded)
        pix = pix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - pix.width()) // 2
        y = (self.height() - pix.height()) // 2
        painter.drawPixmap(x, y, pix)
        painter.end()
        self.update()

    def save_image(self, path):
        ok = self.image.save(path)
        if not ok:
            QMessageBox.critical(self, "Save", "Failed to save image")
