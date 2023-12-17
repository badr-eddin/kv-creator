import keyword
import os.path
import re
import string
import tempfile

from PyQt6.Qsci import QsciLexerCustom, QsciAPIs
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QTabWidget

KV_APP = """
import os
import re
import threading
# os.environ['KIVY_NO_CONSOLELOG'] = '0'
from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


Config.set('input', 'mouse', 'mouse,multi''touch_on_demand')


class TxtFileHandler(FileSystemEventHandler):
    on_file_modified = None

    def __init__(self, filename):
        self.filename = filename

    def on_modified(self, event):
        if self.on_file_modified:
            Clock.schedule_once(self.on_file_modified, 1/100)

class KvApp(App):
    title = "KivyApp"
    
    def __init__(self, **kwargs):
        super(KvApp, self).__init__(**kwargs)
        self.file = "$FILE"
        self.f_root, self.f_name = os.path.split(self.file)
        self.event_handler = TxtFileHandler(self.f_name)
        self.observer = Observer()
        self.toggle_wdog()

    def build(self):
        return Builder.load_file(self.file)

    def toggle_wdog(self):
        m = self.observer.is_alive()
        if not m:
            threading.Thread(target=self._threaded_watcher).start()
        else:
            self.observer.stop()
            self.observer.join()

    def _threaded_watcher(self):
        self.event_handler.on_file_modified = self._kv_modified_hook
        self.observer.schedule(self.event_handler, self.f_root, recursive=True)
        self.observer.start()

    def _kv_modified_hook(self, *_):
        self.root.clear_widgets()
        Builder.unload_file(self.file)
        self.root = self.build()
        self.run()

    def on_stop(self):
        self.toggle_wdog()


if __name__ == "__main__":
    app = KvApp()
    app.run()
"""


class _settings:
    string = False
    comment = False

    class FLAGS:
        dead = None
        kill = 2


