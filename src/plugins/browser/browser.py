import os
import pathlib
import re

import pyautogui
from PyQt6.QtCore import QRect, QPoint, QSize, QFileInfo, Qt, QPropertyAnimation, QTimer
from PyQt6.QtGui import QPainter, QBrush, QIcon
from PyQt6.QtWidgets import *


class PathItem(QPushButton):
    path = ""

    def __init__(self, parent, on_click=None, text=""):
        super(PathItem, self).__init__(parent)
        self.on_click = on_click

        self.setFixedSize(QSize(len(text) * 10 if len(text) > 1 else 15, 25))
        self.setText(text)
        self.clicked.connect(self._clicked)  # Type: ignore

    def _clicked(self):
        if self.on_click:
            self.on_click(self.path)


class FileDialog(QWidget):
    class Selection:
        Multi = 0
        Single = 1

    class Targets:
        Dirs = 2
        Files = 3

    class Mode:
        Open = 4
        Save = 5

    # **********************************************

    def __init__(self, main=None, std=None, **kwargs):
        super().__init__()
        std = std or main.std
        self.std = std
        self.main = main
        self.animate = False
        self.pop_anim = QPropertyAnimation(self, b"pos")
        self.widget = std.loadUi(std.import_("plugins/ui/file-dialog.ui"))
        self.creating = False
        self._close = False
        self.path_frame = None
        self.cover = QWidget(self.main)
        self.current_path = ""
        self.p_fac = self.main.size().height()
        self._save_clicking = False
        self.filter = re.compile("")
        self.files_list: QListWidget = self.widget.files
        self._data = kwargs
        self.x, self.y = 0, 0
        self._restore(self.main)
        self.widget.setStyleSheet(
            "QPushButton, QComboBox{border: none; background: #080808}"
        )

        self.config_ui()

    def config_ui(self):
        self.std.set_layout(self, QVBoxLayout).addWidget(self.widget)

        self.widget.cancel.clicked.connect(self._cancel)
        self.widget.bclose.clicked.connect(self._cancel)
        self.widget.openf.clicked.connect(self._open_save_clicked)
        self.widget.create_folder.clicked.connect(self.create_folder)
        self.widget.file_name.textChanged.connect(self._save_file_name_changed)
        self.files_list.itemDoubleClicked.connect(self._navigate_comes_from_list)  # Type: ignore
        self.files_list.itemClicked.connect(self._file_clicked)  # Type: ignore
        self.files_list.setIconSize(QSize(100, 100))
        self.widget.bclose.setIcon(QIcon(self.std.import_("img/style/close.svg")))

        self.std.bald(self)
        self.std.set_shadow(self)
        self.move(QPoint(self.x, self.y-self.p_fac))
        self.main.on_resize(self._restore)

    def paintEvent(self, a0):
        painter = QPainter(self)

        w = self.size().width()
        h = self.size().height()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.std.theme("background_c")))

        rect = QRect(QPoint(0, 0), QSize(w, h))
        painter.drawRect(rect)

        painter.setBrush(QBrush(self.std.theme("head_c")))

        head = QRect(QPoint(0, 0), QSize(w, 74))
        painter.drawRect(head)

        btm = QRect(QPoint(0, h-60), QSize(w, 60))
        painter.drawRect(btm)

        super(FileDialog, self).paintEvent(a0)

    def keyReleaseEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        super(FileDialog, self).keyPressEvent(a0)

    def closeEvent(self, a0):
        if not self._close:
            self._close = True

            if self.animate:
                self.pop_anim.setEndValue(QPoint(self.x, self.y-self.p_fac))
                self.pop_anim.setDuration(200)
                self.pop_anim.start()
                QTimer().singleShot(1000, self.close)
                a0.ignore()
            else:
                self.close()
        else:
            super(FileDialog, self).closeEvent(a0)
            self._close = False

    # **********************************************
    def encapsulate(self, path):
        path = path.as_posix() if isinstance(path, pathlib.Path) else path
        encapsulate = self._data.get("encapsulate")
        if encapsulate:
            path = encapsulate(path)
        return path

    def custom_check(self, path):
        if self._data.get("custom_check"):
            v = self._data.get("custom_check")(self.encapsulate(path))
            return path if v else None
        return path

    def build_path_levels(self, path=None):
        if self.path_frame:
            self.widget.path_bar.removeWidget(self.path_frame)

        self.path_frame = QFrame(self)
        layout = self.std.set_layout(self.path_frame, QHBoxLayout)
        path = pathlib.Path(path or self._data.get("entry") or os.getcwd())
        self.current_path = path.as_posix()

        self.widget.title.setText(path.as_posix())
        if path.exists():
            pth = ""
            for part in path.parts:
                item = PathItem(self, self.navigate_to, text=part)
                pth = os.path.join(pth, part)
                item.path = pth
                layout.addWidget(item)

            layout.addItem(self.std.SPItem(200))
            self.widget.path_bar.addWidget(self.path_frame)

    def _navigate_comes_from_list(self, item):
        self.navigate_to(os.path.join(self.current_path, item.text()))

    def _open_save_clicked(self):
        self.cover.close()
        k = 0
        if self._data.get("mode") == self.Mode.Save:
            name = self.widget.file_name.text()
            path = pathlib.Path(os.path.join(self.current_path, name))
            if name:
                if path.exists():
                    log = f"{'folder' if self._data.get('target') == self.Targets.Dirs else 'file'} " \
                          f"'{path.name}', already exists !"
                    self.std.debug(log, _c="w")
                    self.inform(log + " Overwrite ?", "Save",
                                lambda _: self._save_dialog_accept(self.encapsulate(path.as_posix())))

                else:
                    if self.filter.match(path.name):
                        self.callback(path)
                    else:
                        msg = self.main.buttons.get_obj("msg")
                        msg.pop("invalid file name !", 5000)
        else:
            items = self.files_list.selectedItems() or ["$"]
            paths = []
            for item in items:
                if item != "$":
                    path = os.path.join(self.current_path, item.text())
                else:
                    path = self.current_path
                if os.path.isdir(path):
                    if self._data.get("target") == self.Targets.Files:
                        k = 1
                        self.navigate_to(path)
                        break
                try:
                    path = self.encapsulate(path)
                except Exception as e:
                    self.std.debug(f"fbr: path encapsulation -> {e}", _c="e")

                paths.append(path)

            if not k:
                paths = paths if len(paths) else [None]
                self.cover.close()
                self.callback(paths if len(paths) > 1 else paths[0])

    def _cancel(self):
        self.cover.close()
        self.close()

    def _save_dialog_refuse(self, d):
        d.close()
        self.cover.close()

    def _save_dialog_accept(self, path):
        self.cover.close()
        self.callback(path)

    def _save_file_name_changed(self):
        if self._data.get("mode") == self.Mode.Save and not self._save_clicking:
            self.files_list.clearSelection()
        self._save_clicking = False

    def is_it_valid_file(self, path):
        path = pathlib.Path(path)
        target = self._data.get("target")

        if target == self.Targets.Dirs:
            return path.is_dir()

        if self._data.get("mode") == self.Mode.Open:
            return self.filter.match(path.name) or path.is_dir()

        if self._data.get("mode") == self.Mode.Save:
            return True

    def _file_clicked(self, item):
        self._save_clicking = True
        text = item.text()

        if not self.filter.match(text):
            text = ""

        if os.path.isdir(os.path.join(self.current_path, text)) \
                and self._data.get("target") != self.Targets.Dirs:
            text = ""

        self.widget.file_name.setText(text)

    def _restore(self, m=None):
        if m:
            self.cover.resize(self.main.size())
        self.x, self.y = self.std.restore(self, self.widget.size(), sz=pyautogui.size())
        self.move(QPoint(self.x, self.y))

    def _cover(self):
        self.cover.setStyleSheet("background: rgba(255, 255, 255, 20)")
        self.cover.resize(self.main.size())
        self.cover.move(QPoint(0, 0))
        self.cover.show()

    def inform(self, text, title, oac):
        inform = self.std.InformUser(self, self.main, True)
        inform.setWindowModality(Qt.WindowModality.NonModal)
        inform.no_cancel()
        inform.inform(text, title, dis=self.widget,
                      res=(self.size().width(), self.size().height()), sz=(300, 120),
                      on_accept=oac, on_deny=self._save_dialog_refuse)

    def get_valid_new_folder_name(self, path, suffix, k=0):
        new = f"{suffix} ({k})" if k else suffix
        if os.path.exists(os.path.join(path, new)):
            return self.get_valid_new_folder_name(path, suffix, k+1)
        return new

    # **********************************************

    def callback(self, path=None):
        callback = self._data.get("callback")
        path = self.custom_check(path)
        self.close()

        if path and callback:
            callback(path)

    def navigate_to(self, path=None):
        path = pathlib.Path(path or self._data.get("entry") or os.getcwd())

        if path.is_dir():
            self.build_path_levels(path)
            self.files_list.clear()

            items = os.listdir(path.as_posix())
            dirs = [dir_path for dir_path in items if os.path.isdir(os.path.join(path.as_posix(), dir_path))]
            files = [file_path for file_path in items if os.path.isfile(os.path.join(path.as_posix(), file_path))]
            items = sorted(dirs) + sorted(files)

            for file in items:
                fpt = os.path.join(path.as_posix(), file)

                if not self.is_it_valid_file(fpt):
                    continue

                item = QListWidgetItem()
                icon = QFileIconProvider().icon(QFileInfo(fpt))
                item.setText(file)
                item.setIcon(icon)
                item.setToolTip(file)
                self.files_list.addItem(item)
        else:
            self.cover.close()
            self.callback(path)

    def open_save_file(self, **kwargs):
        self._cover()

        self._data = kwargs or self._data

        self._conf_mode()
        self._conf_ui_filters()
        self._conf_selection()

        self.show_up()
        self.build_path_levels()
        self.navigate_to()

    def show_up(self):
        self.show()
        self.raise_()

        if self.animate:
            self.pop_anim.setEndValue(QPoint(self.x, self.y))
            self.pop_anim.setDuration(200 if self.animate else 0)
            self.pop_anim.start()
        else:
            self.move(QPoint(self.x, self.y))

    def create_folder(self):
        if self.creating:
            return

        self.creating = True
        path = self.current_path
        pos = self.mapFromGlobal(self.cursor().pos())

        def create(name):
            name.close()
            init_name = self.get_valid_new_folder_name(path, name.text())
            os.mkdir(os.path.join(path, init_name))
            self.navigate_to(path)
            self.creating = False

        self.std.InLineInput(create, "folder name", self).read_at(pos)

    # **********************************************

    def _conf_selection(self):
        selection = self._data.get("selection")
        if selection == self.Selection.Multi:
            self.files_list.setSelectionMode(self.files_list.SelectionMode.ExtendedSelection)
        else:
            self.files_list.setSelectionMode(self.files_list.SelectionMode.SingleSelection)

    def _conf_ui_filters(self):
        filters = self._data.get("filters")
        self.widget.filters.clear()

        if isinstance(filters, (list, tuple)):
            self.widget.filters.addItems(list(self._data.get("labels")) or list(filters))
            self.filter = re.compile(r"\w+" + r"|\w+".join(list(filters)))
        else:
            regex = self._data.get("regex")
            if regex:
                self.filter = regex
                labels = self._data.get("label") or self._data.get("labels") or ["Any"]
                self.widget.filters.addItems(labels if isinstance(labels, list) else [str(labels)])
            else:
                self.widget.filters.addItem("All Files")

    def _conf_mode(self):
        mode = self._data.get("mode")
        vis = mode == self.Mode.Save
        self.widget.create_folder.setVisible(vis)
        self.widget.file_name.setVisible(vis)
        self._data["selection"] = self.Selection.Single if vis else self._data.get("selection")
        self.widget.openf.setText("Open" if not vis else "Save")


CLASS = FileDialog
VERSION = 0.1
TYPE = "window/callable"
NAME = "FBR"
