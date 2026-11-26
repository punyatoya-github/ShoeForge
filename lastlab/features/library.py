"""Last library panel + file import wiring."""
from PySide6 import QtCore as C, QtWidgets as W

from lastlab.features import generator as G


class Library:
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = W.QWidget()
        v = W.QVBoxLayout(self.panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(W.QLabel('<b>SHOE LAST LIBRARY</b>'))
        self.list = W.QListWidget()
        v.addWidget(self.list, 1)
        imp = W.QPushButton('Import STL / OBJ…')
        v.addWidget(imp)
        hint = W.QLabel('Or drop a file on the window. Imports are oriented length-along-X and scaled to mm.')
        hint.setWordWrap(True)
        v.addWidget(hint)
        imp.clicked.connect(self.browse)
        self.list.itemClicked.connect(self.pick)
        ctx.bus.on('import:loaded', self.loaded)
        ctx.bus.on('project:changed', self.render)

    def browse(self):
        path, _ = W.QFileDialog.getOpenFileName(self.panel, 'Import shoe last', '', 'Meshes (*.stl *.obj)')
        if path:
            self.ctx.importer.import_file(path)

    def pick(self, item):
        p = self.ctx.store.cur()
        p['lastId'] = item.data(C.Qt.UserRole)
        p['spec'] = {}
        self.ctx.store.save()
        self.ctx.bus.emit('project:changed')

    def loaded(self, rec):
        p = self.ctx.store.cur()
        p.update({'import': rec, 'lastId': 'import', 'spec': {}})
        self.ctx.store.save()
        self.ctx.bus.emit('project:changed')

    def render(self, _=None):
        p = self.ctx.store.cur()
        self.list.blockSignals(True)
        self.list.clear()
        items = [(k, f"{s['name']}   {s['L']}×{s['W']}") for k, s in G.PRESETS.items()]
        if p.get('import'):
            items.append(('import', p['import']['name'] + '   (imported)'))
        for k, text in items:
            it = W.QListWidgetItem(text)
            it.setData(C.Qt.UserRole, k)
            self.list.addItem(it)
            if k == p['lastId']:
                self.list.setCurrentItem(it)
        self.list.blockSignals(False)
