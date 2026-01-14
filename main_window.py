import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QAction, QActionGroup,
    QColorDialog, QFileDialog, QSpinBox, QToolBar,
    QToolButton, QMenu, QScrollArea, QInputDialog
)

from canvas import Canvas
from helpers import QInputDialogWithInt, QInputDialogWithFloat
from global_variables import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Image Editor (PyQt5)")
        self.setGeometry(80, 80, CANVAS_W + 40, CANVAS_H + 80)

        self.canvas = Canvas()
        self.init_ui()

    # ------------------------------------------------------------------

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # Wrap canvas in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        layout.addWidget(scroll)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # Show dialog to adjust canvas size
        self.showMaximized()  # maximize window first
        self.ask_canvas_size()

        self.create_toolbar()

    # ------------------------------------------------------------------

    def create_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        self.addToolBar(tb)

        # ---------- Tool group (exclusive) ----------
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        def make_tool(name, label):
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda _, t=name: self.select_tool(t))
            self.tool_group.addAction(act)
            return act

        # ---------- Draw tools ----------
        draw_menu = QMenu("Draw", self)
        draw_menu.addAction(make_tool("brush", "Brush"))
        draw_menu.addAction(make_tool("airbrush", "Airbrush"))
        draw_menu.addAction(make_tool("eraser", "Eraser"))

        draw_btn = QToolButton()
        draw_btn.setText("Draw")
        draw_btn.setMenu(draw_menu)
        draw_btn.setPopupMode(QToolButton.InstantPopup)
        tb.addWidget(draw_btn)

        # ---------- Shape tools ----------
        shape_menu = QMenu("Shapes", self)
        shape_menu.addAction(make_tool("line", "Line"))
        shape_menu.addAction(make_tool("rect", "Rectangle"))
        shape_menu.addAction(make_tool("ellipse", "Ellipse"))

        shape_btn = QToolButton()
        shape_btn.setText("Shapes")
        shape_btn.setMenu(shape_menu)
        shape_btn.setPopupMode(QToolButton.InstantPopup)
        tb.addWidget(shape_btn)

        # ---------- Other tools ----------
        tb.addSeparator()

        tb.addAction(make_tool("bucket", "Bucket"))
        tb.addAction(make_tool("text", "Text"))
        tb.addAction(make_tool("text_select", "Text Select"))

        # ---------- Color & size ----------
        tb.addSeparator()

        color_act = QAction("Color", self)
        color_act.triggered.connect(self.choose_color)
        tb.addAction(color_act)

        size_spin = QSpinBox()
        size_spin.setRange(1, 100)
        size_spin.setValue(self.canvas.pen_width)
        size_spin.valueChanged.connect(self.canvas.set_pen_width)
        tb.addWidget(size_spin)

        # ---------- Filters ----------
        tb.addSeparator()

        filter_menu = QMenu("Filters", self)
        filter_menu.addAction("Brightness +/-", self.adjust_brightness_dialog)
        filter_menu.addAction("Contrast", self.adjust_contrast_dialog)
        filter_menu.addAction("Blur", lambda: self.canvas.apply_blur(3))
        filter_menu.addAction("Sharpen", self.canvas.apply_sharpen)

        filter_btn = QToolButton()
        filter_btn.setText("Filters")
        filter_btn.setMenu(filter_menu)
        filter_btn.setPopupMode(QToolButton.InstantPopup)
        tb.addWidget(filter_btn)

        # ---------- Undo / Redo ----------
        tb.addSeparator()

        tb.addAction(QAction("Undo", self, triggered=self.canvas.undo))
        tb.addAction(QAction("Redo", self, triggered=self.canvas.redo))

        # ---------- Load / Save ----------
        tb.addSeparator()

        tb.addAction(QAction("Load", self, triggered=self.load_image))
        tb.addAction(QAction("Save", self, triggered=self.save_image))

        # ---------- Settings: Window Size ----------
        tb.addSeparator()

        window_size_btn = QToolButton()
        window_size_btn.setText("Settings")
        window_size_menu = QMenu("Settings", self)
        window_size_menu.addAction("Window Size", self.ask_canvas_size)
        window_size_btn.setMenu(window_size_menu)
        window_size_btn.setPopupMode(QToolButton.InstantPopup)
        tb.addWidget(window_size_btn)

        # ---------- Default tool ----------
        for act in self.tool_group.actions():
            if act.text() == "Brush":
                act.setChecked(True)
                self.select_tool("brush")
                break

    # ------------------------------------------------------------------

    def select_tool(self, name):
        self.canvas.set_tool(name)

    # ------------------------------------------------------------------

    def choose_color(self):
        c = QColorDialog.getColor(self.canvas.pen_color, self, "Select color")
        if c.isValid():
            self.canvas.set_color(c)

    # ------------------------------------------------------------------

    def adjust_brightness_dialog(self):
        val, ok = QInputDialogWithInt.getInt(
            self, "Brightness", "Delta (-255..255):", 0, -255, 255, 1)
        if ok:
            self.canvas.apply_brightness(val)

    # ------------------------------------------------------------------

    def adjust_contrast_dialog(self):
        val, ok = QInputDialogWithFloat.getFloat(
            self, "Contrast", "Factor (0.1..3.0):", 1.0, 0.1, 3.0, 2)
        if ok:
            self.canvas.apply_contrast(val)

    # ------------------------------------------------------------------

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.bmp *.gif)")
        if path:
            self.canvas.load_image(path)

    # ------------------------------------------------------------------

    def save_image(self):
        path, selected_filter = QFileDialog.getSaveFileName(self,"Save image","",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;BMP Image (*.bmp)")
        if not path:
            return

        suffix = os.path.splitext(path)[1]

        if not suffix:
            if "PNG" in selected_filter:
                path += ".png"
            elif "JPEG" in selected_filter:
                path += ".jpg"
            elif "BMP" in selected_filter:
                path += ".bmp"

        self.canvas.save_image(path)

    # -------------- Other --------------

    def ask_canvas_size(self):
        # Get current canvas size
        current_w = self.canvas.width()
        current_h = self.canvas.height()

        # Ask for new width
        w, ok1 = QInputDialog.getInt(
            self, "Canvas Width", "Enter canvas width:", current_w, 1, 10000)
        if not ok1:
            return

        # Ask for new height
        h, ok2 = QInputDialog.getInt(
            self, "Canvas Height", "Enter canvas height:", current_h, 1, 10000)
        if not ok2:
            return

        self.canvas.set_canvas_size(w, h)