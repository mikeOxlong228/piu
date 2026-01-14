from PyQt5.QtCore import QRect, QSize, QPoint
from PyQt5.QtGui import QFontMetrics, QColor, QFont


class TextItem:
    def __init__(self, text, pos, color, font):
        self.text = text
        self.pos = pos
        self.color = color
        self.font = font
        fm = QFontMetrics(self.font)
        width = fm.horizontalAdvance(self.text)
        height = fm.height()

        top_left = QPoint(self.pos.x(), self.pos.y() - fm.ascent())
        self.bounding_rect = QRect(top_left, QSize(width, height))

    def copy(self):
        return TextItem( self.text, QPoint(self.pos), QColor(self.color), QFont(self.font) )