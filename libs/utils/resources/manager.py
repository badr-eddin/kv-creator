from ..functions import debug
from ...pyqt import QPixmap, QImage, QFile, loadUi

import ctypes
import io
import os
import pathlib
import sqlite3


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
