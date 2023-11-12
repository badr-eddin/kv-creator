from ..utils import *


class Buttons:
    def __init__(self, main=None):
        self.main = main

    def get_obj(self, _s: str):
        _o = _s.split(".")
        if len(_o) > 1:
            if _o[0] == "#":
                if hasattr(self.main, _o[1]):
                    return getattr(self.main, _o[1])

            elif _o[0] in self.main.components:
                obj = self.main.components[_o[0]]
                if hasattr(obj, _o[1]):
                    return getattr(obj, _o[1])
                else:
                    debug(f"{_o[0]} has no attribute '{_o[1]}'", _c="e")
        else:
            return self.main.components.get(_s)

    def connect(self, _f, _o, _a=None, _c=None, _t=QPushButton):

        if isinstance(_o, tuple):
            _o = find_in(*_o, _t)

        if isinstance(_f, str):
            if _f.startswith("$"):
                _f = getattr(self, _f[1:])

            elif _f.startswith("@"):
                _f = getattr(self.main, _f[1:])

            elif len(_f.split(".")) > 1:
                __f = self.main.components.get(_f.split(".")[0])
                if __f:
                    _f = getattr(__f, _f.split(".")[1])

            else:
                _f = None

        if _a:
            if _o and _f:
                if _c:
                    _cl = getattr(_o, _c)
                else:
                    _cl = getattr(_o, "clicked")
                _cl.connect(lambda: _f(*_a))
        else:
            if _o and _f:
                if _c:
                    _cl = getattr(_o, _c)
                else:
                    _cl = getattr(_o, "clicked")
                _cl.connect(_f)
