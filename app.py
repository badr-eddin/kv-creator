import os
import sys
import traceback

from libs import Creator, QApplication, debug, get_db


# os.environ["dev-env-loading"] = '1'
os.environ["dev-env"] = '1'


get_db()


def excepts(_, exc_value, exc_traceback):
    tb = traceback.extract_tb(exc_traceback)
    filename, line, func, text = tb[-1]
    filename = os.path.basename(filename)
    debug(f"[{filename}:{line}] {exc_value}", _c="e")


sys.excepthook = excepts


app = QApplication([])
window = Creator(app=app)
sys.exit(app.exec())
