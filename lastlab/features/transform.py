"""Scale / rotate / mirror the last + live dimensions."""
from functools import partial

import numpy as np
from PySide6 import QtWidgets as W

from lastlab.core import ui
from lastlab.core.store import default_transform

SL = [('sx', 'Length scale', 50, 150), ('sz', 'Width scale', 50, 150), ('sy', 'Height scale', 50, 150),
      ('rx', 'Rotate X', -180, 180), ('ry', 'Rotate Y', -180, 180), ('rz', 'Rotate Z', -180, 180)]


def matrix(t):
    """4x4 matrix: scale (mirror = negative Z) then Euler XYZ rotation (same convention as three.js)."""
    rx, ry, rz = np.radians([t['rx'], t['ry'], t['rz']])
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    S = np.diag([t['sx'] / 100, t['sy'] / 100, t['sz'] / 100 * (-1 if t['mir'] else 1)])
    m = np.eye(4)
    m[:3, :3] = Rx @ Ry @ Rz @ S
    return m


def dimensions(mesh, t):
    lo, hi = mesh.bbox
    c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    w = c @ matrix(t)[:3, :3].T
    return w.min(0), w.max(0) - w.min(0)


class Transform:
    def __init__(self, ctx):
        self.ctx = ctx
        # dimensions card
        self.dims = W.QWidget()
        h = W.QHBoxLayout(self.dims)
        h.setContentsMargins(0, 0, 0, 0)
        self.lab = {}
        for k, name in (('l', 'Length'), ('w', 'Width'), ('h', 'Height')):
            box = W.QVBoxLayout()
            self.lab[k] = W.QLabel('–')
            self.lab[k].setStyleSheet('font-size:16px;font-weight:600;')
            box.addWidget(self.lab[k])
            box.addWidget(W.QLabel(name + ' (mm)'))
            h.addLayout(box)
        # controls
        self.panel = W.QWidget()
        v = W.QVBoxLayout(self.panel)
        v.setContentsMargins(0, 0, 0, 0)
        self.sliders = W.QVBoxLayout()
        v.addLayout(self.sliders)
        row = W.QHBoxLayout()
        for text, fn in (('Mirror L/R', self.mirror), ('Z-up → Y-up', self.zup), ('Reset', self.reset)):
            b = W.QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        v.addLayout(row)
        ctx.bus.on('project:changed', self.render)
        ctx.bus.on('geometry:changed', self.apply)

    def t(self):
        return self.ctx.store.cur()['t']

    def apply(self, _=None):
        v = self.ctx.viewer
        v.set_matrix(matrix(self.t()))
        if v.last_mesh is None:
            return
        lo, size = dimensions(v.last_mesh, self.t())
        v.set_ground(float(lo[1]))
        for k, val in (('l', size[0]), ('h', size[1]), ('w', size[2])):
            self.lab[k].setText(f'{val:.1f}')
        self.ctx.bus.emit('transform:changed')

    def _set(self, k, val):
        self.t()[k] = val
        self.ctx.store.save()
        self.apply()

    def render(self, _=None):
        ui.clear(self.sliders)
        for k, label, lo, hi in SL:
            ui.slider(self.sliders, label, lo, hi, 1, self.t()[k], partial(self._set, k), '%' if k[0] == 's' else '°')
        self.apply()

    def mirror(self):
        self._set('mir', not self.t()['mir'])

    def zup(self):
        t = self.t()
        t['rx'] = t['rx'] + 270 if t['rx'] - 90 < -180 else t['rx'] - 90
        self.ctx.store.save()
        self.render()

    def reset(self):
        self.ctx.store.cur()['t'] = default_transform()
        self.ctx.store.save()
        self.render()
