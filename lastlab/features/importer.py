"""STL / OBJ import. Imports are welded, centred, oriented length-along-X and scaled to mm."""
import re
import struct
from pathlib import Path

import numpy as np

from lastlab.core.mesh import Mesh


def parse_stl(data: bytes):
    n = struct.unpack('<I', data[80:84])[0] if len(data) >= 84 else 0
    if len(data) == 84 + 50 * n and n:
        dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
        v = np.frombuffer(data, dt, count=n, offset=84)['v'].reshape(-1, 3).astype(float)
    else:
        rows = re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)', data.decode('utf-8', 'ignore'))
        v = np.array(rows, float).reshape(-1, 3)
    return v, np.arange(len(v)).reshape(-1, 3)


def parse_obj(text: str):
    v, f = [], []
    for line in text.splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == 'v':
            v.append([float(x) for x in p[1:4]])
        elif p[0] == 'f':
            idx = [int(t.split('/')[0]) for t in p[1:]]
            idx = [k - 1 if k > 0 else len(v) + k for k in idx]
            f += [[idx[0], idx[i], idx[i + 1]] for i in range(1, len(idx) - 1)]
    return np.array(v, float), np.array(f, int)


def process(v, f) -> Mesh:
    m = Mesh(v, f).welded().center()
    if len(m.f) == 0:
        raise ValueError('No triangles found')
    x, y, z = m.bbox[1] - m.bbox[0]
    if z > x and z >= y:
        m.v = m.v @ np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float).T
    elif y > x and y > z:
        m.v = m.v @ np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float).T
    mx = float((m.bbox[1] - m.bbox[0]).max())
    m.v = m.v * (1000 if mx < 2 else 10 if mx < 40 else 1)
    return m.oriented().center()


class Importer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cache = {}

    def load(self, path):
        path = str(path)
        if path not in self.cache:
            p = Path(path)
            if p.suffix.lower() == '.obj':
                v, f = parse_obj(p.read_text(errors='ignore'))
            else:
                v, f = parse_stl(p.read_bytes())
            self.cache[path] = process(v, f)
        return self.cache[path]

    def get(self, project):
        rec = project.get('import')
        if not rec:
            return None
        try:
            return self.load(rec['path'])
        except Exception:
            return None

    def import_file(self, path):
        try:
            self.load(path)
        except Exception as e:
            self.ctx.bus.emit('status', f'Import failed: {e}')
            return
        self.ctx.bus.emit('import:loaded', {'name': Path(path).name, 'path': str(path)})
