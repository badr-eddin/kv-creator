import keyword

from .debugger import debug


class duck:
    def __init__(self, obj: dict):
        self.properties = {}

        self.__recursive_loading(obj, self)

    def __getattr__(self, item):
        if item not in self.properties:
            debug(f"duck doesn't have property : '{item}' ", _c="w")
            return 0

    def __recursive_loading(self, obj, parent=None):
        parent = parent or self

        for key, value in obj.items():
            if str(key).isdigit():
                key = "_" + str(key)

            elif key in keyword.kwlist:
                key = key + "_"

            self.properties[key] = value

            if isinstance(value, dict):
                setattr(parent, key, duck(value))
            else:
                setattr(parent, key, value)


def hex2rgb(c: str):
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def hex2rgba(c: str, a):
    return tuple(list(hex2rgb(c)) + [a])