class KivyLexer(QsciLexerCustom):
    styles = {
        'default': 0,
        'class': 1,
        'prop': 2,
        'string': 3,
        'error': 4,
        "escape": 5,
        "comment": 6,
        "keywords": 7,
        "digit": 8,
        "alias": 9
    }

    FILES = [".kv"]
    COMMENT = "#"

    class CONFIG:
        string = False
        comment = False
        custom_class = False
        alais = False
        error = False
        escape = False

        def reset(self):
            self.string = False
            self.comment = False
            self.custom_class = False
            self.alais = False
            self.error = False
            self.escape = False

    def __init__(self, parent, main, std=None):
        super(KivyLexer, self).__init__(parent)
        std = std or main.std
        self.std = std
        self.main = main
        self.factor = 0
        self.settings = _settings
        self.parent = parent
        self.aliases = []
        self.errors = []
        self.config = self.CONFIG()
        self.props = list((std.settings.pull("kivy/properties") or {}).keys())
        self.props += list((std.settings.pull("kivy/actions") or {}).keys())
        self.classes = std.settings.pull("kivy/classes")
        self.keywords = std.settings.pull("kivy/keywords")
        self.escapable_chars = std.settings.pull("kivy/escapable-chars")

        styles = std.duck(self.styles)

        self.setColor(std.color("foreground"), styles.default)
        self.setColor(std.color("c4"), styles.class_)
        self.setColor(std.color("c1"), styles.prop)
        self.setColor(std.color("c3"), styles.string)
        self.setColor(std.color("Error"), styles.error)
        self.setColor(std.color("c1"), styles.escape)
        self.setColor(std.color("Comment"), styles.comment)
        self.setColor(std.color("c2"), styles.keywords)
        self.setColor(std.color("c7"), styles.digit)
        self.setColor(std.color("c6"), styles.alias)
        self.setPaper(std.color("c6"), 10)
        self.setColor(std.color("Error"), 10)

        self.setDefaultPaper(std.color("background"))
        self.setDefaultColor(std.color("foreground"))
        self.setPaper(std.color("background"))

    def config_auto_complete(self):
        api = QsciAPIs(self)

        words = self.keywords + self.props + self.classes

        for i in words:
            api.add(i)

        api.prepare()
        self.parent.setAutoCompletionCaseSensitivity(False)
        self.parent.setAutoCompletionReplaceWord(True)
        self.parent.setAutoCompletionThreshold(1)
        self.parent.setAutoCompletionSource(self.parent.AutoCompletionSource.AcsAll)
        self.parent.setLexer(self)

    def description(self, *_):
        return "KivyLexer"

    def styleText(self, start, end):
        self.startStyling(start)

        txt = self.editor().text()
        text = txt[start:end]

        p = re.compile(r"(\{\.|\.\}|\#|\'\'\'|\"\"\"|\n|\s+|\w+|\W)")
        token_list = [(token, len(bytearray(token, "utf-8"))) for token in p.findall(text)]

        self.config.reset()

        for i, token in enumerate(token_list):
            # --------------------------------

            next1 = ''

            if i + 1 < len(token_list):
                next1 = token_list[i + 1][0]

            # --------------------------------
            if self.config.escape:
                self.setStyling(1, self.styles.get(str(self.config.escape)))
                self.setStyling(token[1] - 1, self.styles.get("string"))
                self.config.escape = False

            elif self.config.error:
                self.setStyling(token[1], self.styles.get("error"))

            elif self.config.string:

                if self.config.string == token[0] or re.match(r"\s*\n$", token[0]):
                    self.config.string = False

                if token[0] == "\\":

                    if next1[0] in self.escapable_chars:
                        x = "escape"
                    else:
                        x = "comment"

                    self.config.escape = x

                    self.setStyling(1, self.styles.get(x))
                else:
                    self.setStyling(token[1], self.styles.get("string"))

            elif self.config.custom_class:
                if token[0] == "@":
                    self.config.custom_class = "class"
                    self.setStyling(token[1], self.styles.get("default"))

                elif re.match(r"\s*>$", token[0]):
                    self.config.custom_class = False
                    self.setStyling(token[1], self.styles.get("default"))

                else:
                    x = self.config.custom_class
                    self.setStyling(
                        token[1],
                        self.styles.get(
                            (x if type(x) is str else "alias") if token[0] in self.classes else "alias"
                        ))

            elif self.config.comment:
                self.setStyling(token[1], self.styles.get("comment"))
                if re.match(r"\s*\n$", token[0]):
                    self.config.comment = False

            else:
                if token[0] in self.classes:
                    self.setStyling(token[1], self.styles.get("class"))

                elif token[0] == "<":
                    self.config.custom_class = True
                    self.setStyling(token[1], self.styles.get("default"))

                elif token[0] in self.keywords:
                    self.setStyling(token[1], self.styles.get("keywords"))

                elif token[0] in self.props:
                    self.setStyling(token[1], self.styles.get("prop"))

                elif token[0].isdigit():
                    self.setStyling(token[1], self.styles.get("digit"))

                elif token[0] in ['"', "'"]:
                    self.config.string = token[0]

                    self.setStyling(token[1], self.styles.get("string"))

                elif token[0] == "#":
                    if token_list[i + 1][0] == ":":
                        if token_list[i + 2][0] in ["set", "import", "include"]:
                            self.setStyling(token[1], self.styles.get("default"))
                            self.config.alias = token_list[i + 2][0]
                        else:
                            self.setStyling(token[1], self.styles.get("comment"))
                            self.config.comment = True
                    else:
                        self.config.comment = True
                        self.setStyling(token[1], self.styles.get("comment"))

                else:
                    self.setStyling(token[1], self.styles.get("default"))

    def run(self, callback=None):
        path = getattr(self.editor(), "path")
        s_path = os.path.join(self.main.tmp, os.path.basename(tempfile.mktemp()) + ".kv")
        sp_path = os.path.join(self.main.tmp, os.path.basename(tempfile.mktemp()) + ".py")

        if not path:
            path = s_path

        if not os.path.exists(str(path)):
            path = s_path
            with open(path, "w") as file:
                file.write(self.editor().text())

        run = self.main.element("console.add_terminal")
        python = self.std.settings.pull("execution/python-interpreter")

        kvt = KV_APP.replace("$FILE", path)

        with open(sp_path, "w") as file:
            file.write(kvt)

        proc = run(
            os.path.basename(path),
            command=[python, sp_path],
            wait=True,
            on_done=self._close_attached_tab
        )

        if callback and self.std.settings.pull("user-prefs/embed-kivy"):
            callback(path, proc, {"editor": self.editor()})

    def _close_attached_tab(self, tin):
        tabs: QTabWidget = self.parent.tabs
        tabs.removeTab(tin)

    def comment(self, text, lines):
        text_s = text.splitlines(False)
        pattern = re.compile(rf"^(?P<indentation>\s*)({self.COMMENT}\s)(?P<line>\s*.*?)$")

        for i in lines:
            match = pattern.match(text_s[i])
            if match:
                # uncomment
                text_s[i] = match.group("indentation") + match.group("line")
            else:
                # comment
                text_s[i] = self.COMMENT + " " + text_s[i]

        return "\n".join(text_s)

    def error(self, exp):
        num_line = -1

        if hasattr(exp, "line"):
            num_line = exp.line
        else:
            snl = re.findall(r"line\s*(\d+)", str(exp))
            if snl:
                snl = snl[0]

                if snl.isdigit():
                    num_line = max(0, int(snl) - 1)

        if num_line < 0:
            return

        line = self.editor().text().splitlines(False)[num_line]
        beg = re.findall(r"^(\s*)\w+", line)  # ignore underlining indentation
        beg = len(beg[0]) if beg else 0
        end = len(line)

        error_at = (num_line, beg, num_line, end, 0)

        if error_at not in self.errors:
            self.errors.append(error_at)

            getattr(self.editor(), "point_under")(*error_at)

    def clear_errors(self):
        for error in self.errors:
            getattr(self.editor(), "unpoint")(*error)
            self.errors.remove(error)

    def select(self, beg, end):
        self.startStyling(beg)
        self.setStyling(end - beg, 10)


CLASS = KivyLexer
VERSION = 0.1
TYPE = "editor/support"
NAME = "kivy"
