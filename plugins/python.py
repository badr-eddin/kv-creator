import json
import os
import pathlib
import re
import sys
import tempfile
from io import StringIO

import autopep8
from PyQt6.Qsci import QsciLexerPython, QsciAPIs, QsciScintilla as _Qsci
from PyQt6.QtCore import QThread
from jedi import Script
from pylint import lint


class _PythonAutoCompleter(QThread):
    def __init__(self, file_path, api):
        super(_PythonAutoCompleter, self).__init__(None)
        self.file_path = file_path
        self.script = None
        self.api: QsciAPIs = api
        self.completions = None

        self.line = 0
        self.index = 0
        self.text = ""

    def run(self):
        try:
            self.script = Script(self.text, path=self.file_path)
            self.completions = self.script.complete(self.line, self.index)
            self.load_autocomplete(self.completions)
        except Exception as err:
            _ = err

        self.finished.emit()

    def load_autocomplete(self, completions):
        self.api.clear()
        [self.api.add(i.name) for i in completions]
        self.api.prepare()

    def get_completions(self, line: int, index: int, text: str):
        self.line = line
        self.index = index
        self.text = text
        self.start()


class _PythonAnalyzer(QThread):
    def __init__(self, code, path, main):
        super(_PythonAnalyzer, self).__init__(None)
        self.text = ""
        self.main = main
        self.path = pathlib.Path("")
        self.__callback = None

        self.save(code, path)

    def save(self, text, path):
        tmp = pathlib.Path(os.path.join(os.getenv("tmp"), os.path.basename(path)))
        if tmp.exists():
            os.remove(tmp)

        self.path = tmp
        self.text = text

        with open(tmp, "w") as f:
            f.write(text)

    def run(self):
        try:
            if self.path.exists():

                # override stdout in order to catch the output
                stdout = sys.stdout
                sys.stdout = StringIO()

                lint.Run([self.path.as_posix(), '--output-format', "json"], exit=False)
                inspections = sys.stdout.getvalue()
                sys.stdout.close()
                sys.stdout = stdout

                inspections = json.loads(inspections)

                if self.__callback:
                    self.__callback(inspections)

                self.parse_and_report(inspections)
                self.finished.emit()
        except Exception as e:
            self.main.std.debug(f"analyze: {e}")

    def parse_and_report(self, jss):
        self.main.buttons.get_obj("console.report")(jss)

    def set_callback(self, cb):
        if not callable(cb):
            self.main.std.debug(f"callback ({cb}) is not callable", _c="e")
            return

        self.__callback = cb

    def inspect(self, code, path, cb=None):
        self.save(code, path)
        self.set_callback(cb)
        self.run()


