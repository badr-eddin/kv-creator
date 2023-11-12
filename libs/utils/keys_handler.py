from PyQt6.Qsci import QsciScintilla as _QSci

from .debugger import debug


class Handler:
    def __init__(self, main):
        self.main = main
        self.got = self.main.std.InLineInput(self.main, self.__goto, "line")

    def set_comment(self):
        editor: _QSci = self.main.buttons.get_obj("editor.widget").currentWidget()

        if not isinstance(editor, _QSci):
            debug(f"set_comment: expected 'QsciScintilla' got '{type(editor).__name__}'", _c="e")
            return

        text = editor.text()
        lexer = editor.lexer()

        if not hasattr(lexer, "comment"):
            self.main.buttons.get_obj("msg.pop")("comment not supported !")
            return

        pos = list(editor.getCursorPosition())
        if not editor.selectedText():
            lines = [pos[0]]
        else:
            start, _, end, _ = editor.getSelection()
            lines = list(range(start, end+1))

        new_text = lexer.comment(text, lines)
        editor.setText(new_text)

        editor.setCursorPosition(*pos)

    def goto(self):
        self.got.check(lambda k: k.isdigit() or not k)
        self.got.read_at(self.main.mapFromGlobal(self.main.cursor().pos()))

    def __goto(self, inp):
        editor: _QSci = self.main.buttons.get_obj("editor.widget").currentWidget()

        editor.setCursorPosition(int(inp.text())-1, 0)
        editor.setFocus()
        inp.close()
