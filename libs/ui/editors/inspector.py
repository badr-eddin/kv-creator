import collections
import os
import re

from ...pyqt import QFrame, QTreeWidget, QIcon, QTreeWidgetItem, QsciScintilla, QTabWidget, loadUi, Qt
from ...utils import import_, settings, pan, debug, comp_on
from ...kivy import HookParserRule
from ..dialogs import CustomDockWidget


class Inspector(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    name = "inspector"
    icons = {
        re.compile("bubble$"): "img/editors/kve/bubble.png",
        re.compile(".*button$"): "img/editors/kve/button.png",
        re.compile("camera$"): "img/editors/kve/camera.png",
        re.compile("checkbox$"): "img/editors/kve/checkbox.png",
        re.compile("clipboard$"): "img/editors/kve/clipboard.png",
        re.compile("filechooser$"): "img/editors/kve/filechooser.png",
        re.compile(".*layout$"): "img/editors/kve/layout.png",
        re.compile("screen$|screenmanager$"): "img/editors/kve/screen.png",
        re.compile("accordionitem$|.*listitem$|tabbedpanelitem$"): "img/editors/kve/accordion-item.png",
        re.compile("accordion$"): "img/editors/kve/accordion.png",
        re.compile("scrollview$|recycleview$"): "img/editors/kve/scrollview.png",
        re.compile("splitter$"): "img/editors/kve/splitter.png",
        re.compile("textinput$|codeinput$"): "img/editors/kve/textinput.png",
        re.compile(".*image$"): "img/editors/kve/image.png",
        re.compile("scatter$"): "img/editors/kve/scatter.png",
        re.compile("settings$"): "img/editors/kve/settings.png",
        re.compile("color$|colorpicker$"): "img/editors/kve/color.png",
        re.compile("progressbar$"): "img/editors/kve/progressbar.png",
        re.compile("video$|videoplayer$"): "img/editors/kve/video.png",
        re.compile("switch$"): "img/editors/kve/switch.png",
        re.compile("slider$"): "img/editors/kve/slider.png",
        re.compile("spinner$|dropdown$"): "img/editors/kve/spinner.png",
        re.compile("tabbedpanel$"): "img/editors/kve/tab.png",
        re.compile("modalview$|popup$"): "img/editors/kve/popup.png",
        re.compile("carousel$"): "img/editors/kve/carousel.png",
        re.compile("ellipse$"): "img/editors/kve/ellipse.png",
        re.compile("line$"): "img/editors/kve/line.png",
        re.compile("label$"): "img/editors/kve/label.png",
        re.compile("listview$"): "img/editors/kve/list.png",
        re.compile("vkeyboard$"): "img/editors/kve/keyboard.png",
    }

    FUNCTIONS = ["on_cursor_moved"]

    def __init__(self, parent, main):
        super(Inspector, self).__init__(parent)
        self.main = main
        self.loading = False
        self.prev_item = None
        self.indent_map = {}
        self.lines_map = {}
        self.actions = {}
        self.ids = []
        self.kv_file_ids = {}
        self.loaded_ids = []
        self.elements = {}
        self.actions = {}
        self.objects = {}
        self.widget = loadUi(import_("ui/inspector.ui", 'io'))
        self.tree: QTreeWidget = self.widget.tree

    def initialize(self, _p=None):
        self.main.dock_it(self, "la")
        self.widget.add_class.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.remove.setIcon(QIcon(import_("img/editors/actions/remove.png")))
        self.widget.classes.addItems(settings.pull("kivy/classes"))
        self.tree.itemClicked.connect(self.item_clicked)  # Type: ignore
        self.tree.itemChanged.connect(self.save)  # Type: ignore
        self.tree.itemDoubleClicked.connect(self._item_going_to_change)  # Type: ignore

        self.setWidget(self.widget)
        self.widget.classes.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.itemSelectionChanged.connect(self._tree_clicked)  # Type: ignore
        self.widget.add_class.clicked.connect(self._add_item)
        self.widget.remove.clicked.connect(self._remove_item)
        self.setEnabled(False)
        self.setWindowTitle("Inspector")

        comp_on("finish", self.parsing_done)

    def _remove_item(self):
        item = self.tree.selectedItems()
        if not item:
            return
        item = item[0]
        os.environ["editor-editing"] = "0"
        os.environ["building"] = "0"
        self.delete_tree_item(item)
        self.save()

    def delete_tree_item(self, item):
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.tree.indexOfTopLevelItem(item)
            if index != -1:
                self.tree.takeTopLevelItem(index)

    def _add_item(self):
        cls = self.widget.classes.currentText()
        item = QTreeWidgetItem()
        item.setText(0, cls or "Widget")
        debug(f"adding item of type '{cls or 'Widget'}' ...")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        if id(item) not in self.ids:
            item_ = self.tree.selectedItems()
            if not self.tree.topLevelItemCount():
                self.tree.insertTopLevelItem(0, item)

            elif item_:
                parent_item = item_[0]
                parent_item.addChild(item)

            else:
                item.setText(0, f"<{cls or 'Widget'}>")
                self.tree.insertTopLevelItem(0, item)

            rule = HookParserRule()
            rule.name = item.text(0)
            rule.properties = {}
            self.elements[id(item)] = rule
            self.main.on("add_widget_item", {"text": cls or "Widget"})
            self.reload()
        else:
            self._add_item()

    def reload(self):
        os.environ["editor-editing"] = "0"
        os.environ["building"] = "0"
        self.tree.update()
        self.update()
        self.save()

    @staticmethod
    def on_cursor_moved(kwargs):
        try:
            if not settings.pull("user-prefs/detect-kivy-item"):
                return

            editor = kwargs.get("editor")

            if not isinstance(editor, QsciScintilla):
                return

            if not hasattr(editor, "path"):
                return

            if not str(getattr(editor, "path", "")).endswith(".kv"):
                return

            text = editor.text().splitlines(False)
            line = kwargs.get("pos")[0]

            if line + 1 > len(text):
                return

            if not text[line] or re.match(r"^\s*#.*.", text[line]):
                return

            tree: QTreeWidget = getattr(editor, "main").element('inspector.tree')
            inspector_lines_map: dict = getattr(editor, "main").element('inspector.lines_map')

            item: QTreeWidgetItem = inspector_lines_map.get(line)

            def select_item(tr, it, k=None):
                tr.clearSelection()
                it.setSelected(True)

                if k:
                    getattr(editor, "main").element('inspector.item_clicked')(k)

            if item:
                select_item(tree, item, item)

            else:
                tree_p: QTreeWidget = getattr(editor, "main").element('p-editor.properties')
                parent_item = getattr(editor, "main").element('p-editor.parents_lines_map').get(line)

                if parent_item:
                    select_item(tree, parent_item, parent_item)

                ped_lines_map: dict = getattr(editor, "main").element('p-editor.lines_map')
                item: QTreeWidgetItem = ped_lines_map.get(line)

                if item:
                    select_item(tree_p, item)

        except Exception as e:
            debug(f"inspector::cursor_moved: {e}", _c="e")

    @staticmethod
    def _item_going_to_change():
        os.environ["editor-editing"] = "0"

    def _tree_clicked(self):
        items = self.tree.selectedItems()
        if not items:
            obj = self.main.element("p-editor.properties")
            obj.clear()

    def save(self):
        if os.getenv("building") != "1" and os.getenv("editor-editing") != "1":
            _kv = ""
            imports = self.main.element("imports.imports") or []

            self.prev_item = self.tree.currentItem()

            if self.prev_item:
                self.prev_item = self.prev_item.data(0, Qt.ItemDataRole.UserRole)

            for imp in imports:
                _kv += f"#:{imp[2]} {imp[1]} {imp[0]}\n"

            if _kv:
                _kv += "\n"

            self.ids.clear()
            item = self.widget.tree.invisibleRootItem()
            _kv += self.tree_to_string(item, idn=id(item))
            self.main.element("p-editor.done")()
            self.main.element("imports.done")()
            ew: QTabWidget = self.main.element("editor.widget")
            if ew:
                ed = ew.currentWidget()
                ed.reload = True

                if hasattr(ed, "pid"):
                    temp_path = getattr(ed, "path")

                    line = getattr(ed, "editor").getCursorPosition()[0]

                    if os.path.exists(temp_path):
                        with open(temp_path, "w") as fl:
                            fl.write(_kv)

                        if hasattr(ed, "editor"):
                            ed.editor.setText(_kv)
                    else:
                        self.main.element("msg.pop")("target file not exists !", 3000)
                        debug(f"{temp_path} not found !", _c="e")

                else:
                    line = getattr(ed, "getCursorPosition")
                    line = line()[0] if line else 0
                    ed.setText(_kv)  # Type: ignore
                    self.main.on("inspector_save", {"text": _kv})

                self.select_last_element(line, True)

    def set_item_icon(self, txt, item, tree=True):
        txt: str = txt.lower()

        if not settings.pull("user-prefs/inspector-icons"):
            return

        for icon in self.icons:
            if icon.match(txt):
                icon = self.icons[icon]

                if tree:
                    pars = (0, QIcon(import_(icon)))
                else:
                    pars = (QIcon(import_(icon)), )

                item.setIcon(*pars)
                return

            icon = QIcon(import_("img/editors/kve/object.png"))
            k = 0, icon if tree else icon,
            item.setIcon(*k)

    def tree_to_string(self, item, level=0, idn=0):
        k = "    "
        output = k * (level - 1 if level else level)
        if level:
            if item.text(0):
                output += item.text(0) + ':\n'
                props = self.main.element("p-editor.props")
                props = props.get(idn)
                self.ids.append(idn)
                obj = self.objects.get(id(item))
                if obj:
                    if obj.id:
                        output += k * level + f"id: {obj.id}\n"

                for p in props or []:
                    val = pan.dump(p, props[p].value)
                    vals = val.splitlines(False)

                    if len(vals) > 1:
                        n = k * (level + 1)
                        x = f'\n{n}'.join(vals)
                        val = f"\n{n}{x}"

                    output += k * level + f"{p}: {val}\n"

                events = self.main.element("actions.events_of")(item, level, level+1, k)
                if events:
                    output += events

        for i in range(item.childCount()):
            output += self.tree_to_string(item.child(i), level+1, id(item.child(i)))

        return output

    def done(self):
        self.tree.clear()
        self.elements.clear()
        self.indent_map.clear()

    def populate_tree_widget(self, parent, kivy_widget):
        def load(child):
            text = str(child.name or "Widget")
            item = QTreeWidgetItem(parent)
            self.set_item_icon(text, item)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setText(0, text)
            self._save_kv_item_data(item, child)

            self.populate_tree_widget(item, child)

        if hasattr(kivy_widget, "children"):
            for c in kivy_widget.children:
                load(c)
        else:
            load(kivy_widget)

    def _save_kv_item_data(self, item, kvi):
        self.loaded_ids.append(id(item))
        item.setData(0, Qt.ItemDataRole.UserRole, kvi.line)

        events = [(i.name, i) for i in kvi.handlers]
        self.elements[id(item)] = kvi.properties
        self.actions[id(item)] = collections.OrderedDict(events)

        if kvi.id:
            self.kv_file_ids.update({kvi.id: kvi})

        self.lines_map[kvi.line] = item
        self.objects[id(item)] = kvi

        self.item_clicked(item)

    def parsing_done(self, parsed_kv, *_):
        debug("populating kivy tree ...")

        self.prev_item = self.tree.currentItem()
        if self.prev_item:
            self.prev_item = self.prev_item.data(0, Qt.ItemDataRole.UserRole)

        self.tree.clear()
        self.elements.clear()
        self.objects.clear()
        self.kv_file_ids.clear()

        self.main.element("console.done")()
        self.main.element("p-editor.done")()
        self.main.element("actions.done")()

        if not parsed_kv.root and not parsed_kv.rules:
            return

        for rot in [parsed_kv.root] + parsed_kv.rules:
            if not rot:
                continue

            _rot = rot[1] if type(rot) is tuple else rot
            root = QTreeWidgetItem(self.tree)

            self.set_item_icon(_rot.name, root)
            root.setText(0, _rot.name)
            root.setFlags(root.flags() | Qt.ItemFlag.ItemIsEditable)

            self._save_kv_item_data(root, _rot)

            self.populate_tree_widget(root, _rot)

            root.setSelected(True)
            self.item_clicked(root)

        self.tree.expandAll()
        editor = self.main.element("editor.widget").currentWidget()

        if editor:
            editor.reload = True

        os.environ["building"] = "0"
        self.select_last_element()

    def select_last_element(self, line=None, imp=False):
        obj = self.main.element("editor.widget").currentWidget()
        x = (self.prev_item or line) if not imp else line

        if type(x) is int:
            self.on_cursor_moved({"editor": obj, "pos": [x, 0]})

    def item_clicked(self, item):
        pid = id(item)
        func = self.main.element("p-editor.load_properties")
        func2 = self.main.element("actions.load_actions")
        func(self.elements.get(pid), item)
        func2(self.actions.get(pid), item)
