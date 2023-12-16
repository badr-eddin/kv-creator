import os
import pathlib
import shutil
import sqlite3
import zipfile
import zlib

from cryptography.fernet import Fernet

PATH = "./src"
DB = "./db/resources.db"
IGNORED = ["plugins", "tmp"]
ENC = {"settings.json": "conf"}
KEY = b"mrqtXulGq-K3UwCN876qFDUuYafXBEApw0fzzhPUAXs="

db = sqlite3.connect(DB)
cursor = db.cursor()


def build_all():
    query = '''CREATE TABLE "resources" (
        "key" TEXT UNIQUE,
        "type" TEXT,
        "content" BLOB
    );'''
    cursor.execute(query)

    # *************************************

    for root, dirs, files in os.walk(PATH):
        dirs[:] = [d for d in dirs if d not in IGNORED]

        for file in files:
            path = os.path.join(root, file)
            path = pathlib.Path(path)
            key = path.as_posix().replace("src/", "")
            ext = os.path.basename(key).split(".")[-1]

            by = path.read_bytes()

            if file in ENC:
                fernet = Fernet(KEY)
                by = zlib.compress(fernet.encrypt(by))

                ext0 = ENC.get(file)
                key = key.replace(ext, ext0)
                ext = ext0

            cursor.execute(
                "INSERT INTO resources (key, type, content) VALUES (?, ?, ?)", (key, ext, by)
            )

    # *************************************


def zip_plugin(pl):
    m = os.path.join("src", "dst", pl + ".zip")
    if os.path.exists(m):
        os.remove(m)

    shutil.make_archive(
        os.path.join("src", "dst", pl),
        "zip",
        os.path.join("src", "plugins"),
        pl
    )


k = input("*| >>> ")

if k == "*":
    build_all()

elif k.startswith("@"):
    zip_plugin(k[1:])

db.commit()
db.close()

