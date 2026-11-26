"""Parametric last generator: lofts elliptical-ish cross-sections from heel (t=0) to toe (t=1)."""
import math

import numpy as np

from lastlab.core.mesh import Mesh

PRESETS = {
    'sneaker': dict(name='Men’s sneaker last', L=290, W=105, hw=.62, H=85, heel=20, spring=12, p=.75, ball=.7, tp=.55),
    'pump': dict(name='Women’s pump last', L=245, W=78, hw=.62, H=70, heel=75, spring=14, p=.8, ball=.7, tp=.55),
    'boot': dict(name='Chelsea boot last', L=285, W=100, hw=.62, H=125, heel=28, spring=14, p=.7, ball=.7, tp=.55),
}


def ss(a, b, x):
    x = min(1.0, max(0.0, (x - a) / (b - a)))
    return x * x * (3 - 2 * x)


def sp(v, e):
    return np.sign(v) * np.abs(v) ** e


def spec(p):
    return {**PRESETS.get(p['lastId'], PRESETS['sneaker']), **p.get('spec', {})}


def sect(s, t, m):
    """Cross-section at t as an (m, 2) array of [y, z]."""
    w = s['W'] * (s['hw'] + (1 - s['hw']) * ss(0, s['ball'], t))
    if t > s['ball']:
        w *= math.cos((t - s['ball']) / (1 - s['ball']) * math.pi / 2) ** s['tp']
    f = 1.0
    if t < .05:
        f = math.sqrt(1 - (1 - t / .05) ** 2)
    if t > .96:
        f = math.sqrt(max(0.0, 1 - ((t - .96) / .04) ** 2))
    w *= f
    T = s['H'] * (1 - .72 * ss(.18, .95, t)) * f
    bot = s['heel'] * (1 - ss(0, .5, t)) + s['spring'] * ss(.82, 1, t)
    a = np.arange(m) / m * 2 * np.pi
    c, sn = np.cos(a), np.sin(a)
    y = bot + T / 2 + sp(sn, np.where(sn < 0, s['p'] * .6, s['p'])) * T / 2
    z = sp(c, s['p']) * w / 2
    return np.stack([y, z], 1)


def gen(s, n=70, m=44):
    rings = [np.column_stack([np.full(m, i / n * s['L']), sect(s, i / n, m)]) for i in range(n + 1)]
    v = np.concatenate(rings)
    i, j = np.meshgrid(np.arange(n), np.arange(m), indexing='ij')
    a = (i * m + j).ravel()
    b = (i * m + (j + 1) % m).ravel()
    c, d = a + m, b + m
    f = np.concatenate([np.stack([a, c, b], 1), np.stack([b, c, d], 1)])
    return Mesh(v, f).center()


def girth(s, t, sy=1.0, sz=1.0, n=90):
    """Perimeter of the section at t (mm), with height/width scale factors."""
    pts = sect(s, t, n)
    d = (np.roll(pts, -1, axis=0) - pts) * [sy, sz]
    return float(np.hypot(d[:, 0], d[:, 1]).sum())
