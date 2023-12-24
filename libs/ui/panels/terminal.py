from ...pyqt import QWidget, QVBoxLayout, QTimer, QProcess, QTabWidget
from ...utils import settings, set_layout, debug

import xdo


class Terminal(QWidget):
    tabs = None
    pid = 0
    tin = -1

    def __init__(self, main=None, console=None, **kwargs):
        super(Terminal, self).__init__(None)
        self.process = QProcess(self)
        self.main = main
        self.console = console
        self.callback = kwargs.get("callback")
        self.on_done = kwargs.get("on_done")
        self.command = kwargs.get("command")
        self.x = xdo.Xdo()
        self.resize_timer = QTimer(self)

        self.resize_timer.timeout.connect(self.resize_term)  # Type: ignore
        self.resize_timer.setSingleShot(True)
        self.args = [
                settings.pull("terminal/-embed"), 0,
                settings.pull("terminal/-font-name"), settings.pull("terminal/font-name"),
                settings.pull("terminal/-font-size"), str(settings.pull("terminal/font-size")),
                settings.pull("terminal/-bg-color"), settings.pull("terminal/bg-color"),
                "+bdc"
            ]

        if kwargs.get("wait"):
            self.command.extend([";", "echo -n \"exit >> \"", ";", "read"])

        if self.command:
            self.args.extend([settings.pull("terminal/-run"), " ".join(self.command)])

    def embed(self):
        self.args[1] = str(int(self.winId()))
        self.process.start(
            settings.pull("terminal/-provider"),
            self.args
        )
        self.resize_timer.start(500)
        self.process.started.connect(self.resize_term)
        self.process.finished.connect(self._process_done)  # Type: ignore

        if self.callback:
            self.callback(self)

    def _process_done(self, ec, es):
        if es == QProcess.ExitStatus.CrashExit:
            self.main.element("msg.pop")("The process crashed!", 3000)
        else:
            self.main.element("msg.pop")(f"The process finished with exit code {ec}.", 5000)

        parent = self.tabs
        if isinstance(parent, QTabWidget):
            parent.removeTab(parent.indexOf(self))

        terms: list = self.console.terminals

        if self in terms:
            terms.remove(self)

        if self.on_done:
            self.on_done(self.tin)

    def resizeEvent(self, event):
        self.resize_timer.start(200)

    def resize_term(self):
        try:
            self.pid = self.process.processId()

            if not self.pid:
                return

            width = self.width()
            height = self.height()
            pid = 0
            window_ids = self.x.search_windows(pid=self.pid)

            if window_ids:
                pid = window_ids[0] if type(window_ids[0]) is int else 0

            if pid:
                self.x.set_window_size(pid, width, height)

        except Exception as e:
            debug(f"resize-terminal: {e}", _c="e")
