from ...pyqt import QsciLexerCustom
from .theme import DefaultTheme


class DefaultLexer(QsciLexerCustom):
    def __init__(self, parent):
        super(DefaultLexer, self).__init__(parent)
        self.setDefaultPaper(DefaultTheme.background_c)
        self.setDefaultColor(DefaultTheme.foreground_c)

    def description(self, *_):
        return "Default Lexer"

    def styleText(self, start=0, end=0):
        pass
