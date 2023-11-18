import os
import pathlib
import sqlite3


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


k = input("*| >>> ")

if k == "*":
    build_all()

db.commit()
db.close()

