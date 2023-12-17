from . import standard
from ...pyqt import QWidget


class Addons:
    ICON: str


class Plugin:
    CLASS: object | Addons
    VERSION: int
    TYPE: str
    NAME: str


class Editor:
    ui: str
    ui_type: QWidget
    name: str

    def __init__(self, parent, main):
        self.main = main
        self.widget: QWidget

    def initialize(self, parent=None):
        """
        initialize the editor, call 'self.main.dock_it(obj, area)'
            obj: self
            area: choice(["la", "ra", "ba"])
        ! not obligatory to start from here
        """

