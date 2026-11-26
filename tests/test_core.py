import numpy as np
import pytest

from lastlab.core.bus import Bus
from lastlab.core.store import Store, default_upper
from lastlab.features import generator as G
from lastlab.features.importer import parse_obj, parse_stl, process
from lastlab.features.transform import dimensions, matrix
from lastlab.core.store import default_transform


def test_generator_dimensions():
    s = G.PRESETS['sneaker']
    m = G.gen(s)
    lo, hi = m.bbox
    assert hi[0] - lo[0] == pytest.approx(s['L'], rel=1e-3)
    assert hi[2] - lo[2] == pytest.approx(s['W'], rel=.02)
    assert 200 < G.girth(s, s['ball']) < 400
    # outward orientation (positive volume)
    a, b, c = (m.v[m.f[:, i]] for i in range(3))
    assert np.einsum('ij,ij->i', a, np.cross(b, c)).sum() > 0


def test_stl_obj_import_roundtrip():
    stl = b"solid x\n" + b"".join(
        f"facet normal 0 0 0\nouter loop\nvertex {a}\nvertex {b}\nvertex {c}\nendloop\nendfacet\n".encode()
        for a, b, c in [("0 0 0", "1 0 0", "0 1 0"), ("0 0 0", "0 1 0", "0 0 1")]) + b"endsolid"
    v, f = parse_stl(stl)
    assert v.shape == (6, 3) and f.shape == (2, 3)
    v, f = parse_obj("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 2 3 4\n")
    assert f.shape == (2, 3)
    m = process(v, f)
    assert len(m.f) == 2


def test_transform_dims():
    m = G.gen(G.PRESETS['sneaker'])
    t = default_transform()
    t['sx'] = 110
    _, size = dimensions(m, t)
    assert size[0] == pytest.approx(m.bbox[1][0] * 2 * 1.1, rel=1e-6)
    assert np.allclose(matrix(default_transform()), np.eye(4))


def test_upper_build():
    pytest.importorskip('pyvista')
    from lastlab.features.upper_design import STYLES, build
    m = G.gen(G.PRESETS['sneaker'])
    u = {**default_upper(), **STYLES['derby']}
    shell, colors = build(m, u)
    assert shell is not None and len(colors) == len(shell.f)
    u['margin'] = 0
    full, _ = build(m, u)
    assert len(full.f) > len(shell.f)


def test_store(tmp_path):
    bus, seen = Bus(), []
    bus.on('project:changed', seen.append)
    s = Store(bus, tmp_path / 'p.json')
    s.ensure()
    p = s.create('A')
    s.select(p['id'])
    s.remove(p['id'])
    assert seen and s.cur() is not None
    assert Store(bus, tmp_path / 'p.json').all()
