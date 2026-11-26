"""BASIC UPPER DESIGN: a real mesh shell offset from the last surface (so it can be exported), cut by a sole margin
(feather) and a collar opening, split into toe cap / body / heel counter zones with stitch lines."""
from functools import partial

import numpy as np
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W

from lastlab.core import ui
from lastlab.core.mesh import Mesh

STYLES = {'sneaker': dict(collar=.72, throat=.3, toe=.8, heel=.22), 'derby': dict(collar=.78, throat=.34, toe=.84, heel=.2),
          'boot': dict(collar=.85, throat=.22, toe=.8, heel=.25), 'pump': dict(collar=.6, throat=.52, toe=.9, heel=.12)}
MATS = ['leather', 'suede', 'patent', 'mesh']


def rgb(hexcol):
    c = G.QColor(hexcol)
    return np.array([c.red(), c.green(), c.blue()], np.uint8)


def build(mesh, u, max_faces=60000):
    """Return (shell Mesh, per-face RGB) or (None, None) if nothing remains."""
    v, f = mesh.v, mesh.f
    if len(f) < max_faces:  # one linear subdivision gives smoother cut lines
        import pyvista as pv
        pd = pv.PolyData(v, np.hstack([np.full((len(f), 1), 3), f]).ravel()).subdivide(1, subfilter='linear')
        v, f = np.asarray(pd.points, float), pd.faces.reshape(-1, 4)[:, 1:]
    m = Mesh(v, f)
    n = m.vertex_normals()
    lo, hi = mesh.bbox
    q = (v[f].mean(1) - lo) / (hi - lo)
    nx = 1 - q[:, 0] if u['flip'] else q[:, 0]
    fny = n[f][:, :, 1].mean(1)
    keep = ~(fny < -(1 - u['margin'])) & ~((nx < u['throat']) & (q[:, 1] > u['collar']))
    if not keep.any():
        return None, None
    col = np.where((nx > u['toe'])[:, None], rgb(u['c2']), np.where((nx < u['heel'])[:, None], rgb(u['c3']), rgb(u['c1'])))
    stitch = np.minimum(abs(nx - u['toe']), abs(nx - u['heel'])) < .006
    col[stitch] = (20, 20, 20)
    return Mesh(v + n * u['thick'], f[keep]), col[keep].astype(np.uint8)


class UpperDesign:
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = W.QWidget()
        self.box = W.QVBoxLayout(self.panel)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.timer = C.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.rebuild)
        ctx.bus.on('geometry:changed', lambda _=None: self.timer.start(10))
        ctx.bus.on('project:changed', self.render)

    def u(self):
        return self.ctx.store.cur()['upper']

    def set(self, k, val):
        self.u()[k] = val
        self.ctx.store.save()
        self.timer.start(40)

    def style(self, name):
        self.u().update(style=name, **STYLES[name])
        self.ctx.store.save()
        C.QTimer.singleShot(0, self.render)  # rebuild controls after the combo box finishes its signal
        self.timer.start(10)

    def render(self, _=None):
        u, b, s = self.u(), self.box, self.set
        ui.clear(b)
        ui.check(b, 'Show upper', u['on'], partial(s, 'on'))
        ui.select(b, 'Style', [(k, k.title()) for k in STYLES], u['style'], self.style)
        ui.select(b, 'Material', [(k, k.title()) for k in MATS], u['mat'], partial(s, 'mat'))
        for k, label, lo, hi, st, unit in [('thick', 'Thickness', .5, 6, .1, ' mm'), ('margin', 'Sole margin (feather)', 0, .9, .01, ''),
                                           ('collar', 'Collar height', .4, 1, .01, ''), ('throat', 'Throat length', 0, .6, .01, ''),
                                           ('toe', 'Toe cap start', .5, .95, .01, ''), ('heel', 'Heel counter end', .05, .4, .01, '')]:
            ui.slider(b, label, lo, hi, st, u[k], partial(s, k), unit)
        ui.check(b, 'Flip heel/toe (for imports)', u['flip'], partial(s, 'flip'))
        ui.check(b, 'Hide last (upper only)', u['hideLast'], partial(s, 'hideLast'))
        for k, label in (('c1', 'Body'), ('c2', 'Toe cap'), ('c3', 'Heel counter')):
            ui.color(b, label, u[k], partial(s, k))

    def rebuild(self):
        v, p = self.ctx.viewer, self.ctx.store.cur()
        if v.last_mesh is None or not p:
            return
        u = p['upper']
        shell, colors = build(v.last_mesh, u) if u['on'] else (None, None)
        v.set_upper(shell, colors, u['mat'], u['on'], u['hideLast'])
