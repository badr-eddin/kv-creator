from ...pyqt import QIcon, loadUi, QVBoxLayout, QKeyEvent, Qt
from ...utils import import_, set_layout, restore
from .dialog import Dialog


class InformUser(Dialog):
    ui = "$"
    name = "inform"

    ERROR = -1
    WARNING = 0
    INFO = 1

    def __init__(self, parent, main, i=False):
        super(InformUser, self).__init__(parent, main)
        self.main = main
        self.eno = None
        self.sts_icons = {
            -1: QIcon(import_("img/dialog/error.png")),
            0: QIcon(import_("img/dialog/warning.png")),
            1: QIcon(import_("img/dialog/info.png"))
        }
        self.widget = loadUi(import_("ui/ask-user.ui", 'io'))
        if i:
            self.initialize()

    def initialize(self, _p=None):
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.widget.cancel.clicked.connect(self.close)

    def no_cancel(self):
        self.widget.cancel.close()

    def closeEvent(self, a0):
        (self.eno or self.main).setEnabled(True)
        super(InformUser, self).closeEvent(a0)

    def inform(self, msg, title="Prompt", on_accept=None, on_deny=None, dis=None,
               res=None, sz=(300, 130), sts=4, args=None):
        self.widget.text.setText(msg)
        self.widget.title.setText(title.upper())

        if on_deny:
            self.widget.refuse.clicked.connect(lambda: on_deny(self, *(args or ())))
        else:
            self.widget.refuse.clicked.connect(self.close)

        if on_accept:
            self.widget.accept.clicked.connect(lambda: on_accept(self, *(args or ())))
        else:
            self.widget.accept.clicked.connect(self.close)

        self.eno = dis or self.main

        self.setParent(dis.parent() if dis else None)

        # self.eno.setEnabled(False)
        if self.sts_icons.get(sts):
            self.widget.icon.setIcon(self.sts_icons.get(sts))
        else:
            self.widget.icon.close()

        restore(self, *sz, sz=res)

        self.show_up(self.main)

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Y:
            self.widget.accept.click()

        if a0.key() == Qt.Key.Key_N:
            self.widget.refuse.click()

        if a0.key() == Qt.Key.Key_C:
            self.widget.cancel.click()
