from ..pyqt import QThread, pyqtSignal
from ..utils import debug

from kivy.lang import Parser


class KivyParser(QThread):
    on_error = pyqtSignal(object, list)
    on_finish = pyqtSignal(object, object)

    def __init__(self, parent, text="", path="", arg=None):
        super(KivyParser, self).__init__(parent)
        self.path = path
        self.text = text
        self.arg = arg

    def run(self):
        try:
            parsed = Parser(content=self.text, filename=self.path)

            if self.arg:
                self.on_finish.emit(parsed, self.arg)
            else:
                self.on_finish.emit(parsed)

        except Exception as e:
            if hasattr(e, 'msg'):
                debug(f"thread::parse : {e.msg}", _c="e")

            self.on_error.emit(self.arg, [
                {
                    "type": "error",
                    "message": getattr(e, "msg", str(e).replace("\n", " ")),
                    "line": getattr(e, "lineno", 0) + 1,
                    "endLine": getattr(e, "lineno", 0) + 1,
                    "column": 0,
                    "endColumn": len(self.text.splitlines(False)[getattr(e, "lineno", 0)])
                }
            ])

        self.finished.emit()

    def trigger(self, text, path, arg=None):
        self.text = text
        self.path = path

        if arg:
            self.arg = arg

        if self.isRunning():
            self.terminate()
            self.wait()

        self.run()