class PythonLexer(QsciLexerPython):
    FILES = [".py"]
    FUNCTIONS = ["on_editor_text_changed", "on_editor_tab_created", "on_tab_changed", "on_cursor_moved",
                 "on_asked_for_completion"]
    ACTIONS = {
        "@type": "lexer",
        "$refactor": "refactor_code@plugins/python/fix.png",
        "$comment": "comment@plugins/python/comment.png",
        "$run": "run@plugins/python/run.png"
    }
    COMMENT = "#"

    auto_completer = None
    analyzer = None

    def __init__(self, parent, main, std=None):
        super(PythonLexer, self).__init__(parent)
        std = std or main.std
        self.std = std
        self.main = main
        self.parent = parent
        self.api = None
        self.analyzer = _PythonAnalyzer(parent.text(), parent.path, self.main)

        self.setDefaultPaper(std.theme("background_c"))
        self.setDefaultColor(std.theme("foreground_c"))

        self.setColor(std.color("Foreground"), self.Default)
        self.setColor(std.color("Error"), self.UnclosedString)
        self.setColor(std.color("Comment"), self.Comment)
        self.setColor(std.color("C6"), self.Operator)
        self.setColor(std.color("Foreground"), self.Operator)
        self.setColor(std.color("Foreground"), self.Identifier)
        self.setColor(std.color("C4"), self.HighlightedIdentifier)
        self.setColor(std.color("C4"), self.ClassName)
        self.setColor(std.color("C6"), self.TripleDoubleQuotedString)
        self.setColor(std.color("C2"), self.Decorator)
        self.setColor(std.color("C2"), self.CommentBlock)
        self.setColor(std.color("C4"), self.FunctionMethodName)
        self.setColor(std.color("C1"), self.Keyword)
        self.setColor(std.color("C7"), self.Number)
        self.setColor(std.color("C3"), self.TripleSingleQuotedString)
        self.setColor(std.color("C3"), self.DoubleQuotedString)
        self.setColor(std.color("C3"), self.SingleQuotedString)
        self.setColor(std.color("C3"), self.SingleQuotedFString)
        self.setColor(std.color("C3"), self.DoubleQuotedFString)
        self.setColor(std.color("C3"), self.TripleDoubleQuotedString)
        self.setColor(std.color("Error"), self.UnclosedString)

        self.setPaper(std.color("Transparent"), self.UnclosedString)

        self.setFoldComments(True)
        self.setFoldComments(True)
        self.setFoldCompact(True)

    def config_auto_complete(self, *_):
        self.api = QsciAPIs(self)

        self.auto_completer = _PythonAutoCompleter(self.parent.path, self.api)

        self.parent.setAutoCompletionCaseSensitivity(False)
        self.parent.setAutoCompletionReplaceWord(True)
        self.parent.setAutoCompletionThreshold(1)
        self.parent.setAutoCompletionSource(self.parent.AutoCompletionSource.AcsAPIs)

    def run(self, callback=None):
        path = getattr(self.editor(), "path")
        s_path = os.path.join(self.main.tmp, os.path.basename(tempfile.mktemp()) + ".py")

        if not path:
            path = s_path

        if not os.path.exists(str(path)):
            path = s_path
            with open(path, "w") as file:
                file.write(self.editor().text())

        run = self.main.buttons.get_obj("console.add_terminal")
        python = self.std.settings.pull("execution/python-interpreter")

        proc = run(os.path.basename(path), command=[python, path], wait=True)

    def comment(self, text="", lines=None):
        if not text:
            return

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

    def refactor_code(self):
        code = self.parent.text()

        self.parent.clear()
        self.parent.setText(autopep8.fix_code(code))

    @staticmethod
    def on_asked_for_completion(kwargs):
        kwargs = kwargs or {}
        kwargs.update({"ignore_analyze": True})
        PythonLexer.reload(kwargs)

    @staticmethod
    def on_cursor_moved(kwargs):
        kwargs = kwargs or {}
        kwargs.update({"ignore_analyze": True})
        PythonLexer.reload(kwargs)

    @staticmethod
    def on_tab_changed(kwargs):
        PythonLexer.reload(kwargs)

    @staticmethod
    def on_editor_tab_created(kwargs):
        PythonLexer.reload(kwargs)

    @staticmethod
    def reload(kwargs):
        editor = kwargs.get("editor")

        if isinstance(editor, _Qsci):
            PythonLexer.on_editor_text_changed(kwargs)

    @staticmethod
    def complete(code, line, column, comp: _PythonAutoCompleter | None):
        if comp:
            comp.get_completions(line, column, code)

    @staticmethod
    def on_editor_text_changed(kwargs):
        if not kwargs:
            return

        editor = kwargs.get("editor")

        if not editor:
            return

        self: PythonLexer = editor.lexer()

        if not isinstance(self, PythonLexer):
            return

        analyse = editor.main.std.settings.pull("user-prefs/code-analyse")
        complete = editor.main.std.settings.pull("user-prefs/autocomplete")

        if analyse and not kwargs.get("ignore_analyze"):
            self.analyzer.inspect(editor.text(), editor.path)

        if complete:
            if hasattr(self, "auto_completer"):
                pos = editor.getCursorPosition()
                auto: _PythonAutoCompleter = getattr(self, "auto_completer")
                PythonLexer.complete(
                    editor.text(), pos[0]+1, pos[1], auto
                )


CLASS = PythonLexer
VERSION = 0.1
TYPE = "editor/support"
NAME = "Python"
