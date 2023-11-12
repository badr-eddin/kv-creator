import re
import xdo

from ..utils import *


class Console(QDockWidget):
    ui = "head"
    ui_type = QFrame

    def __init__(self, parent, main):
        super(Console, self).__init__(parent)
        self.main = main
        self.lines = []
        self.terminals = []
        self.widget = loadUi(import_("ui/problems.ui"))
        self.problems: QTextBrowser = self.widget.problems
        self.tabs: QTabWidget = self.widget.tabs
        self.setVisible(False)

    def initialize(self, _p=None):
        self.main.dock_it(self, "ba")
        self.setWindowTitle("Problems And Output")
        self.setWidget(self.widget)
        self.problems.setStyleSheet("background: transparent; border: none; font-size: 15px;")
        self.problems.cursorPositionChanged.connect(self._cursor_moved)  # Type: ignore

    def _cursor_moved(self):
        pos = self.problems.textCursor().position()
        text = self.problems.toPlainText()

        for k in re.finditer(r"line\s+(?P<line>\d+)\s*", text):
            if pos+1 in range(k.start(), k.end()):
                current = self.main.buttons.get_obj("editor.widget").currentWidget()
                if hasattr(current, "editor"):
                    line = int(k.group("line"))-1
                    current.setCursorPosition(line, 0)
                    current.setFocus()
                    # current.setSelection(line, 0, line, len(current.text().splitlines()[line]))

    def _style(self, c, o="first"):
        s = "QTabBar::tab:%s{color: %s;}" % (o, c)
        self.widget.tabs.setStyleSheet(s)

    def report(self, msg: str):
        msg = f"<span style='color:#FF3333'>{msg}</span>"
        k = re.findall(r"line\s+\d+\s*", msg)
        if k:
            msg = msg.replace(k[0], f"<a style='text-decoration:underline'>{k[0]}</a>")

        self.problems.setText(msg.replace("\n", "<br>"))
        self._style("#FF3333")
        self.main.on("report_error", {"msg": msg})

    def done(self):
        self.problems.setText("<span style='color:#33FF33'>CLEAN</span>")
        self._style("white")

    def add_terminal(self, title=None, **kwargs):
        title = title if isinstance(title, str) else "Terminal"
        term = Terminal(self.tabs, self.main, self, **kwargs)
        term.tabs = self.tabs
        term.tin = self.tabs.addTab(term, title)
        self.tabs.setCurrentWidget(term)
        term.embed()
        self.setVisible(True)
        self.terminals.append(term)
        self.main.on("add_terminal", {"terminal": term})
        return term.process

    def final_main_close(self, *args):
        for term in self.terminals:
            term.process.kill()
            debug(f"process: '{term.pid}' is dead °^° .")


class Terminal(QWidget):
    tabs = None
    pid = 0
    tin = -1

    def __init__(self, parent=None, main=None, console=None, **kwargs):
        super(Terminal, self).__init__(parent)
        set_layout(self, QVBoxLayout)
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
                settings.pull("terminal/-embed"), str(int(self.winId())),
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
            self.main.buttons.get_obj("msg.pop")("The process crashed!", 3000)
        else:
            self.main.buttons.get_obj("msg.pop")(f"The process finished with exit code {ec}.", 5000)

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
