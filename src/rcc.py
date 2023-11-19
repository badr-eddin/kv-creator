import os
import pathlib
import shutil
import sqlite3
import zipfile

PATH = "./src"
DB = "./db/resources.db"
IGNORED = ["plugins", "tmp"]


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

            cursor.execute(
                "INSERT INTO resources (key, type, content) VALUES (?, ?, ?)", (key, ext, path.read_bytes())
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

