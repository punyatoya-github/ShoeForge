# LastLab – Footwear CAD MVP (Python)

Desktop Python port of the LastLab web MVP, with the same module structure: projects, shoe last library/import, 3D view and manipulation, **last design** and **basic upper design**.

**Stack:** Python 3.10+, PySide6 (UI), pyvista + pyvistaqt (3D viewport), numpy (geometry).

## Run
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
pytest                                               # unit tests (generator, importer, transform, upper, store)
```
Projects are saved to `~/.lastlab/projects.json` (override with the `LASTLAB_HOME` env var). Imported files are remembered by path, so they reload with the project.

## Features
| Module | What it does |
|---|---|
| Projects | Create / switch / delete projects |
| Library & import | 3 parametric lasts; import `.stl` / `.obj` (button, File menu or drag-and-drop). Imports are welded, centred, oriented length-along-X and scaled to mm |
| Viewer | Orbit / pan / zoom, Iso / Side / Top / Front / Fit, wireframe, ground grid |
| Transform | Scale L/W/H, rotate XYZ, mirror, Z-up fix, live dimensions in mm |
| Last design | Length, ball width, heel width, instep/back height, heel height, toe spring, ball position, toe shape, section shape; live ball and waist girth |
| Upper design | Real mesh shell offset from the last: style presets, material finish, thickness, sole margin (feather), collar height, throat length, toe cap / body / heel counter zones with stitch lines, colours |
| Export | File menu: export last or upper as STL (with transform applied) |

## Structure (mirrors the JS version)
```
main.py                     bootstrap + main window (was index.html + js/main.js)
resources/style.qss         styles (was css/style.css)
lastlab/
  core/
    bus.py                  event bus
    ui.py                   slider / select / checkbox / colour / collapsible-section helpers
    store.py                project state + persistence
    mesh.py                 numpy mesh helper (weld, orient, normals, pyvista conversion)
    model.py                builds last geometry for the current project
    viewer.py               3D viewport, camera views, export
  features/
    projects.py  library.py  importer.py  generator.py
    transform.py  last_design.py  upper_design.py
tests/test_core.py
```
Modules communicate through `Bus` events: `project:changed`, `geometry:changed`, `transform:changed`, `import:loaded`, `status`. Each feature is a class taking a shared `ctx` (bus, store, viewer, model, …) and exposing a `panel` widget.
To add a feature: create `lastlab/features/<name>.py`, instantiate it in `main.py`, and place its `panel` in the window.

## Differences from the JS version
- The upper is real geometry (subdivided, offset along normals, faces removed by the cut rules) instead of a shader, so it can be exported.
- Imports are welded on load, which removes the seams the web version could show, and are persisted by file path.
- Mouse: left-drag orbit, Shift+left or middle-drag pan, right-drag/wheel zoom (VTK trackball style).

## Known limits
- Upper zones assume x runs heel→toe; use "Flip heel/toe" for imports oriented the other way.
- No pattern flattening or DXF export yet; roadmap: style lines on the last, sole/heel modelling, undo/redo, project files with embedded meshes.
