from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QFontMetrics

class TextItem:
    def __init__(self, text, pos, color, font):
        self.text = text
        self.pos = pos
        self.color = color
        self.font = font
        fm = QFontMetrics(self.font)
        width = fm.horizontalAdvance(self.text)
        height = fm.height()
        self.bounding_rect = QRect(self.pos, QSize(width, height))
