import os
import ctypes

__all__ = ["comp_object", "comp_update", "comp_parse", "comp_on", "comp_update_inspector"]


def comp_object(idn: str | int = None):
    return ctypes.cast(
        int(os.environ["composer.id"] or "0") or \
        int(str(os.environ[str(idn)] if not str(idn).isdigit() else str(idn))),
        ctypes.py_object).value


def comp_update(*args):
    comp_object().update(*args)


def comp_update_inspector(line):
    comp_object().update_inspector(line)


def comp_parse(code, path):
    comp_object().parse(code, path)


def comp_on(name, func):
    comp_object().on(name, func)


