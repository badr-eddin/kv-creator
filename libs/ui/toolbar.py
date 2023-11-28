import os.path

from .demo_kv_app import get_kivy_window_id
from ..utils import *


class Button(QPushButton):
    obj = {}

    def __init__(self, parent, on_click, bar):
        super(Button, self).__init__(parent)
        self.setFixedSize(QSize(30, 25))
        self.setIconSize(QSize(20, 20))
        self.setObjectName("bar-button")
        self.bar = bar
        self.on_click = on_click

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.clicked.connect(self._clicked)  # Type: ignore

    def _clicked(self):
        if hasattr(self.bar, self.on_click[0]):
            on_click = getattr(self.bar, self.on_click[0])
            args = self.on_click[1]
            if args:
                on_click(self, args)
            else:
                on_click(self)


class Bar:
    ui = "head"
    ui_type = QFrame

    def __init__(self, ui, main):
        self.ui = ui
        self.main = main
        self.buttons = settings.pull("-buttons")
        self.kv_app_running = False
        self.embed_wins = []
        self.timer = QTimer(main)
        self.layout = self.ui.layout()

        if not self.layout:
            self.layout = set_layout(self.ui, QHBoxLayout, (2, 2, 2, 2))

    def _close_app(self, _):
        self.main.close()

    def add_plugin(self, _):
        self.main.install_plugin()

    def search_(self, _):
        self.main.search_in(self.main.element("editor.widget").currentWidget())

    def no_app_running(self):
        self.kv_app_running = False

    def _run_app(self, _e):
        widget = self.main.element("editor.widget").currentWidget()

        if hasattr(widget, "lexer"):
            lexer = widget.lexer()

            if hasattr(lexer, "run"):
                debug(f"running ...")
                lexer.run(self.process_started)

            else:
                self.main.element("msg.pop")("action 'run' not supported !", 5000)

    def process_started(self, kv_file, process, kwargs):
        self.timer = QTimer(self.main)
        self.timer.timeout.connect(lambda: self._embed_kv_window(kv_file, process.processId(), kwargs))  # Type: ignore
        self.timer.start(500)

    def _embed_kv_window(self, kvf, pid, args):
        wid = get_kivy_window_id(pid)
        if not wid:
            return
        if wid in self.embed_wins:
            return

        self.embed_wins.append(wid)

        debug(f"embedding window 'pid={wid}' ...")
        self.timer.stop()
        func = self.main.element("editor.add_external_window")
        if func:
            func(wid, title=os.path.basename(kvf), path=kvf, pid=pid, kwargs=args)

    def _global_connector(self, _, args):
        func = self.main.element(args[0])
        if func:
            func(*args[1:])

    def initialize(self, _p=None):
        for _b in sorted(self.buttons.keys()):
            obj = self.buttons.get(_b)
            btn = Button(self.ui, obj.get("function"), self)
            # btn.setText(_b)
            btn.setIcon(QIcon(import_(obj.get("icon"))))
            btn.obj = obj
            self.layout.addWidget(btn)
        self.layout.addItem(QSpacerItem(5000, 25, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
