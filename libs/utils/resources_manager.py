import ctypes
import os
from PyQt6.QtCore import QFile

MODs = {
    "r": QFile.OpenModeFlag.ReadOnly,
    "w": QFile.OpenModeFlag.WriteOnly,
    "w+": QFile.OpenModeFlag.ReadWrite,
    "r+": QFile.OpenModeFlag.ReadWrite,
}


def import_(path: str, r=False, posix=False, mode='r'):
    if os.getenv("dev-env-loading"):
        return os.path.join("src", path) if not r else open(os.path.join("src", path), "r").read()

    if not r:
        file = QFile(f":/{path}")
        file.open(MODs.get(mode))
        return file if os.path.splitext(path)[1] not in [".png", ".svg"] else f":/{path}"
    else:
        if posix:
            return f":/{path}"
        else:
            return read_file(f":/{path}")


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

