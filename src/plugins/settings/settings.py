import pathlib
import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import *
from importlib_metadata import distributions


class SettingsMan(QWidget):
    ICON = "plugins/settings/settings.png"

    def __init__(self, main, **kwargs):
        super(SettingsMan, self).__init__(kwargs.get("editor"))
        self.editor: QTabWidget = kwargs.get("editor")
        self.main = main
        self.std = main.std
        self.items = {}
        self.pips = list(distributions())
        self.pip_c = 0
        self.pip_t = QTimer(self)
        self.already_edited = False
        self.pip_installer = self.std.InLineInput(self, self.__pip_install, "package")
        self.widget = self.std.import_("plugins/settings/settings.ui")
        self.tabs: QTabWidget = self.widget.tabs
        self.kw_types = sorted(self.std.settings.pull("kivy/props-types") or [])

        self.conf_window()
        self.load()
        self.sort_all()

    # ********************************************

    def conf_window(self):
        self.std.set_layout(self, QVBoxLayout, (1, 1, 1, 1))

        self.widget.kv_keywords.itemChanged.connect(self.item_done_editing)
        self.widget.kv_classes.itemChanged.connect(self.item_done_editing)
        self.widget.kv_props.itemChanged.connect(self.item_done_editing)
        self.widget.pip_search.textChanged.connect(self.pip_search)

        self.widget.progress.setStyleSheet("background: transparent;")
        self.layout().addWidget(self.widget)
        self.conf_icons()
        self.conf_connect_buttons()

    def conf_connect_buttons(self):
        self.widget.browse_python.clicked.connect(lambda: self.browse4(self.widget.python_path, r".*python.*$"))
        self.widget.browse_xterm.clicked.connect(lambda: self.browse4(self.widget.xterm_path, r".*xterm.*$"))

        self.widget.add_prop.clicked.connect(self._add_prop)
        self.widget.minus_prop.clicked.connect(self._minus_prop)

        self.widget.add_keyw.clicked.connect(self._add_keyword)
        self.widget.minus_keyw.clicked.connect(self._minus_keyword)

        self.widget.add_cls.clicked.connect(self._add_cls)
        self.widget.minus_cls.clicked.connect(self._minus_cls)

        self.widget.pip_install.clicked.connect(self.pip_install)
        self.widget.save.clicked.connect(self.save)

    def conf_icons(self):
        self.widget.add_prop.setIcon(QIcon(self.std.import_("img/editors/actions/add.png")))
        self.widget.minus_prop.setIcon(QIcon(self.std.import_("img/editors/actions/remove.png")))
        self.widget.add_keyw.setIcon(QIcon(self.std.import_("img/editors/actions/add.png")))
        self.widget.minus_keyw.setIcon(QIcon(self.std.import_("img/editors/actions/remove.png")))
        self.widget.add_cls.setIcon(QIcon(self.std.import_("img/editors/actions/add.png")))
        self.widget.pip_install.setIcon(QIcon(self.std.import_("img/editors/actions/add.png")))
        self.widget.minus_cls.setIcon(QIcon(self.std.import_("img/editors/actions/remove.png")))
        self.widget.save.setIcon(QIcon(self.std.import_("img/editors/actions/save.png")))
        self.widget.browse_python.setIcon(QIcon(self.std.import_("img/editors/actions/browse.png")))
        self.widget.browse_xterm.setIcon(QIcon(self.std.import_("img/editors/actions/browse.png")))

    # ********************************************

    def browse4(self, w, r):
        dialog, plg = self.main.get_file_dialog()
        if plg:
            dialog = dialog(main=self.main, std=self.std)
            dialog.open_save_file(
                callback=w.setText,  # (path.as_posix()),
                selection=dialog.Selection.Single,
                # encapsulate=pathlib.Path,
                mode=dialog.Mode.Open,
                regex=re.compile(r)
            )
        else:
            dialog = QFileDialog(self)
            path = dialog.getOpenFileName(self)
            if re.compile(r).match(path[0]):
                w.setText(path[0])

    def item_done_editing(self, item):
        if self.already_edited:
            self.already_edited = False
            return

        self.already_edited = True
        if isinstance(item, QTreeWidgetItem):
            widget = self.widget.kv_props.itemWidget(item, 1)
            if widget:
                self.widget.kv_props.removeItemWidget(item, 1)
                item.setText(1, widget.currentText())

        item.setFlags(QTreeWidgetItem().flags())

        self.sort_all()

    def sort_all(self):
        self.widget.kv_props.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.widget.pips.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.widget.kv_keywords.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.widget.kv_classes.sortItems(0, Qt.SortOrder.AscendingOrder)

    def pip_search(self):
        text = self.widget.pip_search.text()
        tree: QTreeWidget = self.widget.pips

        for i in range(0, tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            vis = re.match(text, item.text(0)) or re.match(text, item.text(1))
            item.setHidden(not vis)

    # ********************************************

    def load(self):
        self._load_props()
        self._load_lst("classes", self.widget.kv_classes)
        self._load_lst("keywords", self.widget.kv_keywords)
        self._load_primary_data()
        self._load_pip_list()

    def _load_primary_data(self):
        pull = self.std.settings.pull
        self.main.on("load_default_prefs", {"pull": pull})
        self.widget.python_path.setText(pull("execution/python-interpreter"))
        self.widget.winx.setValue(pull("kivy/window-resolution/height"))
        self.widget.winy.setValue(pull("kivy/window-resolution/width"))
        self.widget.term_font.setCurrentText(pull("terminal/font-name"))
        self.widget.term_font_size.setValue(pull("terminal/font-size"))
        self.widget.xterm_path.setText(pull("terminal/-provider"))
        self.widget.autocomplete.setChecked(pull("user-prefs/autocomplete"))
        self.widget.display_icons.setChecked(pull("user-prefs/inspector-icons"))
        self.widget.embed_window.setChecked(pull("user-prefs/embed-kivy"))
        self.widget.point_errors.setChecked(pull("user-prefs/point-errors"))
        self.widget.detect_pos.setChecked(pull("user-prefs/detect-kivy-item"))
        self.widget.code_analyse.setChecked(pull("user-prefs/code-analyse"))
        self.widget.ed_font.setCurrentText(pull("editor/font-name"))
        self.widget.edf_size.setValue(pull("editor/font-size") or 5)

        self.widget.editor_theme.addItems(list((pull("editor-themes") or {}).keys()))
        self.widget.editor_theme.setCurrentText(pull("editor-theme"))

        self._setup_themes_settings()

    def _setup_themes_settings(self):
        ths = self.std.settings.pull("themes") or {}
        cut = self.std.settings.pull("-theme")

        self.widget.theme.addItems(ths.keys())
        if cut:
            self.widget.theme.setCurrentText(cut)
        elif ths:
            self.std.settings.push("-theme", list(ths.keys())[0])

    def _load_props(self):
        props = self.std.settings.pull("kivy/properties")
        self.widget.kv_props.clear()

        for p in props:
            item = QTreeWidgetItem()
            item.setText(0, p)
            item.setText(1, props[p])
            self.widget.kv_props.insertTopLevelItem(0, item)

        self.sort_all()
        self.std.scroller(self.widget.kv_props, self.main)

    def _load_lst(self, p, _l):
        cls = self.std.settings.pull(f"kivy/{p}")
        _l.clear()

        for c in cls:
            item = QTreeWidgetItem()
            item.setText(0, c)
            _l.addTopLevelItem(item)

        self.sort_all()
        self.std.scroller(_l, self.main)

    def _load_pip_list(self):
        self.widget.pip_search.setVisible(False)
        self.widget.progress.setValue(0)
        self.widget.progress.setMaximum(len(self.pips))
        self.widget.pips.clear()
        self.pip_t.timeout.connect(self._timer_load_pips)
        self.pip_t.start(1)

    def _timer_load_pips(self):
        if self.pip_c < len(self.pips):
            dist = self.pips[self.pip_c]
            self.pip_c += 1
            item = QTreeWidgetItem()
            item.setText(0, dist.metadata.get("name") or "dist")
            item.setText(1, str(dist.version) or "0.0.0")
            self.widget.pips.addTopLevelItem(item)
            self.widget.pips.scrollToItem(item)
            self.widget.progress.setValue(self.pip_c)
        else:
            self.pip_t.stop()
            self.sort_all()
            self.widget.pip_search.setVisible(True)
            self.widget.progress.setValue(0)
            self.pip_c = 0
            self.std.scroller(self.widget.pips, self.main)

    # ********************************************

    def _add_cls(self):
        k = "NewUserClass"
        item = QTreeWidgetItem()
        item.setText(0, k)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.widget.kv_classes.addTopLevelItem(item)
        self.widget.kv_classes.scrollToItem(item)

    def _minus_cls(self):
        items = self.widget.kv_classes.selectedItems() or []
        for item in items:
            self.widget.kv_classes.takeTopLevelItem(self.widget.kv_classes.indexOfTopLevelItem(item))
    # ********************************************

    def _add_prop(self):
        item = QTreeWidgetItem()
        item.setText(0, "NewProp")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        item_widget = QComboBox()
        item_widget.addItems(self.kw_types or [])
        self.widget.kv_props.addTopLevelItem(item)
        self.widget.kv_props.setItemWidget(item, 1, item_widget)
        self.widget.kv_props.scrollToItem(item)

    def _minus_prop(self):
        items = self.widget.kv_props.selectedItems()
        for item in items or []:
            self.widget.kv_props.takeTopLevelItem(self.widget.kv_props.indexOfTopLevelItem(item))

    # ********************************************

    def _add_keyword(self):
        k = "None"
        item = QTreeWidgetItem()
        item.setText(0, k)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.widget.kv_keywords.addTopLevelItem(item)
        self.widget.kv_keywords.scrollToItem(item)

    def _minus_keyword(self):
        items = self.widget.kv_classes.selectedItems() or []
        for item in items:
            self.widget.kv_keywords.takeTopLevelItem(self.widget.kv_keywords.indexOfTopLevelItem(item))

    # ********************************************

    def pip_install(self):
        pos = self.mapFromGlobal(self.cursor().pos())
        self.pip_installer.read_at(pos)

    def __pip_install(self, field):
        field.close()
        if not field.text():
            self.main.buttons.get_obj("msg.pop")("empty package name !")
            return

        add_term = self.main.buttons.get_obj("console.add_terminal")
        add_term(
            command=[self.std.settings.pull("execution/python-interpreter"), "-m", "pip", "install",
                     field.text()],
            wait=True,
            on_done=self._load_pip_list
        )

    # ********************************************
    def _collect_props(self):
        tree: QTreeWidget = self.widget.kv_props
        props = {}

        for i in range(0, tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            props.update({item.text(0): item.text(1)})

        return props

    def _collect_lists(self, lst: QTreeWidget):
        _ = self
        list_ = []

        for i in range(0, lst.topLevelItemCount()):
            list_.append(lst.topLevelItem(i).text(0))

        return list_

    def save(self):
        settings = [
            [self._collect_props(), "kivy/properties"],
            [self._collect_lists(self.widget.kv_classes), "kivy/classes"],
            [self._collect_lists(self.widget.kv_keywords), "kivy/keywords"],
            [self.widget.python_path.text(), "execution/python-interpreter"],
            [self.widget.winx.value(), "kivy/window-resolution/width"],
            [self.widget.winy.value(), "kivy/window-resolution/height"],
            [self.widget.term_font.currentText(), "terminal/font-name"],
            [self.widget.term_font_size.value(), "terminal/font-size"],
            [self.widget.xterm_path.text(), "terminal/-provider"],
            [self.widget.autocomplete.isChecked(), "user-prefs/autocomplete"],
            [self.widget.display_icons.isChecked(), "user-prefs/inspector-icons"],
            [self.widget.embed_window.isChecked(), "user-prefs/embed-kivy"],
            [self.widget.point_errors.isChecked(), "user-prefs/point-errors"],
            [self.widget.code_analyse.isChecked(), "user-prefs/code-analyse"],
            [self.widget.detect_pos.isChecked(), "user-prefs/detect-kivy-item"],
            [self.widget.theme.currentText(), "-theme"],
            [self.widget.ed_font.currentText(), "editor/font-name"],
            [self.widget.editor_theme.currentText(), "editor-theme"],
            [self.widget.edf_size.value(), "editor/font-size"]
        ]
        push = self.std.settings.push
        self.main.on("save_settings", {"push": push, "settings": settings, "self": self})

        for si in settings:
            push(si[1], si[0])


CLASS = SettingsMan
VERSION = 0.1
TYPE = "window/editor"
NAME = "settings"
