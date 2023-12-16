from ....pyqt import QAction, QMenu, QIcon
from ....utils import settings, import_, debug
from .const import FILE, FOLDER
import os


class TreeMenuAction(QAction):
    def __init__(self, parent, on_click=None, args=None):
        super(TreeMenuAction, self).__init__(parent)
        self.on_click = on_click
        self.args = args

        self.triggered.connect(self.__clicked)  # Type: ignore

    def __clicked(self):
        if self.on_click:
            self.on_click(*(self.args or ()))


class TreeMenu(QMenu):
    def __init__(self, main, parent):
        super(TreeMenu, self).__init__()
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
                action = TreeMenuAction(self, args=(obj,))

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

    def is_root(self, item_s):
        path = self.parent.map.get(id(item_s))
        return path == self.parent.root_path

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

    def new_folder(self, _):
        debug("creating new folder ...")
        self.parent.make(FOLDER)

    def new_file(self, _):
        debug("creating new file ...")
        self.parent.make(FILE)

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

    def new_project(self, _=None):
        self.close_project(d=False)

    def close_project(self, _=None, d=True):
        with open(self.main.proc, "w") as f:
            f.write("")

        self.main.get_project(d)
