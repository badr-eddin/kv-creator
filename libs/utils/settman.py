import json
import dpath.util as dutil
from PyQt6.QtGui import QColor

from .resources_manager import import_
from .debugger import debug


def color(key: str, _qc=True):
    themes = settings.pull("editor-themes")
    theme_ = themes.get(settings.pull("editor-theme") or list(themes.keys())[0]) or {}
    _c = theme_.get(key.capitalize()) or "#FFFFFF"
    return QColor(_c) if _qc else _c


class settings:
    @staticmethod
    def pull(path, sep="/"):
        data = json.loads(import_("data/settings.json", True))
        try:
            return dutil.get(data, path, separator=sep)
        except Exception as e:
            debug(f"settings::pull : {e}", _c="e")
            return {}

    @staticmethod
    def push(path, value):
        data = json.loads(import_("data/settings.json", True))
        try:
            dutil.set(data, path, value)

            with open(import_("data/settings.json"), "w") as e:
                e.write(json.dumps(data, indent=4))
        except Exception as e:
            debug(f"settings::push : {e}", _c="e")
            return {}


def theme(tar, c=True):
    thm = (settings.pull("-theme") or "").lower().replace(" ", "")
    _c = ((settings.pull("themes-colors") or {}).get(thm) or {}).get(tar) or "#000000"
    if _c.startswith("#") and c:
        return QColor(_c)

    return _c
