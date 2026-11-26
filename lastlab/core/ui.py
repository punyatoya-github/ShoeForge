"""Small Qt helpers for panel controls (sliders, checkboxes, selects, colours, collapsible sections)."""
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W


def clear(layout):
    while layout.count():
        it = layout.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
        elif it.layout():
            clear(it.layout())


def slider(layout, label, lo, hi, step, val, on, unit='', disabled=False):
    n = round((hi - lo) / step)
    dec = 2 if step < 1 else 0
    row = W.QWidget()
    v = W.QVBoxLayout(row)
    v.setContentsMargins(0, 0, 0, 4)
    v.setSpacing(0)
    head, out = W.QHBoxLayout(), W.QLabel()
    head.addWidget(W.QLabel(label))
    head.addStretch()
    head.addWidget(out)
    s = W.QSlider(C.Qt.Horizontal)
    s.setRange(0, n)
    s.setValue(round((val - lo) / step))
    s.setEnabled(not disabled)
    value = lambda: lo + s.value() * step
    show = lambda: out.setText(f'{value():.{dec}f}{unit}')
    s.valueChanged.connect(lambda _: (show(), on(value())))
    show()
    v.addLayout(head)
    v.addWidget(s)
    layout.addWidget(row)
    return s


def check(layout, label, val, on):
    c = W.QCheckBox(label)
    c.setChecked(bool(val))
    c.toggled.connect(lambda b: on(bool(b)))
    layout.addWidget(c)
    return c


def select(layout, label, opts, val, on):
    row = W.QHBoxLayout()
    row.addWidget(W.QLabel(label))
    cb = W.QComboBox()
    for v, t in opts:
        cb.addItem(t, v)
    cb.setCurrentIndex(max(0, cb.findData(val)))
    cb.currentIndexChanged.connect(lambda i: on(cb.itemData(i)))
    row.addWidget(cb, 1)
    layout.addLayout(row)
    return cb


def color(layout, label, val, on):
    row = W.QHBoxLayout()
    b = W.QPushButton()
    b.setFixedSize(28, 22)
    paint = lambda c: b.setStyleSheet(f'background:{c};border:1px solid #888;')
    paint(val)

    def pick():
        c = W.QColorDialog.getColor(G.QColor(b.property('c') or val), b)
        if c.isValid():
            b.setProperty('c', c.name())
            paint(c.name())
            on(c.name())
    b.clicked.connect(pick)
    row.addWidget(b)
    row.addWidget(W.QLabel(label))
    row.addStretch()
    layout.addLayout(row)
    return b


class Section(W.QWidget):
    """Collapsible titled section."""

    def __init__(self, title, body, open_=True):
        super().__init__()
        v = W.QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        self.btn = W.QToolButton()
        self.btn.setText(title.upper())
        self.btn.setCheckable(True)
        self.btn.setChecked(open_)
        self.btn.setToolButtonStyle(C.Qt.ToolButtonTextBesideIcon)
        self.btn.setArrowType(C.Qt.DownArrow if open_ else C.Qt.RightArrow)
        self.btn.setStyleSheet('QToolButton{border:0;font-weight:600;text-align:left;}')
        self.body = body
        body.setVisible(open_)
        self.btn.toggled.connect(self._t)
        v.addWidget(self.btn)
        v.addWidget(body)

    def _t(self, on):
        self.btn.setArrowType(C.Qt.DownArrow if on else C.Qt.RightArrow)
        self.body.setVisible(on)
