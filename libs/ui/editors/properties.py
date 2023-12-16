import json
import os
import re
from collections import OrderedDict

from ..dialogs import CustomDockWidget
from ...pyqt import QFrame, QTreeWidget, QTreeWidgetItem, QIcon, loadUi, Qt
from ...kivy import HookParserRule
from ...utils import pan, settings, import_, debug


class Properties(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    name = "p-editor"

    def __init__(self, parent, main):
        super(Properties, self).__init__(parent)
        self.main = main
        self.props = {}
        self.parent_item = None
        self.map = {}
        self.lines_map = {}
        self.map_lines = {}
        self.parents_lines_map = {}

        self.kv_props = settings.pull("kivy/properties")
        self.widget = loadUi(import_("ui/property-editor.ui", 'io'))
        self.properties: QTreeWidget = self.widget.properties
        self.setWidget(self.widget)

    def initialize(self, _p=None):
        self.main.dock_it(self, "ra")
        self.properties.itemChanged.connect(self.update_prop)  # Type: ignore
        self.properties.itemDoubleClicked.connect(self._item_going_to_change)  # Type: ignore
        self.widget.add_prop.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.remove.setIcon(QIcon(import_("img/editors/actions/remove.png")))
        self.widget.props.addItems(settings.pull("kivy/properties"))
        self.widget.props.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.widget.add_prop.clicked.connect(self.add_property)
        self.widget.remove.clicked.connect(self._remove_item)
        self.setWindowTitle("Properties")
        self.setEnabled(False)

    def _item(self):
        current = self.main.element("inspector.widget").tree.selectedItems()
        if not current:
            self.main.element("msg.pop")("no item selected !", 2000)
            return
        return current[0]

    def add_property(self):
        prop = self.widget.props.currentText()
        current = self._item()
        item_id = id(current)
        if not self.props.get(item_id):
            self.props[item_id] = {}

        rule = HookParserRule()
        rule.name = prop
        rule.value = "None"

        self.props[item_id][prop] = rule
        item = QTreeWidgetItem()
        item.setText(0, prop)
        item.setText(1, "None")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.properties.insertTopLevelItem(0, item)
        self.main.on("add_property", {"property": prop})
        self._update()

    def _remove_item(self):
        item = self._item()
        sli = self.properties.selectedItems()
        if not sli:
            return

        current = sli[0]
        if item:
            pid = id(item)
            if self.props.get(pid):
                if self.props[pid][current.text(0)]:
                    del self.props[pid][current.text(0)]
                    self.main.on("remove_property", {"property": current.text(0), "value": current.text(1)})

        self._update()

    def _update(self):
        os.environ["editor-editing"] = "0"
        self.main.element("inspector.save")()

    def _item_going_to_change(self, item):
        os.environ["editor-editing"] = "0"

        current_item = self.main.element("inspector.tree").selectedItems()
        if not current_item:
            return

        current_item = current_item[0]

        if self.props.get(id(current_item)):
            if self.props.get(id(current_item)).get(item.text(0)):
                del self.props[id(current_item)][item.text(0)]

    def update_prop(self, item):
        func = self.main.element("inspector.save")
        rem = self.main.element("inspector.select_last_element")
        props_id = self.map.get(id(item))

        c_line = self.map_lines.get(id(item))

        if props_id:
            rule = HookParserRule()
            rule.name = item.text(0)
            rule.value = item.text(1)
            self.props[props_id][item.text(0)] = rule
            self.main.on("update_property", {"property": item.text(0), "value": item.text(1)})
        func()
        rem(self.main.element("editor.widget").currentWidget(), c_line)

    def done(self):
        self.properties.clear()
        self.props.clear()
        self.map.clear()

    def eval_prop(self, prop, value):
        prop_type = str(self.kv_props.get(prop)).lower()

        if re.match(r".*string.*|.*numeric.*", prop_type):
            try:
                return json.loads(value)
            except Exception as e:
                debug(f"eval-prop: {e}", _c="e")
                return json.loads(f'"{value}"')

        return value

    def load_properties(self, props, par):
        self.properties.clear()
        self.lines_map.clear()
        self.props.update({id(par): props})

        self.parent_item = par

        if not props:
            props = OrderedDict([])

        if not isinstance(props, OrderedDict):
            props = OrderedDict(tuple(props))

        for prop in props:
            value = props[prop].value
            value = pan.load(prop, value)
            item = QTreeWidgetItem()

            item.setText(0, str(prop))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setText(1, value)

            self.properties.insertTopLevelItem(0, item)
            self.map.update({id(item): id(par)})

            self.lines_map[props[prop].line] = item
            self.map_lines[id(item)] = props[prop].line
            self.parents_lines_map[props[prop].line] = par
