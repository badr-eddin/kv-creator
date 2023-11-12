import sys
import os
import traceback

from libs import Creator, QApplication, debug

os.environ["dev-env"] = "1"
os.environ["theme"] = "dark"


def excepts(exc_type, exc_value, exc_traceback):
    tb = traceback.extract_tb(exc_traceback)
    filename, line, func, text = tb[-1]
    filename = os.path.basename(filename)
    debug(f"[{filename}:{line}] {exc_value}", _c="e")


sys.excepthook = excepts
app = QApplication(sys.argv)
window = Creator(app=app)
# window = window.load(app)
sys.exit(app.exec())
