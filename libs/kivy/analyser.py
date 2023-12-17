import ast
import os.path
import pathlib
import re

import jedi
from jedi import Script
from jedi.api.classes import Name, BaseSignature

from .const import KIVY_APP_SRC
from ..pyqt import QThread, pyqtSignal


class KivyAnalyser(QThread):
    on_finish = pyqtSignal(object, object)

    class TARGETS:
        KivyApp = 524

    def __init__(self, parent, src=None):
        super(KivyAnalyser, self).__init__(parent)
        self.source = src
        self.target = self.TARGETS.KivyApp
        self.script: Script | None = None

    def kivy_app_import(self):
        imports = {}
        for imp in self.script.get_names(definitions=True):
            if imp.full_name == KIVY_APP_SRC:
                imports.update({imp.name: imp.full_name})

        return imports

    def run(self):
        if self.script:
            if self.target == self.TARGETS.KivyApp:
                imports = self.kivy_app_import()
                apps = {}
                text = pathlib.Path(self.source).read_text()

                if imports:
                    for node in self.script.get_names():
                        node: Name
                        if node.type == "class":
                            inherit = re.finditer(
                                r"^class\s+\w+\((?P<inherit>\w+)\):$", text.splitlines(False)[node.line - 1]
                            )
                            inherit = [inh.group("inherit") for inh in inherit]

                            if inherit and inherit[0] in imports:
                                apps.update({node.name: node})

                self.on_finish.emit(apps, self.script)

        self.finished.emit()

    def trigger(self, src=None, tar=None):
        self.source = src or self.source
        self.target = tar or self.TARGETS.KivyApp

        if os.path.isfile(str(self.source)):
            self.script = Script(pathlib.Path(self.source).read_text(), path=self.source)
        else:
            self.script = None

        if self.isRunning():
            self.terminate()
            self.wait()

        self.run()
