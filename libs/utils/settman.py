import json
import sqlite3

import dpath.util as dutil
from PyQt6.QtGui import QColor

from .resources_manager import import_, get_db
from .debugger import debug


def color(key: str, _qc=True):
    themes = settings.pull("editor-themes")
    theme_ = themes.get(settings.pull("editor-theme") or list(themes.keys())[0]) or {}
    _c = theme_.get(key.capitalize()) or "#FFFFFF"
    return QColor(_c) if _qc else _c


class settings:
    @staticmethod
    def load_blob(key):
        db = sqlite3.connect(get_db())
        data = db.cursor().execute("SELECT content FRoM resources WHERE key='%s'" % key).fetchall()
        db.close()
        return data[0][0]

    @staticmethod
    def update_blob(key, data):
        db = sqlite3.connect(get_db())
        # TODO: doesnt save data
        print(db.cursor().execute(
            "UPDATE resources SET content = ? WHERE key = ?",
            (
                data if type(data) is bytes else str(data).encode(), key
            )
        ))
        db.commit()
        db.close()

    @staticmethod
    def pull(path="", sep="/", do=False):
        data = json.loads(settings.load_blob("data/settings.json").decode())
        if do:
            return data
        try:
            return dutil.get(data, path, separator=sep)
        except Exception as e:
            debug(f"settings::pull : {e}", _c="e")
            return {}

    @staticmethod
    def push(path, value):
        data = settings.pull(do=True)
        try:
            dutil.set(data, path, value)
            settings.update_blob("./src/data/settings.json", json.dumps(data, indent=4))
        except Exception as e:
            debug(f"settings::push : {e} :", _c="e")
            return {}


def theme(tar, c=True):
    thm = (settings.pull("-theme") or "").lower().replace(" ", "")
    _c = ((settings.pull("themes-colors") or {}).get(thm) or {}).get(tar) or "#000000"
    if _c.startswith("#") and c:
        return QColor(_c)

    return _c
