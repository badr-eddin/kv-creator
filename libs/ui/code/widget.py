from .editor import Editor
from ..dialogs import AppScene
from ...pyqt import QWidget, QFrame, QTabWidget, QVBoxLayout, QMimeData, QDragEnterEvent, QUrl, Qt
from ...utils import theme, set_layout, debug, comp_update

import magic
import psutil
import os
import pathlib


class EditorWidget(QWidget):
    ui = "body"
    ui_type = QFrame
    name = "editor"

    def __init__(self, parent, main):
        super(EditorWidget, self).__init__(parent)
        self.main = main
        self.editors = []
        self.opened_paths = {}
        self.widget = QTabWidget(self)

    def style_on_off(self, on=False):
        if on:
            k = f"1px solid {theme('border_2c', False)}"
        else:
            k = "none"

        self.widget.setStyleSheet("QStackedWidget{" f"border: {k};" "}")

    def config_window(self):
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.widget.setObjectName("editor-tab-widget")
        self.widget.setTabsClosable(True)
        self.widget.tabCloseRequested.connect(self.close_editor_tab)  # Type: ignore
        self.widget.currentChanged.connect(self._tab_changed)  # Type: ignore
        self.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.widget.tabBar().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.widget.setAcceptDrops(True)
        self.setAcceptDrops(True)
        self.style_on_off()
        self.widget.dropEvent = lambda e: self.dropped_from(e)

    def dropEvent(self, e):
        self.dropped_from(e)
        super(EditorWidget, self).dropEvent(e)

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data: QMimeData = event.mimeData()
        if mime_data.hasUrls():
            event.acceptProposedAction()

    def dropped_from(self, e):
        mime: QMimeData = e.mimeData()
        mag = magic.Magic(True)
        if mime.hasUrls():
            for url in mime.urls():
                url: QUrl
                mmt = mag.from_file(url.path())
                if mmt.startswith("text") or "svg" in mmt:
                    self.add_editor(pathlib.Path(url.path()).read_text(), url.path())

    def search(self):
        self.main.search_in(self.widget.currentWidget())

    def close_editor_tab(self, index):
        tab = self.widget.widget(index)

        self.main.editor_closed(tab)

        if self.widget.count() == 1:
            self.style_on_off()

        if isinstance(tab, Editor):
            if not getattr(tab, "saved"):
                func = self.main.element("inform.inform")
                func("Changes have been made but haven't been saved. Would you like to save them now?", "Editor",
                     on_accept=lambda d: self._save_confirmed(tab, index, d),  # Type: ignore
                     on_deny=lambda d: self._single_deny(index, d, tab), sts=0)
            else:
                self.widget.removeTab(index)
                self.super_done()
                if tab.path in self.opened_paths:
                    self.opened_paths.pop(tab.path)

        elif hasattr(tab, "pid"):
            self.widget.removeTab(index)

            # remove tab before you kill the process, because it might be null
            if tab.pid > 0:
                process = psutil.Process(tab.pid)
                process.kill()
                process.terminate()
                debug(f"process: '{process.pid}' is dead °^° .")
        else:
            self.widget.removeTab(index)

    def _single_deny(self, index, d, tab):
        self.widget.removeTab(index)
        d.close()

        if tab in self.editors:
            self.editors.remove(tab)

        if getattr(tab, "path") in self.opened_paths:
            self.opened_paths.pop(getattr(tab, "path"))

    def add_external_window(self, wid, title="Kivy", path=None, pid=0, kwargs=None):
        debug("adding external window ... ")
        scene = AppScene(self.widget, self.main)
        scene.pid = pid
        scene.title = title
        scene.path = path
        scene.editor = (kwargs or {}).get("editor")
        scene.init(path, wid)
        index = self.widget.addTab(scene, title)
        self.widget.setCurrentWidget(scene)

        self.main.on("external_window_tab_created", {"editor": self.widget.widget(index)})

    def _save_confirmed(self, tab, index, _d, c=True):
        tab.save_content(index)
        _d.close()
        self.super_done()
        if c:
            self.widget.removeTab(index)
            if tab.path in self.opened_paths:
                self.opened_paths.pop(tab.path)

        if tab in self.editors:
            self.editors.remove(tab)

    def _save(self):
        editor = self.widget.currentWidget()
        if isinstance(editor, Editor):
            editor.save_content(self.widget.currentIndex())  # Type: ignore

    def super_done(self):
        self.main.element("inspector.done")()
        self.main.element("p-editor.done")()
        self.main.element("imports.done")()

        kvf = os.path.basename(str(getattr(self.widget.currentWidget(), "path", "0"))).endswith(".kv")

        self.main.element("inspector").setEnabled(kvf)
        self.main.element("p-editor").setEnabled(kvf)
        self.main.element("imports").setEnabled(kvf)

    def open_file(self):
        dialog, plg = self.main.get_file_dialog()

        if plg:
            dialog = dialog(main=self.main, std=self.main.std)
            dialog.open_save_file(
                callback=self._add_editor_on_open,
                selection=dialog.Selection.Single,
                encapsulate=pathlib.Path,
                mode=dialog.Mode.Open,
                custom_check=self._check_file_mimetype,
                entry=self.main.project_path
            )
        else:
            dialog = dialog(self)
            path_ = dialog.getOpenFileName(directory=self.main.project_path)

            if path_[0]:
                path_ = path_[0]

                if self._check_file_mimetype(path_):
                    self._add_editor_on_open(pathlib.Path(path_))

    def _add_editor_on_open(self, path: pathlib.Path):
        if path:
            self.add_editor(path.read_text(), path.as_posix())

    def point_under(self, *args):
        editor = self.editor()
        if editor:
            editor.point_under(*args)

    def editor(self, k=None, d=None) -> Editor | QWidget | int:
        if isinstance(self.widget.currentWidget(), Editor):
            if not k:
                return self.widget.currentWidget()

            return getattr(self.widget.currentWidget(), str(k), d)
        return 0

    @staticmethod
    def _check_file_mimetype(path: str):
        try:
            pathlib.Path(path).read_text()
            return True
        except Exception as e:
            _ = e
            debug(f"{os.path.basename(path)}: expected 'text' got 'bytes'", _c="e")

    def _tab_changed(self, index: int):
        widget = self.widget.widget(index)
        if isinstance(widget, Editor):
            widget = widget
        elif isinstance(widget, AppScene):
            widget = widget.editor
        else:
            widget = None

        if widget:
            os.environ["building"] = "1"
            self.super_done()
            comp_update(widget.text(), widget.path)

        self.main.on("tab_changed", {"editor": widget})

    def on_main_close(self, mn):
        unsaved = []
        for editor in self.editors:
            if not editor.saved:
                unsaved.append(editor)

        if unsaved:
            mn.close_win = False
            func = self.main.element("inform.inform")
            func("Changes have been made but haven't been saved. Would you like to save them now?", "Editor",
                 on_accept=lambda d: self._save_all(d, unsaved), on_deny=lambda d: self._deny(d), sts=0)
        else:
            self._deny(mn)

    def _save_all(self, d, un):
        for ed in un:
            self._save_confirmed(ed, self.widget.indexOf(ed), d, False)

        self._deny(d)

    def _deny(self, d=None):
        self.main.super_close()
        if d:
            d.close()

    def add_editor(self, content="", path=None):
        if path in self.opened_paths:
            self.widget.setCurrentIndex(self.opened_paths.get(path))
            return

        debug(f"create new tab '{path or 'anonymous'}'")

        content = content if isinstance(content, str) else ""
        ed = Editor(self, self.main, self.widget)
        ed.reload = False
        ed.setText(content)
        ed.saved = True
        ed.set_path(path)
        index = self.widget.addTab(ed, os.path.basename(path) if path else "New Tab")
        ed.index = index

        self.style_on_off(True)
        self.editors.append(ed)
        self.widget.setTabToolTip(ed.index, path or "")
        self.widget.setCurrentWidget(ed)
        self.opened_paths.update({path: index})

        self.main.on("editor_tab_created", {"editor": self.widget.widget(index)})

    @staticmethod
    def get_text_editor(*args, path=""):
        ed = Editor(*args)
        ed.reload = False
        ed.index = -1
        ed.saved = True
        ed.set_path(path)
        return ed

    def initialize(self, _p):
        parent = _p or self.parent()
        parent.layout().addWidget(self)
        self.config_window()
