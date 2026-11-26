"""Triangle mesh helper (numpy) + conversion to pyvista."""
import numpy as np


class Mesh:
    def __init__(self, verts, faces):
        self.v = np.asarray(verts, float).reshape(-1, 3)
        self.f = np.asarray(faces, int).reshape(-1, 3)

    @property
    def bbox(self):
        return self.v.min(0), self.v.max(0)

    def center(self):
        lo, hi = self.bbox
        self.v = self.v - (lo + hi) / 2
        return self

    def welded(self, dec=4):
        """Merge coincident vertices (gives smooth normals, closed offsets) and drop degenerate faces."""
        uniq, inv = np.unique(np.round(self.v, dec), axis=0, return_inverse=True)
        f = inv.reshape(-1)[self.f]
        ok = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])
        return Mesh(uniq, f[ok])

    def oriented(self):
        """Flip winding if the signed volume is negative so normals point outward."""
        a, b, c = (self.v[self.f[:, i]] for i in range(3))
        if np.einsum('ij,ij->i', a, np.cross(b, c)).sum() < 0:
            self.f = self.f[:, [0, 2, 1]]
        return self

    def vertex_normals(self):
        a, b, c = (self.v[self.f[:, i]] for i in range(3))
        fn = np.cross(b - a, c - a)
        vn = np.zeros_like(self.v)
        for i in range(3):
            np.add.at(vn, self.f[:, i], fn)
        n = np.linalg.norm(vn, axis=1, keepdims=True)
        return vn / np.where(n == 0, 1, n)

    def to_pv(self, colors=None):
        import pyvista as pv
        faces = np.hstack([np.full((len(self.f), 1), 3), self.f]).ravel()
        pd = pv.PolyData(self.v, faces).compute_normals(
            cell_normals=False, point_normals=True, split_vertices=False,
            consistent_normals=False, auto_orient_normals=False)
        if colors is not None:
            pd.cell_data['rgb'] = colors
        return pd
