from .terminal import Terminal
from ..dialogs import CustomDockWidget
from ...pyqt import QFrame, QIcon, QTabWidget, loadUi, QTreeWidget, QTreeWidgetItem, QsciScintilla, QPushButton
from ...utils import import_, debug, duck


class Console(CustomDockWidget):
    ui = "head"
    ui_type = QFrame

    def __init__(self, parent, main):
        super(Console, self).__init__(parent)
        self.main = main
        self.lines = {}
        self.icons = {
            "warning": QIcon(import_("img/editors/console/warning.png")),
            "refactor": QIcon(import_("img/editors/console/refactor.png")),
            "convention": QIcon(import_("img/editors/console/convention.png")),
            "fatal": QIcon(import_("img/editors/console/fatal.png")),
            "error": QIcon(import_("img/editors/console/error.png")),
        }
        self.terminals = []
        self.widget = loadUi(import_("ui/problems.ui", 'io'))
        self.tabs: QTabWidget = self.widget.tabs
        self.problems: QTreeWidget = self.widget.problems
        self.setVisible(False)

    def initialize(self, _p=None):
        self.main.dock_it(self, "ba")
        self.setWindowTitle("Problems And Outputs")
        self.setWidget(self.widget)
        self.problems.itemDoubleClicked.connect(self._item_double_clicked)

    def underline(self, m):
        message = duck(m)

        if message.type == "warning":
            x = "WARNING_INDICATOR"

        elif message.type == "error":
            x = "ERROR_INDICATOR"

        else:
            x = "DEFAULT_INDICATOR"

        x = self.main.element("editor.editor")(x)

        if not x:
            return

        self.main.element("editor.point_under")(
            message.line - 1, message.column,
            (message.endLine or message.line) - 1, message.endColumn or message.column, x
        )

    def report(self, messages: list):
        self.done()

        msg = {}
        msg_ = []

        # classify depend on object
        for message in messages:
            if message.get("obj"):
                if message.get("obj") not in msg:
                    msg[message.get("obj")] = []

                msg[message.get("obj")].append(message)
            else:
                msg_.append(message)

        for message in msg:
            message_obj = msg.get(message)

            parent = QTreeWidgetItem()
            parent.setText(0, message)
            parent.setIcon(0, QIcon(import_("img/editors/console/object.png")))

            for m in message_obj:
                item = QTreeWidgetItem()

                item.setText(0, m.get("message") + " :" + str(m.get('line')))
                item.setIcon(0, self.icons.get(m.get("type")) or QIcon())
                self.lines.update({id(item): m})
                parent.addChild(item)
                self.underline(m)

            self.problems.addTopLevelItem(parent)

        for message in msg_:
            item = QTreeWidgetItem()
            item.setText(0, message.get("message") + " :" + str(message.get('line')))
            item.setIcon(0, self.icons.get(message.get("type")) or QIcon())

            self.lines.update({id(item): message})
            self.underline(message)
            self.problems.addTopLevelItem(item)

        self.main.on("report_error", {"msg": messages})
        self.problems.expandAll()

    def _item_double_clicked(self, item):
        msg = self.lines.get(id(item))
        if not msg:
            return

        editor = self.main.element("editor.widget").currentWidget()

        if not isinstance(editor, QsciScintilla):
            return

        line = msg.get("line") - 1
        index = msg.get("column")

        editor.setFocus()
        editor.setCursorPosition(max(line or 0, 0), index or 0)

    def done(self):
        self.lines.clear()
        self.problems.clear()

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

    def final_main_close(self, *_):
        for term in self.terminals:
            term.process.kill()
            debug(f"process: '{term.pid}' is dead °-° .")
