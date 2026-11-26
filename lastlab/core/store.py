"""Project state + JSON persistence (~/.lastlab/projects.json, override with LASTLAB_HOME)."""
import json
import os
import random
import string
import time
from pathlib import Path


def default_transform():
    return dict(sx=100, sy=100, sz=100, rx=0, ry=0, rz=0, mir=False)


def default_upper():
    return dict(on=True, style='sneaker', mat='leather', thick=2.5, margin=.7, collar=.72, throat=.3,
                toe=.8, heel=.22, flip=False, hideLast=False, c1='#e8e4dc', c2='#2b2b2b', c3='#b4531f')


class Store:
    def __init__(self, bus, path=None):
        self.bus = bus
        home = Path(os.environ.get('LASTLAB_HOME', Path.home() / '.lastlab'))
        self.path = Path(path) if path else home / 'projects.json'
        self.data = self._load()

    def _load(self):
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {'projects': [], 'cur': None}

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=1))
        except OSError:
            pass

    def all(self):
        return self.data['projects']

    def cur(self):
        return next((p for p in self.all() if p['id'] == self.data['cur']), None)

    def create(self, name=''):
        pid = hex(int(time.time() * 1000))[2:] + ''.join(random.choices(string.ascii_lowercase, k=3))
        p = dict(id=pid, name=name or f'Project {len(self.all()) + 1}', lastId='sneaker', spec={},
                 t=default_transform(), upper=default_upper(), **{'import': None})
        self.all().append(p)
        self.data['cur'] = pid
        self.save()
        return p

    def select(self, pid):
        self.data['cur'] = pid
        self.save()
        self.bus.emit('project:changed')

    def remove(self, pid):
        self.data['projects'] = [p for p in self.all() if p['id'] != pid]
        if not self.all():
            self.create('Untitled')
        if not self.cur():
            self.data['cur'] = self.all()[0]['id']
        self.save()

    def ensure(self):
        if not self.all():
            self.create('My first shoe')
        if not self.cur():
            self.data['cur'] = self.all()[0]['id']
        for p in self.all():
            p.setdefault('spec', {})
            p.setdefault('import', None)
            p['t'] = {**default_transform(), **p.get('t', {})}
            p['upper'] = {**default_upper(), **p.get('upper', {})}
