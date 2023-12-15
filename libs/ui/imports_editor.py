import os
import re
from .dialogs import CustomDockWidget
from ..utils import *


class ImportsEditor(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    name = "imports"

    def __init__(self, parent, main):
        super(ImportsEditor, self).__init__(parent)
        self.main = main
        self.imports = []
        self.map = {}
        self.widget = loadUi(import_("ui/imports-editor.ui", 'io'))
        self.setWidget(self.widget)

    def initialize(self, _p=None):
        self.main.dock_it(self, "ra")
        self.widget.imports.setIconSize(QSize(20, 20))
        self.widget.add_alias.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.remove.setIcon(QIcon(import_("img/editors/actions/remove.png")))
        self.setWindowTitle("Imports and Variables")
        self.widget.imports.itemDoubleClicked.connect(self._item_going_to_edit)
        self.widget.imports.itemChanged.connect(self._item_edited)
        self.widget.add_alias.clicked.connect(self._add_item)
        self.widget.alias.returnPressed.connect(self._add_item)
        self.widget.remove.clicked.connect(self._remove_item)
        self.setEnabled(False)

    def _remove_item(self):
        item = self.widget.imports.selectedItems()
        if not item:
            return
        item = item[0]
        data = (item.text(1), item.text(0), self.map.get(id(item)))

        self.imports.remove(data)

        self._update()

    def _update(self):
        os.environ["editor-editing"] = "0"
        self.main.element("inspector.save")()

    def _item_going_to_edit(self, item):
        data = (item.text(1), item.text(0), self.map.get(id(item)))
        if data in self.imports:
            self.imports.remove(data)

    def _item_edited(self, item):
        data = (item.text(1), item.text(0), self.map.get(id(item)))
        self.imports.append(data)
        self._update()

    def _add_item(self):
        type_ = self.widget.type_.currentText()
        keyword = "import" if type_ == "module" else "set"
        icon = type_
        alias = self.widget.alias.text() or "var"
        data = ('None', alias, keyword)

        if data in self.imports:
            self.imports.remove(data)

        self.imports.append(data)
        item = QTreeWidgetItem()
        item.setText(0, alias)
        item.setText(1, "None")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item.setIcon(0, QIcon(import_(f"img/editors/items/{icon}.svg")))
        self.widget.imports.insertTopLevelItem(0, item)
        self.map.update({id(item): keyword})
        self._update()
        self.main.on("add_imports_item", {"alias": alias, "type": icon})

    def done(self):
        self.widget.imports.clear()
        self.imports.clear()

    def load(self, editor):
        self.done()

        text: str = editor.text()
        keywords = ["import", "set"]
        pattern = re.compile(r"\s*#\s*:\s*(?P<keyword>\w+)\s+(?P<alias>\w+)\s+(?P<value>.*?)\n*$", flags=re.MULTILINE)

        for imp in pattern.finditer(text):
            alias = imp.group('alias')
            src = imp.group('value')
            keyword = imp.group('keyword')
            if keyword in keywords:
                icon = "variable" if keyword == keywords[1] else "module"
                if src and alias:
                    self.imports.append((src, alias, keyword))
                    item = QTreeWidgetItem()
                    item.setText(0, alias)
                    item.setText(1, src)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    item.setIcon(0, QIcon(import_(f"img/editors/items/{icon}.svg")))
                    self.widget.imports.insertTopLevelItem(0, item)
                    self.map.update({id(item): keyword})
