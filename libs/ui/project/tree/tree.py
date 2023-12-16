import os
import pathlib
import send2trash

from .const import FILE, FOLDER
from .menu import TreeMenu
from ...dialogs import CustomDockWidget, InLineInput
from ....pyqt import QFrame, QTreeWidget, QTreeWidgetItem, QIcon, loadUi, Qt, QFileIconProvider, QFileInfo
from ....utils import import_, debug


class ProjectTree(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    _RENAME = 3
    _MAKE = 6

    def __init__(self, parent, main):
        super(ProjectTree, self).__init__(parent)
        self.main = main
        self.root_path = main.project_path
        self.map = {}
        self.item_will_change = None
        self.menu = TreeMenu(self.main, self)

        self.item_going_to_change = None
        self.create_input = InLineInput(self)
        self.root = None
        self.widget = loadUi(import_("ui/ptree.ui", 'io'))
        self.files_tree: QTreeWidget = self.widget.files

    def initialize(self, _p=None):
        self.main.dock_it(self, "la")
        self.setWidget(self.widget)
        self.setWindowTitle("Project")
        self.setMinimumHeight(300)
        self.load_files_at()
        self.connect_items()
        self.widget.add_folder.setIcon(QIcon(import_("img/editors/actions/add-folder.png")))
        self.widget.add_file.setIcon(QIcon(import_("img/editors/actions/add-file.png")))
        self.widget.remove_item.setIcon(QIcon(import_("img/editors/actions/delete.png")))
        self.files_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def connect_items(self):
        self.files_tree.itemDoubleClicked.connect(self._item_double_clicked)  # Type: ignore
        self.widget.show_hf.clicked.connect(self._toggle_hidden_files)
        self.files_tree.itemCollapsed.connect(self._item_collapsed)  # Type: ignore
        self.widget.add_file.clicked.connect(lambda: self.make(FILE))
        self.widget.add_folder.clicked.connect(lambda: self.make(FOLDER))
        self.widget.remove_item.clicked.connect(self.__delete_item)
        self.files_tree.customContextMenuRequested.connect(self._open_item_context_menu)
        self.files_tree.itemChanged.connect(self._item_changed)
        self.files_tree.currentItemChanged.connect(self._current_item_changed)

    def _open_item_context_menu(self, _):
        self.menu.build()
        self.menu.exec(self.main.cursor().pos())

    def build_context_menu(self):
        self.menu.clear()

    def _item_collapsed(self, item):
        if id(item) == id(self.root):
            self.files_tree.collapseAll()

    def _toggle_hidden_files(self, sts):
        self.load_files_at(shf=sts)

    def load_files_at(self, path=None, shf=False):
        self.root_path = path or self.root_path
        path = self.root_path

        if os.path.isdir(path):
            self.main.on("project_tree_load", {"path": path})
            self.files_tree.clear()
            self.map.clear()
            self.root = QTreeWidgetItem()
            self.root.setText(0, os.path.basename(path))
            self.root.setIcon(0, QFileIconProvider().icon(QFileInfo(path)))
            self.files_tree.addTopLevelItem(self.root)
            self.map.update({id(self.root): path})
            self._recursive_loading(path, self.root, shf)
            self.files_tree.expandItem(self.root)

    @staticmethod
    def _sort(path):
        items = os.listdir(path)
        dirs = [dir_path for dir_path in items if os.path.isdir(os.path.join(path, dir_path))]
        files = [file_path for file_path in items if os.path.isfile(os.path.join(path, file_path))]
        return sorted(dirs) + sorted(files)

    def _recursive_loading(self, path, parent, shf):
        for i in self._sort(path):
            if (i.startswith(".") or i == "__pycache__") and not shf:
                continue

            item = QTreeWidgetItem()
            full = os.path.join(path, i)
            item.setData(0, 0, full)

            item.setText(0, i)
            item.setIcon(0, QFileIconProvider().icon(QFileInfo(full)))

            parent.addChild(item)
            self.map.update({id(item): full})

            if os.path.isdir(full):
                self._recursive_loading(full, item, shf)

    def open_file(self, item):
        self._item_double_clicked(item)

    def _item_double_clicked(self, item):
        path = self.map.get(id(item))
        if not path:
            return

        path = pathlib.Path(path)
        if path.is_file():
            self.main.element("editor.add_editor")(path.read_text(), path.as_posix())

    def _item_changed(self, item):
        if (self.item_going_to_change or {}).get(id(item)):
            parent, typ = self.item_going_to_change.get(id(item))
            action = self.item_going_to_change.get("action")

            if action == self._MAKE:
                if typ == FILE:
                    self.__create_file(item.text(0), self.map.get(id(parent)))
                else:
                    self.__create_folder(item.text(0), self.map.get(id(parent)))
            else:
                pre_item, old = self.item_going_to_change.get(id(item))
                new = os.path.join(os.path.split(old)[0], pre_item.text(0))
                os.rename(old, new)

                if old == self.root_path:
                    self.root_path = new

                    self.main.save_project_path(new)

                self.load_files_at()

            self.item_going_to_change = None

    def _current_item_changed(self):
        if self.item_going_to_change:
            self.files_tree.closePersistentEditor(self.item_going_to_change.get("item"), 0)
            self.item_going_to_change = None

    def make(self, typ):
        if typ in [FILE, FOLDER]:
            parent: QTreeWidgetItem = self.files_tree.currentItem()
            if parent:
                self.files_tree.expandItem(parent)
                item = QTreeWidgetItem()
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                parent.addChild(item)
                self.files_tree.openPersistentEditor(item, 0)

                self.item_going_to_change = {id(item): [parent, typ], "action": self._MAKE, "item": item}
            else:
                debug("select parent folder first !")

    def rename(self, item_s=None):
        item, path = item_s[0][0] or self.files_tree.currentItem(), item_s[0][1]
        if not item:
            return

        self.item_going_to_change = {id(item): [item, path], "action": self._RENAME, "item": item}

        self.files_tree.openPersistentEditor(item, 0)

    def __create_folder(self, inp, parent_path):
        path = os.path.join(parent_path, inp)

        if os.path.exists(path):
            self.main.element("msg.pop")(f"name '{inp.text()}' already exists !", 3000)
            return

        os.mkdir(path)
        if os.path.exists(path):
            self.load_files_at()
            self.main.on("project_create_folder", {"path": path})
        else:
            self.main.element("msg.pop")(f"couldn't create '{inp.text()}', "
                                         f"unexpected error occur !", 2000)

    def __create_file(self, inp, parent_path):
        path = os.path.join(parent_path, inp)

        if os.path.exists(path):
            self.main.element("msg.pop")(f"name '{inp.text()}' already exists !")
            return

        open(path, "w").write("")

        if os.path.exists(path):
            self.load_files_at()
            self.main.on("project_create_file", {"path": path})
        else:
            self.main.element("msg.pop")(f"couldn't create '{inp.text()}', unexpected error occur !")

    def delete(self, items):
        self.__delete_item(items)

    def __delete_item(self, items=None):
        items = items or self.files_tree.selectedItems()

        for item in items:
            path = self.map.get(id(item))
            if not path:
                continue

            if os.path.exists(path):
                if path == self.root_path:
                    self.main.element("msg.pop")("cannot delete project root folder !")
                    return

                if os.path.isdir(path):
                    if os.listdir(path):
                        inform = self.main.element("inform")
                        inform.no_cancel()
                        inform.inform(
                            "you are about to permanently delete the entire folder and all its contents.",
                            "Trash",
                            on_accept=self._delete_dir, on_deny=self._deny_delete_dir, args=(path,), sts=0
                        )
                        continue

                send2trash.send2trash(path)

            else:
                self.main.element("msg.pop")("it seems that this file has been deleted externally .", 5000)
        self.load_files_at()

    def _delete_dir(self, *args):
        args[0].close()
        send2trash.send2trash(args[1])
        self.main.on("project_send2trash", {"path": args[1]})
        self.load_files_at()

    def _deny_delete_dir(self, *args):
        args[0].close()
        self.load_files_at()
