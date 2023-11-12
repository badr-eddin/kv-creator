import ctypes
import os
from PyQt6.QtCore import QFile


def import_(path: str, r=False, posix=False):
    if os.getenv("dev-env"):
        return os.path.join("src", path) if not r else open(os.path.join("src", path), "r").read()
    return (QFile(f":/{path}") if not posix else f":/{path}") if not r else read_file(f":/{path}", True)


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

