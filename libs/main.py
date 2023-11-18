import os
import pathlib
import random
import re
import shutil
import sys
import tempfile
import zipfile

import toml

from .ui import COMPONENTS, PCreator
from .utils import *
from .utils import plugins_namespace as std


class Action(QAction):
    def __init__(self, parent=None, text="", on_trigger=None, dock=None):
        super(Action, self).__init__(parent)
        self.setText(text)
        self.on_trigger = on_trigger
        self.dock = dock
        self.triggered.connect(self.__tr)  # Type: ignore

    def __tr(self, ch):
        if self.on_trigger:
            self.on_trigger(ch, self.dock)


class Button(QPushButton):
    def __init__(self, parent=None, text="", on_click=None, icon=None, editor=None):
        super(Button, self).__init__(parent)
        self.setText("")
        self.setToolTip(text)
        self.setFixedSize(QSize(25, 25))
        self.setIcon(icon)
        self.on_click = on_click
        self.editor = editor
        self.clicked.connect(self.__tr)  # Type: ignore

    def __tr(self):
        if self.on_click:
            self.on_click(self)


class Creator(QMainWindow):
    PROJECT_FILE = ".kvc"
    MAX_PLUGIN_SIZE = 1024 * 1024 * 15  # 15MB

    def __init__(self, parent=None, app=None, args=None):
        super(Creator, self).__init__(parent)
        self.widget = loadUi(import_("ui/main-editor.ui", 'io'))
        self.components = {}
        self.plugins = {}
        self.__themes = {}
        self.plugins_actions = {}
        self.env_args = args
        self.app = app
        self.proc = pathlib.Path(os.path.join(os.path.expanduser("~"), ".kvc-project"))
        self.project_path = ""
        self._plugins = {}
        self.editor_functions = {}
        self.functions_co = {}
        self.ui_plugins = {}
        self.editors = []
        self.close_win = True
        self.close_temp = False
        self.std = std
        # self.act_hand = Handler(self)
        self.buttons = Buttons(self)
        self.on_main_close = True
        self.menu = None
        self.ptr = None
        self.__on_mouse_move__ = []
        self.__on_size_change__ = []
        self.tmp = tempfile.mktemp()

        self.config_window()
        self.load_plugins()
        self.load_theme(self.app)
        self.get_project()
        self.load_elements()
        self.load_actions()
        self.load_editors()
        self.build_components_menu()

        self.test()

    # *****************************

    def mouseMoveEvent(self, a0):
        for func in self.__on_mouse_move__:
            func(a0)
        super(Creator, self).mouseMoveEvent(a0)

    def resizeEvent(self, a0: QResizeEvent):
        for fun in self.__on_size_change__:
            if callable(fun):
                fun(self)

        super(Creator, self).resizeEvent(a0)

    def closeEvent(self, a0):
        def _close_callbacks(cb):
            for o in self.components:
                _o = self.components.get(o)
                if hasattr(_o, cb):
                    getattr(_o, cb)(self)

        if self.on_main_close:
            _close_callbacks("on_main_close")

        if self.close_win:
            self.close_win = True

            if not self.close_temp:
                _close_callbacks("final_main_close")

                if os.path.exists(self.tmp):
                    shutil.rmtree(self.tmp)

                settings.push("themes", {"System": " "})
                settings.push("themes-colors", {})
            super(Creator, self).closeEvent(a0)

        else:
            a0.ignore()

    # *****************************
    def test(self):
        pass

    def restart(self):
        pass

    def element(self, k):
        return self.buttons.get_obj(k)

    def load_elements(self):
        for com in COMPONENTS:
            debug("loading", '"' + com.__name__ + '"', "...")
            if com.ui == "$":
                par = self
            else:
                par = self.widget.findChild(com.ui_type, com.ui)  # component parent
            component = com(par, self)
            self.components.update({(com.name if hasattr(com, "name") else com.__name__).lower(): component})
            component.initialize(par)

    def build_components_menu(self):
        menu = QMenu(self)

        for nm in self.components:
            if isinstance(self.components[nm], QDockWidget):
                dock: QDockWidget = self.components[nm]
                action = Action(self, dock.windowTitle(), self._co_clicked, dock)
                dock.visibilityChanged.connect(action.setChecked)  # Type: ignore
                action.setCheckable(True)
                action.setChecked(not dock.isHidden())
                menu.addAction(action)

        self.menu = menu

    def check_deps(self):
        required = []

        for v in settings.pull("-install/required"):
            v = settings.pull(v)
            if not shutil.which(v):
                required.append(os.path.basename(v))

        if required:
            self.element("msg.pop")(f"requirements: {tuple(required)} not found ! "
                                            f"some functions wouldn't work properly .")

    def load_plugins(self):
        loader = PLoader(self, self._load_plugin)
        loader.load()

    def load_theme(self, app=None):
        app = app or self.app
        user_thm = settings.pull("-theme")
        themes = settings.pull("themes")

        if not themes and not user_thm:
            return

        if not themes.get(user_thm):
            return

        _theme = themes[user_thm]

        app.setStyleSheet(load_style(_theme))

    def _load_plugin(self, plugin):

        if plugin.TYPE == "window/callable":
            obj = plugin.CLASS

        elif plugin.TYPE == "window/initiate":
            target = self.widget.findChild(plugin.CLASS.ui_type, plugin.CLASS.ui)
            obj = plugin.CLASS(parent=target, main=self, std=std)

        elif plugin.TYPE == "window/editor":
            obj = plugin
            self.editors.append(obj)

        elif plugin.TYPE == "theme/qss":
            obj = plugin.CLASS()
            _theme = obj.load(self)

            themes = settings.pull("themes")
            themes_c = settings.pull("themes-colors")

            themes.update({
                obj.name: _theme
            })

            if hasattr(obj, "colors"):
                themes_c.update({obj.name.lower().replace(" ", ""): obj.colors})

            settings.push("themes-colors", themes_c)
            settings.push("themes", themes)

        else:
            obj = plugin.CLASS

            ui, type_ = plugin.TYPE.split("/")

            if not self.ui_plugins.get(ui):
                self.ui_plugins[ui] = {}

            if not self.ui_plugins[ui].get(type_):
                self.ui_plugins[ui][type_] = []

            self.ui_plugins[ui][type_].append(obj)

        # *******************************
        self.functions_co.update({plugin.NAME: obj})

        for f in getattr(obj, "FUNCTIONS", []):
            if not self.editor_functions.get(f):
                self.editor_functions[f] = []

            self.editor_functions[f].append(plugin.NAME)

        if hasattr(obj, "ACTIONS"):
            self.plugins_actions.update({plugin.CLASS: getattr(obj, "ACTIONS", {})})
        # *******************************

        self.plugins.update({plugin.NAME.lower(): obj or plugin})
        self._plugins.update({plugin.NAME.lower(): plugin})

    def load_actions(self):
        actions = settings.pull("-actions")
        shortcuts = []

        for act in actions:
            shortcut = actions[act].get("shortcut") or ""
            args = actions[act].get("args") or []

            if shortcut in shortcuts:
                debug(f"action '{act}' -> shortcut already defined ! ignore it instead .", _c="e")
                continue

            func = self

            shortcuts.append(shortcut)

            fns = actions[act].get("function").split(".")
            for fn in fns:
                patt = re.compile(r".*%(\d+)$")
                index = patt.findall(fn)
                last = fns[-1] == fn

                if index:
                    index = int(index[0])

                    fn = fn.replace(f"%{index}", "")

                if not hasattr(func, fn):
                    debug(f"action '{act}' -> has invalid function !", _c="e")
                    break

                func = getattr(func, fn)

                if index:
                    if last:
                        fnc = func
                        func = lambda *_: fnc(*args[index-1])
                    else:
                        func = func(*args[index-1])

            if func is self:
                continue

            if not callable(func):
                debug(f"action '{act}' -> function not callable", _c="e")
                continue

            self.add_action(shortcut, func)

    def load_editors(self):
        for editor in self.editors:
            btn = Button(
                self,
                editor.NAME,
                self._launch_editor,
                QIcon(import_(editor.CLASS.ICON)),
                editor.CLASS
            )
            self.widget.plugins.layout().addWidget(btn)
        self.widget.plugins.layout().addItem(SPItem())

    # *****************************
    def install_plugin(self):
        dialog, plg = self.get_file_dialog()

        if plg:
            paths = []

        else:
            dialog = QFileDialog(self)
            paths = dialog.getOpenFileNames(self, filter="*.zip")

        self._install(paths)

    def _install(self, paths):
        self.on("start_install_plugin", {"path": paths})

        for path in paths[0]:
            name = os.path.basename(path)
            if os.path.exists(path):
                if os.path.getsize(path) <= self.MAX_PLUGIN_SIZE:

                    if not zipfile.is_zipfile(path):
                        debug(f"plugin.install: '{name}' not a zip file !", _c="e")
                        return

                    try:
                        tmp = os.path.join(self.tmp, name.split(".")[0])

                        with zipfile.ZipFile(path, 'r') as zf:
                            zf.extractall(self.tmp)

                        if not os.path.exists(tmp):
                            continue

                        kvc = os.path.join(tmp, ".kvc")
                        src = os.path.join(tmp, "src")

                        if os.path.isdir(src) and os.path.isfile(kvc):
                            data = toml.load(kvc)

                            entry = os.path.join(tmp, data.get("entry") or '')

                            if not os.path.isfile(entry):
                                continue

                            # move entry to plugins directory
                            dst = os.path.join(".", 'plugins')

                            if not os.path.exists(dst):
                                os.mkdir(dst)

                            _k = os.path.join(dst, os.path.basename(entry))
                            if os.path.exists(_k):
                                os.remove(_k)

                            entry = shutil.move(entry, dst)

                            # register data
                            if not os.path.exists(src):
                                continue

                            for rs in data.get("resources") or []:
                                rsp = os.path.join(src, rs)

                                if os.path.exists(rsp):
                                    _p = data.get('name')
                                    settings.set_blob(
                                        f"plugins{'/' + _p if _p else ''}/{rs}", open(rsp, "rb").read()
                                    )

                            PLoader(self, self._load_plugin).load_from_path(entry)

                    except Exception as e:
                        _ = e
                        debug(f"plugin.install: '{name}' unable to complete installation process!", _c="e")
                else:
                    debug(f"plugin.install: '{name}' "
                          f"exceeded maximum size '{self.MAX_PLUGIN_SIZE // 1024**2}MB'", _c="e")
            else:
                debug(f"plugin.install: '{name}' not exists ! probably deleted externally .", _c="e")

        self.restart()

        self.on("plugin_install_done", {"path": paths})

    def get_file_dialog(self):
        dialog = self.plugin("fbr")

        if dialog:
            return dialog, True
        return QFileDialog, False

    def on(self, func, kwargs=None):
        _f = "on_" + func
        funcs = self.editor_functions.get(_f)

        if not funcs:
            return

        for func in funcs:
            func = self.functions_co.get(func)

            if not func:
                return

            func = getattr(func, _f)

            if not func:
                return

            try:
                return func(kwargs)
            except Exception as e:
                debug(f"main::on('{_f}') {e}", _c="e")

    def show_this(self, nm, sts=True):
        tar = self.element(nm)

        if isinstance(tar, QDockWidget):
            tar.setVisible(sts)

    def _launch_editor(self, btn):
        cls = btn.editor(self, editor=self.element("editor"))
        tabs = self.element("editor.widget")
        index = tabs.addTab(cls, btn.toolTip())
        tabs.setCurrentIndex(index)

    def add_action(self, _sc, _fn, parent=None):
        action = QAction(parent or self)
        action.setShortcut(_sc)
        action.triggered.connect(_fn)  # Type: ignore
        self.addAction(action)

    def search_in(self, target):
        self.element("search.pop")(target)

    def on_mouse_move(self, func):
        if func not in self.__on_mouse_move__:
            self.__on_mouse_move__.append(func)

    def remove_mouse_move(self, func):
        if func in self.__on_mouse_move__:
            self.__on_mouse_move__.remove(func)

    def dock_it(self, _w, _p):
        position = {
            "ra": Qt.DockWidgetArea.RightDockWidgetArea, "la": Qt.DockWidgetArea.LeftDockWidgetArea,
            "ba": Qt.DockWidgetArea.BottomDockWidgetArea
        }
        pos = position.get(_p) or position.get(random.choice(list(position.keys())))
        _w.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(pos, _w)

    def super_close(self):
        self.close_win = True
        self.on_main_close = False
        self.close()

    def show_view_menu(self):
        if self.menu:
            self.menu.exec(self.cursor().pos())

    def save_project_path(self, path):
        with open(self.proc, "w") as file:
            file.write(path.as_posix() if isinstance(path, pathlib.Path) else str(path))

    def _co_clicked(self, checked, dock: QDockWidget):
        _ = self
        dock.setVisible(checked)

    def plugin(self, name, m=False):
        return (self.plugins if not m else self._plugins).get(name)

    def on_resize(self, fun):
        self.__on_size_change__.append(fun)

    def config_window(self):
        self.setCentralWidget(self.widget)
        self.resize(QSize(1200, 600))
        self.setMouseTracking(True)

        if os.path.exists(self.tmp):
            shutil.rmtree(self.tmp)

        os.mkdir(self.tmp)
        os.environ["tmp"] = self.tmp

        QTimer(self).singleShot(5000, self.check_deps)

    def load_project(self, proj):
        self.close_temp = False
        self.project_path = proj.as_posix()
        x = self.element("ptree.load_files_at")
        if x:
            x(proj.as_posix())

        self.showMaximized()

    def get_project(self):
        args = sys.argv

        if self.proc.is_file():
            project = pathlib.Path(self.proc.read_text().replace("\n", ""))
        else:
            project = pathlib.Path(args[0] if args else "")

        if project:
            if project.is_dir():
                if Creator.PROJECT_FILE in os.listdir(project.as_posix()):
                    self.load_project(project)
                    return

        self.ptr = PCreator(main=self)
        self.ptr.show()

        self.close_temp = True
        self.close()
