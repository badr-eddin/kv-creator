import pathlib
import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import *


class GitMan(QWidget):
    ICON = "plugins/git/git.png"

    def __init__(self, main, **kwargs):
        super(GitMan, self).__init__(kwargs.get("editor"))
        self.editor: QTabWidget = kwargs.get("editor")
        self.main = main
        self.std = main.std
        self.widget = self.std.import_("plugins/git/git.ui")
        self.std.set_layout(self, QVBoxLayout).addWidget(self.widget)


CLASS = GitMan
VERSION = 0.1
TYPE = "window/editor"
NAME = "git"
