import importlib
import keyword
import os
import pathlib
import re

from PyQt6.QtWidgets import QWidget

from .debugger import debug


class PLoader:
    path = pathlib.Path(os.path.join(".", "plugins"))
    check = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    forbidden = ["__init__", "__pycache__"]
    variables = {"CLASS": (QWidget, object), "VERSION": (float, ), "TYPE": (str, ), "NAME": (str, )}

    def __init__(self, main,  callback):
        self.main = main
        self.callback = callback

    def filename_check(self, path):
        name, ext = os.path.splitext(os.path.basename(path))
        valid = self.check.match(name) and name not in keyword.kwlist and name not in self.forbidden

        if valid and os.path.isfile(path) and ext == (".py" if os.getenv("dev-env") else ".so"):
            return name

    def is_plugin_valid(self, plugin):
        for var in self.variables:
            if not hasattr(plugin, var):
                return False

            if not isinstance(getattr(plugin, var), self.variables.get(var)):
                types = tuple([i.__name__ for i in self.variables.get(var)])
                debug(f"unmatched data types! '{var}' Expected {types}", _c="e")
                return False

        return True

    def load_from_path(self, path):
        name = self.filename_check(path)
        if name:
            debug(f"loading plugin '{name}' ...")

            plugin_obj = importlib.machinery.SourceFileLoader(name, path).load_module()

            if self.is_plugin_valid(plugin_obj) and self.callback:
                self.callback(plugin_obj)
            else:
                debug(f"couldn't load plugin '{name}' !", _c="e")
        else:
            debug(f"invalid plugin '{path}' !", _c="e")

    def load(self):
        if self.path.exists():
            plugins = os.listdir(self.path.as_posix())
            for plugin in plugins:
                path = os.path.join(self.path.as_posix(), plugin)
                self.load_from_path(path)