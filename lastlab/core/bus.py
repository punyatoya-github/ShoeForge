"""Tiny event bus. Modules talk through events, never through each other's widgets."""


class Bus:
    def __init__(self):
        self._h = {}

    def on(self, event, fn):
        self._h.setdefault(event, []).append(fn)

    def emit(self, event, data=None):
        for fn in list(self._h.get(event, [])):
            fn(data)
