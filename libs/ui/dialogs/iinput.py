from ...pyqt import QLineEdit, QAction, QPoint


class InLineInput(QLineEdit):
    def __init__(self, parent, callback=None, place_holder=None, args=None, mf=None):
        super(InLineInput, self).__init__(parent)
        self.callback = callback
        self.check_method = mf
        self.args = args
        action = QAction(self)
        action.triggered.connect(self.close)
        action.setShortcut("Esc")
        self.returnPressed.connect(self._enter)  # Type: ignore
        self.addAction(action)
        self.setStyleSheet("border: 1px solid #333")
        self.set_placeholder(place_holder)
        self.textChanged.connect(self._text_changed)  # Type: ignore
        self.close()

    def set_callback(self, fn):
        self.callback = fn

    def set_placeholder(self, tx):
        self.setPlaceholderText(tx or "")

    def set_args(self, args):
        self.args = args

    def check(self, m):
        self.check_method = m

    def _text_changed(self):
        k = self._check()
        if k or k == 8:
            self.setStyleSheet("color: white")
        else:
            self.setStyleSheet("color: red")

    def _check(self):
        if self.check_method:
            if callable(self.check_method):
                return self.check_method(self.text())
        return 8

    def done(self):
        self.clear()
        self.set_args(None)
        self.set_placeholder("")
        self.set_callback(None)
        self.close()

    def _enter(self):
        if self.callback and self._check():
            self.callback(self, *(self.args or ()))

    def read_at(self, pos):
        self.move(QPoint(pos.x() - 100, pos.y() + 18))
        self.show()
        self.raise_()
        self.setFocus()
