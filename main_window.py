from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMainWindow, QLabel, QVBoxLayout, QPushButton, QAction, QColorDialog, \
    QFileDialog, QSpinBox, QFontDialog

from canvas import Canvas
from helpers import QInputDialogWithInt, QInputDialogWithFloat
from global_variables import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Image Editor (PyQt5)")
        self.setGeometry(80, 80, CANVAS_W+250, CANVAS_H+40)
        self.canvas = Canvas(CANVAS_W, CANVAS_H)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        main_h = QHBoxLayout()
        main_h.addWidget(self.canvas)

        # right panel
        panel = QVBoxLayout()
        panel.setAlignment(Qt.AlignTop)

        # tools
        tools_label = QLabel("Tools:")
        panel.addWidget(tools_label)

        tools = ['brush', 'airbrush', 'eraser', 'line', 'rect', 'ellipse', 'bucket', 'text', 'text_select']
        for t in tools:
            b = QPushButton(t.capitalize())
            b.setCheckable(True)
            b.clicked.connect(lambda _, tt=t: self.select_tool(tt))
            panel.addWidget(b)
            if t == 'brush':
                b.setChecked(True)
        self.tool_buttons = panel

        # color & size
        color_btn = QPushButton("Choose Color")
        color_btn.clicked.connect(self.choose_color)
        panel.addWidget(color_btn)

        panel.addWidget(QLabel("Brush size:"))
        size_spin = QSpinBox()
        size_spin.setRange(1, 100)
        size_spin.setValue(self.canvas.pen_width)
        size_spin.valueChanged.connect(self.canvas.set_pen_width)
        panel.addWidget(size_spin)

        # filters
        panel.addWidget(QLabel("Filters:"))
        bright_btn = QPushButton("Brightness -/+")
        bright_btn.clicked.connect(self.adjust_brightness_dialog)
        panel.addWidget(bright_btn)

        contrast_btn = QPushButton("Contrast")
        contrast_btn.clicked.connect(self.adjust_contrast_dialog)
        panel.addWidget(contrast_btn)

        blur_btn = QPushButton("Blur (box)")
        blur_btn.clicked.connect(lambda: self.canvas.apply_blur(3))
        panel.addWidget(blur_btn)

        sharpen_btn = QPushButton("Sharpen")
        sharpen_btn.clicked.connect(self.canvas.apply_sharpen)
        panel.addWidget(sharpen_btn)

        # undo/redo
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.canvas.undo)
        panel.addWidget(undo_btn)
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.canvas.redo)
        panel.addWidget(redo_btn)

        # load/save
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_image)
        panel.addWidget(load_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_image)
        panel.addWidget(save_btn)

        main_h.addLayout(panel)
        central.setLayout(main_h)
        self.setCentralWidget(central)

        # toolbar quick tool selection (sync with side buttons)
        tb = self.addToolBar("Tools")
        for t in ['Brush','Airbrush','Eraser','Line','Rect','Ellipse','Bucket']:
            a = QAction(t, self)
            a.triggered.connect(lambda checked, tt=t.lower(): self.select_tool(tt))
            tb.addAction(a)

    def select_tool(self, name):
        # uncheck side tool buttons if present (we used simple layout, so just set tool)
        self.canvas.set_tool(name)


    def choose_color(self):
        c = QColorDialog.getColor(self.canvas.pen_color, self, "Select color")
        if c.isValid():
            self.canvas.set_color(c)

    def adjust_brightness_dialog(self):
        val, ok = QInputDialogWithInt.getInt(self, "Brightness", "Delta (-255..255):", 0, -255, 255, 1)
        if ok:
            self.canvas.apply_brightness(val)

    def adjust_contrast_dialog(self):
        val, ok = QInputDialogWithFloat.getFloat(self, "Contrast", "Factor (0.1..3.0):", 1.0, 0.1, 3.0, 2)
        if ok:
            self.canvas.apply_contrast(val)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open image", "", "Images (*.png *.jpg *.bmp *.gif)")
        if path:
            self.canvas.load_image(path)

    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save image", "", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;BMP Image (*.bmp)")
        if path:
            self.canvas.save_image(path)