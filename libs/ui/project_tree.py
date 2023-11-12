import os
import pathlib
import send2trash

from ..utils import *
from . import InLineInput


class MAction(QAction):
    def __init__(self, parent, on_click=None, args=None):
        super(MAction, self).__init__(parent)
        self.on_click = on_click
        self.args = args

        self.triggered.connect(self.__clicked)  # Type: ignore

    def __clicked(self):
        if self.on_click:
            self.on_click(*(self.args or ()))


class Menu(QMenu):
    def __init__(self, main, parent):
        super(Menu, self).__init__()
        self.parent = parent
        self.main = main
        self.actions = settings.pull("ptree/menu")
        self.setMinimumWidth(200)

    def build(self):
        self.clear()

        items = self.parent.files_tree.selectedItems()
        item = self.parent.files_tree.currentItem()

        for ac in self.actions:
            obj = self.actions.get(ac)

            if obj.get("check"):
                checks = str(obj.get("check")).replace(" ", "").split("&&")
                x = 0

                for check in checks:
                    if hasattr(self, check):
                        if getattr(self, check)(items if obj.get("multi") else item):
                            x += 1

                add_action = x == len(checks)

            else:
                add_action = True

            if add_action:
                action = MAction(self, args=(obj, ))

                callback = hasattr(self, obj.get("callback") or "___o")
                if callback:
                    callback = getattr(self, obj.get("callback"))
                    action.on_click = callback

                if obj.get("icon"):
                    action.setIcon(QIcon(import_(obj.get("icon"))))
                action.setText(ac)

                self.addAction(action)

    def is_folder(self, item_s):
        items = item_s if type(item_s) is list else [item_s]
        ps = 0

        for item in items:
            k = self.parent.map.get(id(item))
            if k:
                ps += int(os.path.isdir(k))

        return ps == len(items)

    def is_file(self, item_s):
        items = item_s if type(item_s) is list else [item_s]
        ps = 0

        for item in items:
            k = self.parent.map.get(id(item))
            if k:
                ps += int(os.path.isfile(k))
        return ps == len(items)

    def is_single_selection(self, _):
        return len(self.parent.files_tree.selectedItems()) == 1

    def get_item_s(self, multi=False):
        if multi:
            data = []

            for item in self.parent.files_tree.selectedItems() or []:
                data.append([item, self.parent.map.get(id(item))])

            return data

        item = self.parent.files_tree.currentItem()
        return [[item, self.parent.map.get(id(item))]]

    def new_folder(self, obj):
        debug("creating new folder ...")
        self.parent.make(PTree.FOLDER)

    def new_file(self, obj):
        debug("creating new file ...")
        self.parent.make(PTree.FILE)

    def rename_item(self, obj):
        item = self.get_item_s(obj.get("multi"))
        typ = "folder" if os.path.isdir(item[0][1]) else "file"
        debug(f"renaming {typ} ...")
        self.parent.rename(item)

    def delete_items(self, obj):
        items = self.get_item_s(obj.get("multi"))
        debug("deleting items ...")

        items = [item[0] for item in items]

        self.parent.delete(items)

    def open_file(self, obj):
        debug("opening file ...")
        item = self.get_item_s(obj.get("multi"))
        self.parent.open_file(item[0][0])


class PTree(QDockWidget):
    ui = "head"
    ui_type = QFrame

    FOLDER = 4
    FILE = 8
    _RENAME = 3
    _MAKE = 6

    def __init__(self, parent, main):
        super(PTree, self).__init__(parent)
        self.main = main
        self.root_path = main.project_path
        self.map = {}
        self.item_will_change = None
        self.menu = Menu(self.main, self)

        self.item_going_to_change = None
        self.create_input = InLineInput(self)
        self.root = None
        self.widget = loadUi(import_("ui/ptree.ui"))
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
        self.widget.add_file.clicked.connect(lambda: self.make(self.FILE))
        self.widget.add_folder.clicked.connect(lambda: self.make(self.FOLDER))
        self.widget.remove_item.clicked.connect(self.__delete_item)
        self.files_tree.customContextMenuRequested.connect(self._open_item_context_menu)
        self.files_tree.itemChanged.connect(self._item_changed)
        self.files_tree.currentItemChanged.connect(self._current_item_changed)

    def _open_item_context_menu(self, item):
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
            self.main.buttons.get_obj("editor.add_editor")(path.read_text(), path.as_posix())

    def _item_changed(self, item):
        if (self.item_going_to_change or {}).get(id(item)):
            parent, typ = self.item_going_to_change.get(id(item))
            action = self.item_going_to_change.get("action")

            if action == self._MAKE:
                if typ == self.FILE:
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
        if typ in [self.FILE, self.FOLDER]:
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
            self.main.buttons.get_obj("msg.pop")(f"name '{inp.text()}' already exists !", 3000)
            return

        os.mkdir(path)
        if os.path.exists(path):
            self.load_files_at()
            self.main.on("project_create_folder", {"path": path})
        else:
            self.main.buttons.get_obj("msg.pop")(f"couldn't create '{inp.text()}', "
                                                 f"unexpected error occur !", 2000)

    def __create_file(self, inp, parent_path):
        path = os.path.join(parent_path, inp)

        if os.path.exists(path):
            self.main.buttons.get_obj("msg.pop")(f"name '{inp.text()}' already exists !")
            return

        open(path, "w").write("")

        if os.path.exists(path):
            self.load_files_at()
            self.main.on("project_create_file", {"path": path})
        else:
            self.main.buttons.get_obj("msg.pop")(f"couldn't create '{inp.text()}', unexpected error occur !")

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
                    self.main.buttons.get_obj("msg.pop")("cannot delete project root folder !")
                    return

                if os.path.isdir(path):
                    if os.listdir(path):
                        inform = self.main.buttons.get_obj("inform")
                        inform.no_cancel()
                        inform.inform(
                            "you are about to permanently delete the entire folder and all its contents.",
                            "Trash",
                            on_accept=self._delete_dir, on_deny=self._deny_delete_dir, args=(path,), sts=0
                        )
                        continue

                send2trash.send2trash(path)

            else:
                self.main.buttons.get_obj("msg.pop")("it seems that this file has been deleted externally .",
                                                     5000)
        self.load_files_at()

    def _delete_dir(self, *args):
        args[0].close()
        send2trash.send2trash(args[1])
        self.main.on("project_send2trash", {"path": args[1]})
        self.load_files_at()

    def _deny_delete_dir(self, *args):
        args[0].close()
        self.load_files_at()
