import pyperclip
from PyQt6.Qsci import QsciScintilla as _QSci

from .debugger import debug


class Handler:
    def __init__(self, main, editor):
        self.main = main
        self.editor = editor
        self.got = self.main.std.InLineInput(self.main, self.__goto, "line")

    def set_comment(self):
        if not isinstance(self.editor, _QSci):
            debug(f"set_comment: expected 'QsciScintilla' got '{type(self.editor).__name__}'", _c="e")
            return

        text = self.editor.text()
        lexer = self.editor.lexer()

        if not hasattr(lexer, "comment"):
            self.main.element("msg.pop")("comment not supported !")
            return

        pos = list(self.editor.getCursorPosition())
        if not self.editor.selectedText():
            lines = [pos[0]]
        else:
            start, _, end, _ = self.editor.getSelection()
            lines = list(range(start, end+1))

        new_text = lexer.comment(text, lines)
        self.editor.setText(new_text)

        self.editor.setCursorPosition(*pos)

    def goto(self):
        self.got.check(lambda k: k.isdigit() or not k)
        self.got.read_at(self.main.mapFromGlobal(self.main.cursor().pos()))

    def __goto(self, inp):
        editor: _QSci = self.main.element("editor.widget").currentWidget()

        editor.setCursorPosition(int(inp.text())-1, 0)
        editor.setFocus()
        inp.close()

    def undo(self):
        self.editor.SendScintilla(_QSci.SCI_UNDO)

    def redo(self):
        self.editor.SendScintilla(_QSci.SCI_REDO)

    def find(self):
        print("find")

    def cut(self):
        pyperclip.copy(self.editor.get_selected_text())
        self.editor.remove_selected_text()

    def copy(self):
        pyperclip.copy(self.editor.get_selected_text())

    def paste(self):
        if self.editor.is_selecting:
            self.editor.remove_selected_text()
        self.editor.insert(pyperclip.paste())

    def delete(self):
        self.editor.remove_selected_text()

    def select_all(self):
        self.editor.SendScintilla(_QSci.SCI_SELECTALL)
