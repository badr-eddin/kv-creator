import collections
import os
import re
from ..utils import *
from kivy.lang import Parser, ParserException


class DemoParserRule:
    name: str
    properties: dict
    id: str
    value: str


class ThreadedParser(QThread):
    on_error = pyqtSignal(object, list)
    on_finish = pyqtSignal(object, object)

    def __init__(self, parent, text, path, arg=None):
        super(ThreadedParser, self).__init__(parent)
        self.path = path
        self.text = text
        self.arg = arg

    def run(self):
        try:
            parsed = Parser(content=self.text, filename=self.path)

            if self.arg:
                self.on_finish.emit(self.arg, parsed)
            else:
                self.on_finish.emit(parsed)

        except Exception as e:
            debug(f"thread::parse : {e.msg}", _c="e")
            self.on_error.emit(self.arg, [
                {
                    "type": "error",
                    "message": e.msg,
                    "line": e.lineno
                }
            ])

        self.finished.emit()


class Inspector(QDockWidget):
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
        self.ids = []
        self.loaded_ids = []
        self.elements = {}
        self.objects = {}
        self.widget = loadUi(import_("ui/inspector.ui", 'io'))
        self.tree: QTreeWidget = self.widget.tree
        self.setWidget(self.widget)
        self.tree.itemClicked.connect(self.item_clicked)  # Type: ignore
        self.tree.itemChanged.connect(self.save)  # Type: ignore
        self.tree.itemDoubleClicked.connect(self._item_going_to_change)  # Type: ignore

    def initialize(self, _p=None):
        self.main.dock_it(self, "la")
        self.widget.add_class.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.remove.setIcon(QIcon(import_("img/editors/actions/remove.png")))
        self.widget.classes.addItems(settings.pull("kivy/classes"))

        self.widget.classes.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.itemSelectionChanged.connect(self._tree_clicked)  # Type: ignore
        self.widget.add_class.clicked.connect(self._add_item)
        self.widget.remove.clicked.connect(self._remove_item)
        self.setEnabled(False)
        self.setWindowTitle("Inspector")

        # self.tree.setIconSize(QSize(20, 20))

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

            rule = DemoParserRule()
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

            if not str(editor.path).endswith(".kv"):
                return

            text = editor.text().splitlines(False)
            line = kwargs.get("pos")[0]

            if line + 1 > len(text):
                return

            if not text[line] or re.match(r"^\s*#.*.", text[line]):
                return

            if not re.match(r"\s*\w+\s*:\s*$", text[line]):
                return

            tree: QTreeWidget = editor.main.element('inspector.tree')
            lines_map: dict = editor.main.element('inspector.lines_map')
            item: QTreeWidgetItem = lines_map.get(line)

            if item:
                tree.clearSelection()
                item.setSelected(True)
                editor.main.element('inspector.item_clicked')(item)

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

                    if os.path.exists(temp_path):
                        with open(temp_path, "w") as fl:
                            fl.write(_kv)

                        if hasattr(ed, "editor"):
                            ed.editor.setText(_kv)
                    else:
                        self.main.element("msg.pop")("target file not exists !", 3000)
                        debug(f"{temp_path} not found !", _c="e")
                else:
                    ed.setText(_kv)  # Type: ignore
                    self.main.on("inspector_save", {"text": _kv})

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
                    output += k * level + f"{p}: {pan.dump(p, props[p].value)}\n"

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
            item.setData(0, Qt.ItemDataRole.UserRole, child.line)
            item.setText(0, text)
            self.loaded_ids.append(id(item))
            events = [(i.name, i) for i in child.handlers]
            self.elements[id(item)] = child.properties
            self.lines_map[child.line] = item
            self.elements[id(item)].update(
                collections.OrderedDict(events)
            )
            self.objects[id(item)] = child
            self.item_clicked(item)
            self.populate_tree_widget(item, child)

        if hasattr(kivy_widget, "children"):
            for c in kivy_widget.children:
                load(c)
        else:
            load(kivy_widget)

    def parsing_finished(self, obj, parsed):
        self.main.element("console.done")()
        self.main.element("p-editor.done")()

        if hasattr(obj.lexer(), "clear_errors"):
            obj.lexer().clear_errors()

        self.parsing_done_well(parsed)

    def parsing_crashed(self, obj, errors):
        self.main.element("console.report")(errors)

    def parsing_done_well(self, parsed_kv):
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

            self.lines_map[_rot.line] = root
            self.elements[id(root)] = _rot.properties
            self.objects[id(root)] = _rot

            self.populate_tree_widget(root, _rot)

        self.tree.expandAll()
        self.main.element("editor.widget").currentWidget().reload = True
        os.environ["building"] = "0"

    def load_class(self, obj):
        self.prev_item = self.tree.currentItem()

        self.tree.clear()
        self.elements.clear()
        self.objects.clear()
        text = obj.text()

        if not obj.path or not str(obj.path).endswith(".kv"):
            self.main.element("p-editor.done")()
            return

        thread = ThreadedParser(self, text, obj.path, obj)
        thread.on_error.connect(self.parsing_crashed)
        thread.on_finish.connect(self.parsing_finished)
        thread.start()

    def item_clicked(self, item):
        pid = id(item)
        func = self.main.element("p-editor.load_properties")
        func(self.elements.get(pid), pid)
