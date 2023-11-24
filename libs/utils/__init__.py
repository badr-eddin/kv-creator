from .resources_manager import read_file, import_, get_object_from_memory, get_db, duck
from .ui_customize import find_in, set_layout, bald, restore, set_shadow, scroller
from .debugger import debug
from .style import load_style
from .settman import settings, color, theme
from .keys_handler import Handler
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.uic import loadUi
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom, QsciAPIs, QsciLexer
from .plugin_loader import PLoader
from .buttons import Buttons
from .props_handler import pan
from .clipboard import Clipboard


def SPItem(sz=5000):
    return QSpacerItem(sz, 25, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def VSPItem(sz=5000):
    return QSpacerItem(25, sz, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
