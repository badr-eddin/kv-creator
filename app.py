import os
import sys
import traceback

os.environ['KIVY_NO_CONSOLELOG'] = '1'

from libs import Creator, QApplication, debug, get_db

# load-from-files if var == 1 else load-from-db
# os.environ["dev-env-loading"] = '1'

# load plugins as .py if var == 1 else '.so'
os.environ["dev-env"] = '1'

# if 'db' not found it will exit
get_db()


def excepts(_, exc_value, exc_traceback):
    """
    exception handling in order to improve debugging
    """
    if os.getenv("dev-env"):
        tb = traceback.extract_tb(exc_traceback)
        filename, line, func, text = tb[-1]
        filename = os.path.basename(filename)
        debug(f"[{filename}:{line}] {exc_value}", _c="e")


sys.excepthook = excepts

# create app
app = QApplication([])
window = Creator(app=app)
sys.exit(app.exec())
