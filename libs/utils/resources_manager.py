import ctypes
import io
import keyword
import os
import pathlib
import sqlite3

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QFile
from PyQt6.uic import loadUi

from .debugger import debug


def get_db():
    path = os.path.join('.', 'db', 'resources.db')

    if os.path.exists(path):
        return path

    else:
        debug("couldn't find resources file !", _c="e")
        exit(0)


def import_(path: str, r=None):
    if os.getenv("dev-env-loading"):

        if path.startswith("plugins"):
            x = pathlib.Path(path)
            path = os.path.join("src", "plugins", x.parent.name, "src", x.name)
        else:
            path = os.path.join("src", path)

        data = [[open(path, "rb").read(), os.path.basename(path).split(".")[-1]]]
    else:
        cursor = sqlite3.connect(get_db()).cursor()
        data = cursor.execute("SELECT content, type FROM resources WHERE key = ?", (path, )).fetchall()

    if not data:
        debug(f"{os.path.basename(path)} : missing resources file !", _c="e")
        data = [[b"", os.path.basename(path).split(".")[-1]]]

    data, type_ = data[0]

    if r == "r":
        return data

    if r == "io":
        return io.BytesIO(data)

    if type_ == "ui":
        return loadUi(io.StringIO(data.decode()))

    if type_ in ["png", "svg", "jpg", "jpeg"]:
        img = QImage()
        img.loadFromData(data)
        return QPixmap(img)

    return [data, type_]


def read_file(path, b=False):
    file = QFile(path)
    if file.open(QFile.OpenModeFlag.ReadOnly):
        k = bytes(file.readAll())
        k = k.decode() if not b else k
    else:
        k = "" if not b else b""
    return k


def get_object_from_memory(idn):
    if str(idn).isdigit():
        return ctypes.cast(int(str(idn)), ctypes.py_object).value
    return idn


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
