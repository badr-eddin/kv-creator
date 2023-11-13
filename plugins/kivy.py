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
        self.props = list((std.settings.pull("kivy/properties") or {}).keys())
        self.classes = std.settings.pull("kivy/classes")
        self.keywords = std.settings.pull("kivy/keywords")

        self.setColor(std.color("foreground"), self.styles.get("default"))
        self.setColor(std.color("c4"), self.styles.get("class"))
        self.setColor(std.color("c1"), self.styles.get("prop"))
        self.setColor(std.color("c3"), self.styles.get("string"))
        self.setColor(std.color("Error"), self.styles.get("error"))
        self.setColor(std.color("c1"), self.styles.get("escape"))
        self.setColor(std.color("Comment"), self.styles.get("comment"))
        self.setColor(std.color("c2"), self.styles.get("keywords"))
        self.setColor(std.color("c7"), self.styles.get("digit"))
        self.setColor(std.color("c6"), self.styles.get("alias"))
        self.setPaper(std.color("c6"), 10)
        self.setColor(std.color("Error"), 10)

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

    def _style_it(self, group_name, style_name, valid_tokens: int | list | tuple | str, pattern, text):
        iterator = pattern.finditer(text)
        for match_ in iterator:
            token_ = match_.group(group_name)
            self.startStyling(match_.start(group_name))
            if valid_tokens == -1 or token_ in valid_tokens:
                self.setStyling(len(token_), self.styles.get(style_name))
            else:
                self.setStyling(len(token_), self.styles.get("default"))

    def _style_classes_and_props(self, text):
        classes_pattern = re.compile(r"^\s*(?P<class>\w+)\s*:\s*(?=\s*$)",
                                     flags=re.MULTILINE | re.UNICODE)
        props_pattern = re.compile(r"^\s*(?P<property>\w+)\s*:(?P<value>.+?)(?=\s*(?:\w+\s*:\s*|$))",
                                   flags=re.MULTILINE | re.UNICODE)

        self._style_it("property", "prop", self.props, props_pattern, text)
        self._style_it("class", "class", self.classes, classes_pattern, text)

    def _style_keywords(self, text):
        aliases_pattern = re.compile(
            r"^#:(?P<import>import)\s+(?P<alias>\w+)\s+(?P<src>[.\w'\"]+)\s*$|"
            r"^#:(?P<set>set)\s+(?P<var>\w+)\s+(?P<value>['\"]*(.*?)['\"]*)\s*$",
            re.MULTILINE | re.UNICODE)

        aliases = []
        iterator = aliases_pattern.finditer(text)
        for al in iterator:
            aliases.append(al.group("alias") or al.group("var"))

        aliases.extend(self.keywords)

        keywords_pattern = "|".join(re.escape(keyword) for keyword in aliases)

        keyw_value_pattern = re.compile(
            r"^\s*\w+\s*:(?P<line_content>.+)$",
            re.MULTILINE
        )
        keyword_pattern = re.compile(
            r"\b(?P<keyword>" + keywords_pattern + r")\b"
        )

        for match in keyw_value_pattern.finditer(text):
            line_content = match.group("line_content")
            start_position = match.start("line_content")
            self.startStyling(start_position)
            self.setStyling(len(line_content), self.styles.get("default"))
            for kw_match in keyword_pattern.finditer(line_content):
                self.startStyling(start_position + kw_match.start("keyword"))
                if kw_match.group("keyword") in aliases:
                    self.setStyling(len(kw_match.group("keyword")), self.styles.get("keywords"))

    def _style_digits(self, text):
        digit_pattern = re.compile(r"(?<![a-zA-Z0-9_.])(?P<float>[+-]?(\d+\.\d*|\.\d+))(?![a-zA-Z0-9_])|"
                                   r"(?<![a-zA-Z0-9_.])(?P<int>[+-]?\d+)(?![a-zA-Z0-9_])", re.MULTILINE | re.UNICODE)
        for dgt in digit_pattern.finditer(text):
            group = "int" if dgt.group("int") else "float"
            self.startStyling(dgt.start(group))
            self.setStyling(len(dgt.group(group)), self.styles.get("digit"))

    def _style_comments_and_imports(self, text):
        # Comments
        comments_pattern = re.compile(r"#\s*.*?$", re.MULTILINE | re.UNICODE)
        for cmt in comments_pattern.finditer(text):
            self.startStyling(cmt.start())
            self.setStyling(len(cmt.group(0)), self.styles.get("comment"))

        # Imports and variables
        ims_pattern = re.compile(
            r"\s*#\s*:\s*(?P<import>import)\s+(?P<alias>\w+)\s+(?P<src>[.\w'\"]+)\s*$|"
            r"\s*#\s*:\s*(?P<set>set)\s+(?P<var>\w+)\s+(?P<value>['\"]*(.*?)['\"]*)\s*$",
            re.MULTILINE | re.UNICODE)

        for cmt in ims_pattern.finditer(text):
            group = "import" if cmt.group("import") else "set"

            self.startStyling(cmt.start(group))
            self.setStyling(len(cmt.group(group)), self.styles.get("keywords"))

            cnd_grp = "alias" if group == "import" else "var"

            self.startStyling(cmt.start(cnd_grp))
            self.setStyling(len(cmt.group(cnd_grp)), self.styles.get("alias"))

            self.aliases.append(cmt.group(cnd_grp))

            if group == "import":
                self.startStyling(cmt.start("src"))
                self.setStyling(len(cmt.group("src")), self.styles.get("string"))
            else:
                value = cmt.group("value")
                self.startStyling(cmt.start("value"))

                if value.isdigit():
                    self.setStyling(len(value), self.styles.get("digit"))

                elif value in self.std.settings.pull("kivy/keywords"):
                    self.setStyling(len(value), self.styles.get("keywords"))

                else:
                    if re.match(r"'.*?'\s*$|\".*?\"\s*$", value, re.MULTILINE | re.UNICODE):
                        self.setStyling(len(value or ""), self.styles.get("string"))
                    else:
                        self.setStyling(len(value or ""), self.styles.get("error"))

        kvv_pattern = re.compile(r"\s*#\s*:\s*(?P<kivy>kivy)\s+(?P<version>.*)$", re.MULTILINE | re.UNICODE)

        for v in kvv_pattern.finditer(text):
            self.startStyling(v.start("kivy"))
            self.setStyling(len(v.group("kivy")), self.styles.get("keywords"))

            self.startStyling(v.start("version"))
            version = v.group("version")

            if version[-1] not in string.digits or not re.match(r"\d+\.*\d*\.*\d*\s*", version):
                self.setStyling(len(version), self.styles.get("error"))
            else:
                self.setStyling(len(version), self.styles.get("digit"))

        self.editor().update()

    def _style_quote(self, text):
        line_pattern = re.compile(r'^\s*\w+\s*:\s*.*?(?=\n|$)', re.MULTILINE | re.UNICODE)
        line_matches = line_pattern.finditer(text)

        for line_match in line_matches:
            line = line_match.group(0)
            quote_matches = re.finditer(r'".*?[^\\]"' + r"|'.*?[^\\]'", line)
            for quote_match in quote_matches:
                absolute_start = line_match.start() + quote_match.start()
                co = quote_match.group()
                self.startStyling(absolute_start)
                self.setStyling(len(co), self.styles["string"])

            # Capture escaped quotes and apply "esc" style
            escapable = ['\\', '\'', '"', 'a', 'b', 'f', 'n', 'r', 't', 'v']
            escaped_quote_matches = re.finditer(r'\\.', line)
            for esc_match in escaped_quote_matches:
                if esc_match.group()[1] in escapable:
                    absolute_start = line_match.start() + esc_match.start()
                    self.startStyling(absolute_start)
                    self.setStyling(2, self.styles["escape"])

    def description(self, *_):
        return "KivyLexer"

    def styleText(self, start, end):
        path = getattr(self.editor(), "path")
        self.startStyling(start)

        if not path or str(path).endswith(".kv"):
            text = self.editor().text()
            self._style_keywords(text)

            self._style_digits(text)

            self._style_classes_and_props(text)

            self._style_quote(text)

            self._style_comments_and_imports(text)

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

        run = self.main.buttons.get_obj("console.add_terminal")
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
