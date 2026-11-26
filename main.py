"""LastLab – Footwear CAD MVP (Python). Bootstrap: builds the viewer + feature modules and wires them together."""
import sys
from pathlib import Path
from types import SimpleNamespace

from PySide6 import QtCore as C, QtGui as G, QtWidgets as W

from lastlab.core import ui
from lastlab.core.bus import Bus
from lastlab.core.model import Model
from lastlab.core.store import Store
from lastlab.core.viewer import Viewer
from lastlab.features.importer import Importer
from lastlab.features.last_design import LastDesign
from lastlab.features.library import Library
from lastlab.features.projects import Projects
from lastlab.features.transform import Transform
from lastlab.features.upper_design import UpperDesign


class MainWindow(W.QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle('LastLab – Footwear CAD')
        self.resize(1400, 850)
        self.setAcceptDrops(True)
        ctx.viewer = Viewer(self)
        ctx.importer = Importer(ctx)
        ctx.model = Model(ctx)
        ctx.bus.on('status', lambda t: self.statusBar().showMessage(t))
        ctx.bus.on('project:changed', lambda _=None: ctx.model.refresh(True))  # first: geometry exists before panels render
        ctx.store.ensure()
        ctx.projects, ctx.library = Projects(ctx), Library(ctx)
        ctx.transform, ctx.last_design, ctx.upper = Transform(ctx), LastDesign(ctx), UpperDesign(ctx)

        left = W.QWidget()
        lv = W.QVBoxLayout(left)
        lv.addWidget(ctx.projects.panel, 1)
        lv.addWidget(ctx.library.panel, 1)
        left.setFixedWidth(260)

        center = W.QWidget()
        cv = W.QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)
        bar = W.QHBoxLayout()
        for name in ('iso', 'side', 'top', 'front'):
            b = W.QPushButton(name.title())
            b.clicked.connect(lambda _=False, n=name: ctx.viewer.view(n))
            bar.addWidget(b)
        fit = W.QPushButton('Fit')
        fit.clicked.connect(ctx.viewer.fit)
        bar.addWidget(fit)
        bar.addStretch()
        cv.addLayout(bar)
        cv.addWidget(ctx.viewer.interactor if hasattr(ctx.viewer, 'interactor') else ctx.viewer, 1)

        display = W.QWidget()
        dv = W.QVBoxLayout(display)
        dv.setContentsMargins(0, 0, 0, 0)
        ui.check(dv, 'Wireframe', False, ctx.viewer.set_wireframe)
        ui.check(dv, 'Ground grid', True, ctx.viewer.set_grid)
        dv.addWidget(W.QLabel('Left-drag: orbit · Shift+left / middle-drag: pan · Right-drag / wheel: zoom'))

        right_inner = W.QWidget()
        rv = W.QVBoxLayout(right_inner)
        rv.addWidget(W.QLabel('<b>DIMENSIONS</b>'))
        rv.addWidget(ctx.transform.dims)
        rv.addWidget(ui.Section('Last design', ctx.last_design.panel, True))
        rv.addWidget(ui.Section('Upper design', ctx.upper.panel, True))
        rv.addWidget(ui.Section('Transform', ctx.transform.panel, False))
        rv.addWidget(ui.Section('Display', display, False))
        rv.addStretch()
        right = W.QScrollArea()
        right.setWidgetResizable(True)
        right.setWidget(right_inner)
        right.setFixedWidth(310)

        central = W.QWidget()
        h = W.QHBoxLayout(central)
        h.addWidget(left)
        h.addWidget(center, 1)
        h.addWidget(right)
        self.setCentralWidget(central)

        fm = self.menuBar().addMenu('&File')
        fm.addAction('Import last…', ctx.library.browse)
        fm.addAction('Export last as STL…', lambda: self.export('last'))
        fm.addAction('Export upper as STL…', lambda: self.export('upper'))
        fm.addSeparator()
        fm.addAction('Quit', self.close)

        ctx.bus.emit('project:changed')

    def export(self, which):
        path, _ = W.QFileDialog.getSaveFileName(self, f'Export {which}', f'{which}.stl', 'STL (*.stl)')
        if path:
            try:
                self.ctx.viewer.export(path, which)
                self.statusBar().showMessage(f'Exported {path}')
            except Exception as e:
                self.statusBar().showMessage(f'Export failed: {e}')

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            self.ctx.importer.import_file(url.toLocalFile())
            break

    def closeEvent(self, e):
        self.ctx.viewer.close()
        super().closeEvent(e)


def main():
    app = W.QApplication(sys.argv)
    qss = Path(__file__).parent / 'resources' / 'style.qss'
    if qss.exists():
        app.setStyleSheet(qss.read_text())
    ctx = SimpleNamespace(bus=Bus())
    ctx.store = Store(ctx.bus)
    win = MainWindow(ctx)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
