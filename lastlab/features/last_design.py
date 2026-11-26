"""LAST DESIGN: edit the parametric last (length, widths, heights, heel, toe shape) + girth readout."""
from functools import partial

from PySide6 import QtCore as C, QtWidgets as W

from lastlab.core import ui
from lastlab.features import generator as G

SL = [('L', 'Length', 200, 340, 1, ' mm'), ('W', 'Ball width', 60, 130, 1, ' mm'),
      ('hw', 'Heel width ratio', .5, .85, .01, ''), ('H', 'Instep / back height', 50, 150, 1, ' mm'),
      ('heel', 'Heel height', 0, 100, 1, ' mm'), ('spring', 'Toe spring', 0, 30, 1, ' mm'),
      ('ball', 'Ball position', .6, .78, .01, ''), ('tp', 'Toe shape (square ↔ pointed)', .25, 1.2, .01, ''),
      ('p', 'Section (boxy ↔ pointed)', .5, 1.2, .01, '')]


class LastDesign:
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = W.QWidget()
        v = W.QVBoxLayout(self.panel)
        v.setContentsMargins(0, 0, 0, 0)
        self.box = W.QVBoxLayout()
        v.addLayout(self.box)
        self.note = W.QLabel('Parametric editing applies to library lasts. Imported meshes use the Transform tools.')
        self.note.setWordWrap(True)
        v.addWidget(self.note)
        reset = W.QPushButton('Reset to preset')
        v.addWidget(reset)
        self.girth = W.QLabel()
        v.addWidget(self.girth)
        reset.clicked.connect(self.reset)
        self.timer = C.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.regen)
        ctx.bus.on('project:changed', self.render)
        ctx.bus.on('geometry:changed', self.readout)
        ctx.bus.on('transform:changed', self.readout)

    def editable(self, p):
        return p['lastId'] in G.PRESETS

    def render(self, _=None):
        p = self.ctx.store.cur()
        ui.clear(self.box)
        self.note.setVisible(not self.editable(p))
        s = G.spec(p)
        for k, label, lo, hi, st, unit in SL:
            ui.slider(self.box, label, lo, hi, st, s[k], partial(self.set, k), unit, not self.editable(p))
        self.readout()

    def set(self, k, val):
        self.ctx.store.cur()['spec'][k] = val
        self.timer.start(30)  # debounce regeneration while dragging

    def regen(self):
        self.ctx.store.save()
        self.ctx.model.refresh(False)

    def reset(self):
        self.ctx.store.cur()['spec'] = {}
        self.ctx.store.save()
        self.render()
        self.ctx.model.refresh(False)

    def readout(self, _=None):
        p = self.ctx.store.cur()
        if not p or not self.editable(p):
            self.girth.setText('')
            return
        s, t = G.spec(p), p['t']
        sy, sz = t['sy'] / 100, t['sz'] / 100
        self.girth.setText(f"Ball girth {G.girth(s, s['ball'], sy, sz):.0f} mm · "
                           f"Waist girth {G.girth(s, .4, sy, sz):.0f} mm")
