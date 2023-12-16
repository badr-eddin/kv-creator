from ..pyqt import QPushButton, QSize, QIcon
from ..utils import templates, import_


class AddonsItem(QPushButton):
    name = ""

    def __init__(self, parent=None, text="", on_click=None, icon=None, editor=None):
        super(AddonsItem, self).__init__(parent)
        self.setText("")
        self.setToolTip(text)
        self.name = text
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet("background: transparent; border: none")
        self.setIcon(icon)
        self.on_click = on_click

        if editor:
            editor.name = text

        self.editor = editor

        self.clicked.connect(self.__tr)  # Type: ignore

    def __tr(self):
        if self.on_click:
            self.on_click(self)


class Addons:
    @staticmethod
    def load(addons, widget, callback):
        for editor in addons:
            editor: templates.Plugin

            item = AddonsItem(
                None, editor.NAME, callback, QIcon(import_(editor.CLASS.ICON)), editor.CLASS
            )
            widget.layout().addWidget(item)
