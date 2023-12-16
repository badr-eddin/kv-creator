import os.path
import pathlib
import pyautogui
import toml

from ....pyqt import QTreeWidget, Qt, QWidget, QVBoxLayout, QStackedWidget, loadUi, QPushButton, \
    QTreeWidgetItem, QIcon, QFileDialog, QFileInfo, QFileIconProvider, QSize, QPoint
from ....utils import import_, theme, hex2rgba, settings, set_layout, debug, bald, scroller


class StructureWidget(QTreeWidget):
    def __init__(self, parent, on_click=None):
        super(StructureWidget, self).__init__(parent)
        self.on_click = on_click

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHeaderHidden(True)
        # self.setEnabled(False)
        self.clicked.connect(self._clicked)  # Type: ignore

        self.select(True)

    def select(self, v=False):
        if v:
            c = theme('border_c', False)
            bg = "transparent"
        else:
            c = theme('primary_c', False)
            bg = f"rgba{hex2rgba(c[1:], 50)}"

        self.setStyleSheet("QTreeWidget{" f"background: {bg}; border: 1px solid {c};" "}")

    def _clicked(self):
        if self.on_click:
            self.on_click(self)


class ProjectCreator(QWidget):

    def __init__(self, main=None):
        super().__init__(None)
        self.main = main
        self.tab_unselected = f"background: #13181E; border: none; border-left: 2px solid transparent"
        self.tab_selected = f"background: #0D1117; border: none; border-left: 2px solid #32926F"
        self.added_resources = []
        self.btn_anim = None
        self.btn_anim2 = None
        self.current_btn = None, (0, 0)
        self.added = []
        self.structures = settings.pull("structures")

        self.widget = loadUi(import_("ui/project_creator.ui", 'io'))
        self.layout_: QVBoxLayout = set_layout(self, QVBoxLayout)
        self.stack: QStackedWidget = self.widget.stack
        self.responsive = settings.pull("kivy/responsive")

        self.buttons: [QPushButton] = [
            self.widget.btn1,
            self.widget.btn2,
            self.widget.btn3,
            self.widget.btn4,
            self.widget.btn5
        ]

        debug("no project was found !", _c="w")

        self.init()
        self.load_primaries()
        self.load_structures()

    def init(self):
        bald(self)

        self.layout_.addWidget(self.widget)
        self.restore()
        self.setWindowTitle("KivyCreator: New Project")

        for btn in self.buttons:
            btn.clicked.connect(self.navigate)

        self.buttons[0].click()

        scroller(self.widget.perms, self.main)
        scroller(self.widget.rcc, self.main)

        self.widget.cancel.clicked.connect(self.close)
        self.widget.rem_rcc.clicked.connect(self._remove_rcc)
        self.widget.add_rcc.clicked.connect(self._add_rcc)
        self.widget.create.clicked.connect(self._create_project)
        self.widget.open_proj.clicked.connect(self._open_project)
        self.widget.sizes.currentTextChanged.connect(self._setup_win_size)
        self.widget.kw_width.valueChanged.connect(self._setup_win_size)
        self.widget.kw_height.valueChanged.connect(self._setup_win_size)

        self.widget.sizes.addItems(self.responsive.keys())

        mx, mn = settings.pull("kivy/responsive-max"), settings.pull("kivy/responsive-min")

        self.widget.kw_width.setMinimum(mn[0])
        self.widget.kw_width.setMaximum(mx[0])
        self.widget.kw_height.setMinimum(mn[1])
        self.widget.kw_height.setMaximum(mx[1])

        self.widget.add_rcc.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.rem_rcc.setIcon(QIcon(import_("img/editors/actions/remove.png")))

        self.show()
        self._setup_win_size()

    def load_structures(self):
        tree: QTreeWidget = self.widget.structures

        self.structures.update({"Custom": None})

        for stc in sorted(self.structures.keys()):
            item = QTreeWidgetItem()
            item.setText(0, stc)
            tree.addTopLevelItem(item)

    def _remove_rcc(self):
        items: [QTreeWidgetItem] = self.widget.rcc.selectedItems()
        for item in items:
            item: QTreeWidgetItem
            path = item.data(0, Qt.ItemDataRole.UserRole)

            if path in self.added_resources:
                self.added_resources.remove(path)
            else:
                debug(f"resource '{path}' not in registered resources !", _c="w")

            self.widget.rcc.takeTopLevelItem(self.widget.rcc.indexOfTopLevelItem(item))

    def _add_rcc(self):
        dialog, plg = self.main.get_file_dialog()
        entry = os.path.expanduser("~")

        if plg:
            dialog = dialog(main=self.main, std=self.main.std)
            dialog.open_save_file(
                callback=self.__add_rcc,
                selection=dialog.Selection.Multi,
                encapsulate=pathlib.Path,
                target=dialog.Targets.Files,
                mode=dialog.Mode.Open,
                entry=entry
            )
        else:
            dialog = QFileDialog(self)
            paths = dialog.getOpenFileNames(self, directory=entry)

            paths = [pathlib.Path(path) for path in paths[0]]

            self.__add_rcc(paths)

    def __add_rcc(self, paths: [pathlib.Path]):
        for path in paths:
            if not path.is_file():
                debug(f"cannot add resources: '{path.name}' from '{path.parent.as_posix()}'", _c="w")
                continue

            if path.as_posix() in self.added_resources:
                debug(f"resource already exist: '{path.name}' from '{path.parent.as_posix()}'", _c="w")
                continue

            item = QTreeWidgetItem()
            item.setText(0, path.name)
            item.setIcon(0, QFileIconProvider().icon(QFileInfo(path.as_posix())))
            item.setData(0, Qt.ItemDataRole.UserRole, path.as_posix())

            self.added_resources.append(path.as_posix())
            self.widget.rcc.addTopLevelItem(item)

    def _setup_win_size(self):
        scene_size = self.widget.kw_scene.size()
        scene_size = [scene_size.width(), scene_size.height()]
        resp_max = settings.pull("kivy/responsive-max")

        if self.widget.custom_res.isChecked():
            reso = [self.widget.kw_width.value(), self.widget.kw_height.value()]
        else:
            text = self.widget.sizes.currentText()
            reso = self.responsive.get(text) or list(settings.pull("kivy/window-resolution").values())

        placeholder_reso = [
            (reso[0] * scene_size[0]) // resp_max[0],
            (reso[1] * scene_size[1]) // resp_max[1],
        ]

        self.widget.kw.setFixedSize(QSize(*placeholder_reso))

    def _create_project(self):
        data = {
            "project": {},
            "package": {},
            "resources": {},
            "configuration": {}
        }

        data["project"].update({
            "name": self.widget.project_name.text(),
            "author": self.widget.author_name.text(),
            "description": self.widget.project_desc.toPlainText().splitlines(False)
        })
        data["package"].update({
            "name": self.widget.package_name.text(),
            "domain": self.widget.package_domain.text(),
            "permissions": self._get_perms()
        })

        res = self.responsive.get(self.widget.sizes.currentText())
        res = res or list(settings.pull("kivy/window-resolution").values())

        if self.widget.custom_res.isChecked():
            res = [self.widget.kw_width.value(), self.widget.kw_height.value()]

        data["resources"].update({
            "paths": self.added_resources
        })

        data["configuration"].update({
            "resolution": res
        })

        root = pathlib.Path(os.path.join(self.widget.project_root.text() or ".", self.widget.project_name.text()))

        if root.parent.exists() and not root.exists():
            os.mkdir(root)

        kvc = os.path.join(root, settings.pull("#prefs/kvc"))

        with open(kvc, "w") as file:
            file.write(toml.dumps(data))

        self.open_project(root)

    def open_project(self, path):
        self.main.save_project_path(path)

        self.main.showMaximized()
        self.main.load_project(path)
        self.close()

    def _open_project(self):
        self.dialog = self.main.plugin("fbr")

        if self.dialog:
            self.dialog = self.dialog(main=self.main, std=self.main.std)
            self.dialog.setParent(None)
            self.dialog.open_save_file(
                callback=self.open_project,
                selection=self.dialog.Selection.Single,
                encapsulate=pathlib.Path,
                mode=self.dialog.Mode.Open,
                target=self.dialog.Targets.Dirs,
                custom_check=self._isit_kvc_project
            )

    def _isit_kvc_project(self, path: pathlib.Path):
        _ = self

        if not path.is_dir():
            return False

        k = settings.pull("#prefs/kvc")
        x = k in os.listdir(path)

        if not x:
            debug(f"not kivy project, open valid project or create new one ! probably '{k}' is missing .", _c="w")

        return x

    def _get_perms(self):
        li: QTreeWidget = self.widget.perms
        perms = []

        for i in range(0, li.topLevelItemCount()):
            item = li.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                perms.append(item.text(0))

        return perms

    def reset_tabs_style(self):
        for btn in self.buttons:
            btn.setStyleSheet(self.tab_unselected)

    def restore(self):
        w, h = self.widget.size().width(), self.widget.size().height()
        sw, sh = pyautogui.size()

        self.resize(QSize(w, h))
        self.move(QPoint(sw // 2 - w // 2, sh // 2 - h // 2))

    def load_primaries(self):
        debug("creating new project ...")

        for perm in settings.pull("kivy/perms"):
            item = QTreeWidgetItem()
            item.setText(0, perm)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            self.widget.perms.addTopLevelItem(item)

    def navigate(self):
        btn = self.sender()
        self.reset_tabs_style()
        btn.setStyleSheet(self.tab_selected)
        self.stack.setCurrentIndex(btn.property("index") or 0)
