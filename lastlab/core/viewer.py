"""3D viewport (pyvista + Qt): last + upper actors, ground grid, camera views, user transform."""
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor

DIRS = {'iso': (.8, 1.1), 'side': (0, np.pi / 2), 'top': (0, .02), 'front': (np.pi / 2, np.pi / 2)}
FINISH = {'leather': (.3, 20), 'suede': (0, 1), 'patent': (1, 90), 'mesh': (.1, 5)}


class Viewer(QtInteractor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_background('#e9e6df', top='#c9c4ba')
        self.enable_trackball_style()
        self.matrix = np.eye(4)
        self.last_mesh = None
        self.last = self.upper = None
        self.wire = self.hide_last = False
        plane = pv.Plane(direction=(0, 1, 0), i_size=600, j_size=600, i_resolution=30, j_resolution=30)
        self.grid = self.add_mesh(plane, style='wireframe', color='#888888', opacity=.35,
                                  pickable=False, reset_camera=False)
        self.view('iso', fit=False)

    # --- actors -------------------------------------------------------
    def _apply(self):
        for a in (self.last, self.upper):
            if a is not None:
                a.user_matrix = self.matrix

    def set_last(self, mesh):
        self.last_mesh = mesh
        self.last = self.add_mesh(mesh.to_pv(), name='last', color='#caa47c', specular=.3, specular_power=20,
                                  smooth_shading=False, reset_camera=False)
        self.last.prop.interpolation = 'Phong'
        self.last.prop.style = 'wireframe' if self.wire else 'surface'
        self.last.SetVisibility(not self.hide_last)
        self._apply()
        self.render()

    def set_upper(self, shell, colors, finish, visible=True, hide_last=False):
        if self.upper is not None:
            self.remove_actor('upper', render=False)
            self.upper = None
        self.hide_last = hide_last and shell is not None and visible
        if shell is not None and visible:
            spec, power = FINISH[finish]
            self.upper = self.add_mesh(shell.to_pv(colors), name='upper', scalars='rgb', rgb=True, specular=spec,
                                       specular_power=power, smooth_shading=False, reset_camera=False)
            self.upper.prop.interpolation = 'Phong'
        if self.last is not None:
            self.last.SetVisibility(not self.hide_last)
        self._apply()
        self.render()

    def set_wireframe(self, on):
        self.wire = on
        if self.last is not None:
            self.last.prop.style = 'wireframe' if on else 'surface'
        self.render()

    def set_grid(self, on):
        self.grid.SetVisibility(on)
        self.render()

    def set_matrix(self, m):
        self.matrix = m
        self._apply()
        self.render()

    def set_ground(self, y):
        self.grid.position = (0, y, 0)

    # --- camera -------------------------------------------------------
    def world_bounds(self):
        lo, hi = self.last_mesh.bbox
        c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        w = c @ self.matrix[:3, :3].T
        return w.min(0), w.max(0)

    def view(self, name, fit=True):
        th, ph = DIRS[name]
        self._look(np.array([np.sin(ph) * np.sin(th), np.cos(ph), np.sin(ph) * np.cos(th)]), fit)

    def fit(self):
        pos, foc, _ = self.camera_position
        d = np.array(pos) - np.array(foc)
        self._look(d / np.linalg.norm(d) if np.linalg.norm(d) else np.array([.5, .5, .7]), True)

    def _look(self, d, fit):
        if self.last_mesh is None or not fit:
            c, r = np.zeros(3), 600.0
        else:
            lo, hi = self.world_bounds()
            c, r = (lo + hi) / 2, float((hi - lo).max()) * 2.2
        self.camera_position = [tuple(c + d * r), tuple(c), (0, 1, 0)]
        self.reset_camera_clipping_range()
        self.render()

    def export(self, path, which='last'):
        shell = self.upper if which == 'upper' else self.last
        if shell is None:
            raise ValueError(f'No {which} to export')
        poly = shell.mapper.dataset.copy()
        poly.transform(self.matrix, inplace=True)
        poly.extract_surface().save(path)
