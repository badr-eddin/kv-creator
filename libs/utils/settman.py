import json
import os.path
import sqlite3

import dpath.util as dutil
import toml
from PyQt6.QtGui import QColor

from .resources_manager import get_db
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
        data = db.cursor().execute("SELECT content FROM resources WHERE key='%s'" % key).fetchall()
        db.close()
        return data[0][0]

    @staticmethod
    def update_blob(key, data):
        try:
            db = sqlite3.connect(get_db())
            cursor = db.cursor()
            cursor.execute(
                "UPDATE resources SET content = ? WHERE key = ?",
                (
                    data if type(data) is bytes else str(data).encode(), key
                )
            )
            db.commit()
            db.close()
        except Exception as e:
            _ = e
            debug("resources.update: error during updating resources !", _c="e")

    @staticmethod
    def delete_blob(key):
        try:
            if not settings.blob_exists(key):
                debug(f"resources.delete: {os.path.basename(key)} not exists !", _c="w")
                return

            db = sqlite3.connect(get_db())
            cursor = db.cursor()
            cursor.execute("DELETE FROM resources WHERE key = ?", (key, ))
            db.commit()
            db.close()
        except Exception as e:
            _ = e
            debug("resources.delete: error during delete resource !", _c="e")

    @staticmethod
    def blob_exists(key):
        try:
            db = sqlite3.connect(get_db())
            cursor = db.cursor()
            k = cursor.execute("SELECT type FROM resources WHERE key = ?", (key, ))
            k = k.fetchall()[0][0]
            db.commit()
            db.close()
            return k
        except Exception as e:
            _ = e

    @staticmethod
    def set_blob(key, data):
        try:
            settings.delete_blob(key)

            db = sqlite3.connect(get_db())
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO resources (content, key, type) VALUES (?, ?, ?)",
                (
                    data if type(data) is bytes else str(data).encode(), key, os.path.basename(key).split(".")[-1]
                )
            )
            db.commit()
            db.close()
        except Exception as e:
            _ = e
            debug("resources.create: error during creating new resource !", _c="e")

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
            settings.update_blob("data/settings.json", json.dumps(data, indent=4))
        except Exception as e:
            debug(f"settings::push : {e} :", _c="e")
            return {}


def theme(tar, c=True):
    thm = (settings.pull("-theme") or "").lower().replace(" ", "")
    _c = ((settings.pull("themes-colors") or {}).get(thm) or {}).get(tar) or "#000000"
    if _c.startswith("#") and c:
        return QColor(_c)

    return _c


def load_from_project(key, root, def_=""):
    path = os.path.join(root, ".kvc")

    if os.path.exists(path):
        return toml.load(open(path, "r")).get(key)

    return def_
