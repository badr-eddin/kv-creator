import keyword
import os
import pathlib
import re
import sys
import tempfile

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu
from flake8.api import legacy

from PyQt6.Qsci import QsciLexerPython, QsciAPIs, QsciScintilla as _Qsci
from jedi import Script


class PythonLexer(QsciLexerPython):
    FILES = [".py"]
    FUNCTIONS = ["on_editor_text_changed", "on_editor_tab_created", "on_tab_changed"]
    COMMENT = "#"

    def __init__(self, parent, main, std=None):
        super(PythonLexer, self).__init__(parent)
        std = std or main.std
        self.std = std
        self.main = main
        self.parent = parent
        self.api = None

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

    def config_auto_complete(self, words=keyword.kwlist):
        api = QsciAPIs(self)

        for i in words:
            api.add(i)

        for i in api.installedAPIFiles():
            api.load(i)

        api.prepare()

        self.parent.setAutoCompletionCaseSensitivity(False)
        self.parent.setAutoCompletionReplaceWord(True)
        self.parent.setAutoCompletionThreshold(1)
        self.parent.setAutoCompletionSource(self.parent.AutoCompletionSource.AcsAll)
        setattr(self.parent, "api", api)
        self.api = api
        self.parent.api = api

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
    def complete(code, line, column, path):
        ret_val = []
        try:
            script = Script(code, path=path)
            completions = script.complete(line + 1, column)
        except (RuntimeError, TypeError, AttributeError):
            completions = []

        for comp in completions:
            ret_val.append(f"{comp.name} ({comp.description})")

        return ret_val

    @staticmethod
    def on_editor_text_changed(kwargs):
        editor = kwargs.get("editor")

        if not editor:
            return

        if not isinstance(editor.lexer(), PythonLexer):
            return

        analyse = editor.main.std.settings.pull("user-prefs/code-analyse")
        complete = editor.main.std.settings.pull("user-prefs/autocomplete")
        menu: QMenu = editor.auto_m

        if hasattr(editor, "api"):
            words = PythonLexer.complete(editor.text(), *editor.getCursorPosition(), editor.path)
            editor.api.clear()

            for word in words:
                editor.api.add(word)
            editor.api.prepare()

            editor.lexer().setAPIs(editor.api)
            # editor.complete_with(words)

        else:
            menu.close()

        tmp = pathlib.Path(os.path.join(os.getenv("tmp"), "pytmp.py"))
        tmp.write_text(editor.text())

        if analyse:
            checker = legacy.get_style_guide(quiet=True)

            old_stdout = sys.stdout

            sys.stdout = open(os.devnull, 'w')

            vio = checker.input_file(tmp.as_posix())

            sys.stdout = old_stdout

            if not vio.total_errors:
                editor.main.buttons.get_obj("console.done")()
                return
 
            msg = vio.get_statistics("E")
            msg += vio.get_statistics("W")
            msg += vio.get_statistics("F")
            msg += vio.get_statistics("C")

            msg = "\n".join(msg)
            editor.main.buttons.get_obj("console.report")(msg)


CLASS = PythonLexer
VERSION = 0.1
TYPE = "editor/support"
NAME = "Python"
