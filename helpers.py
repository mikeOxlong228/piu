from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QFormLayout, QDoubleSpinBox, QSpinBox


class QInputDialogWithInt:
    @staticmethod
    def getInt(parent, title, label, value, minv, maxv, step):
        d = QDialog(parent)
        d.setWindowTitle(title)
        layout = QFormLayout(d)
        spin = QSpinBox()
        spin.setRange(minv, maxv)
        spin.setValue(value)
        spin.setSingleStep(step)
        layout.addRow(QLabel(label), spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(d.accept)
        buttons.rejected.connect(d.reject)
        res = d.exec_()
        return spin.value(), res == QDialog.Accepted


class QInputDialogWithFloat:
    @staticmethod
    def getFloat(parent, title, label, value, minv, maxv, decimals):
        d = QDialog(parent)
        d.setWindowTitle(title)
        layout = QFormLayout(d)
        spin = QDoubleSpinBox()
        spin.setRange(minv, maxv)
        spin.setValue(value)
        spin.setDecimals(decimals)
        layout.addRow(QLabel(label), spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(d.accept)
        buttons.rejected.connect(d.reject)
        res = d.exec_()
        return spin.value(), res == QDialog.Accepted


# Aliases used above
QInputDialogWithFloat = QInputDialogWithFloat
QInputDialogWithInt = QInputDialogWithInt