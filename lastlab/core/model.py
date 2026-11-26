"""Builds the last geometry for the current project and pushes it to the viewer."""
from lastlab.features import generator as G


class Model:
    def __init__(self, ctx):
        self.ctx = ctx

    def geometry(self, p):
        if p['lastId'] == 'import':
            m = self.ctx.importer.get(p)
            if m is not None:
                return m, ''
            return G.gen(G.PRESETS['sneaker']), 'Imported file not found – re-import it. Showing default last.'
        if p['lastId'] in G.PRESETS:
            return G.gen(G.spec(p)), ''
        return G.gen(G.PRESETS['sneaker']), ''

    def refresh(self, fit=False):
        p = self.ctx.store.cur()
        if not p:
            return
        mesh, warn = self.geometry(p)
        self.ctx.viewer.set_last(mesh)
        self.ctx.bus.emit('geometry:changed', mesh)
        if fit:
            self.ctx.viewer.fit()
        rec = p.get('import')
        name = rec['name'] if p['lastId'] == 'import' and rec else G.PRESETS.get(p['lastId'], G.PRESETS['sneaker'])['name']
        self.ctx.bus.emit('status', warn or f"{p['name']} · {name}")
