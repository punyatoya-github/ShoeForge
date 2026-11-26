"""Project list panel."""
from PySide6 import QtCore as C, QtWidgets as W


class Projects:
    def __init__(self, ctx):
        self.ctx = ctx
        self.panel = W.QWidget()
        v = W.QVBoxLayout(self.panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(W.QLabel('<b>PROJECTS</b>'))
        row = W.QHBoxLayout()
        self.name = W.QLineEdit()
        self.name.setPlaceholderText('New project name')
        add = W.QPushButton('Add')
        row.addWidget(self.name, 1)
        row.addWidget(add)
        v.addLayout(row)
        self.list = W.QListWidget()
        v.addWidget(self.list, 1)
        rm = W.QPushButton('Delete selected')
        v.addWidget(rm)
        add.clicked.connect(self.add)
        self.name.returnPressed.connect(self.add)
        rm.clicked.connect(self.remove)
        self.list.itemClicked.connect(lambda it: ctx.store.select(it.data(C.Qt.UserRole)))
        ctx.bus.on('project:changed', self.render)

    def add(self):
        self.ctx.store.create(self.name.text().strip())
        self.name.clear()
        self.ctx.bus.emit('project:changed')

    def remove(self):
        self.ctx.store.remove(self.ctx.store.cur()['id'])
        self.ctx.bus.emit('project:changed')

    def render(self, _=None):
        self.list.blockSignals(True)
        self.list.clear()
        cur = self.ctx.store.cur()['id']
        for p in self.ctx.store.all():
            it = W.QListWidgetItem(p['name'])
            it.setData(C.Qt.UserRole, p['id'])
            self.list.addItem(it)
            if p['id'] == cur:
                self.list.setCurrentItem(it)
        self.list.blockSignals(False)
