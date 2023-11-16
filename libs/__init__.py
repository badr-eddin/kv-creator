import os

os.environ['KIVY_NO_CONSOLELOG'] = '1'

from .db import init_resources, resources
from .main import Creator
from .utils import QApplication, load_style, debug

