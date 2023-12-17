import os.path
import re

from jedi.api.classes import Name

from ..dialogs import CustomDockWidget
from ...utils import import_, settings
from ...kivy import KivyAnalyser
from ...pyqt import QFrame, QIcon, loadUi, QTreeWidgetItem, QTreeWidget, QTimer, QComboBox


class ActionsEditor(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    name = "actions"

    def __init__(self, parent, main):
        super(ActionsEditor, self).__init__(parent)
        self.main = main
        self.analyser = KivyAnalyser(self)
        self.apps_loaded_from_src = {}
        self.app_script = None
        self.items_map = {}

        self.src_valid = False

        self.src_info_timer = QTimer(self)
        self.actions = settings.pull("kivy/actions")
        self.widget = loadUi(import_("ui/actions-editor.ui", 'io'))
        self.setWidget(self.widget)

    def initialize(self, _):
        self.main.dock_it(self, "ra")
        self.setWindowTitle("Actions Editor")
        self.src_info_timer.setSingleShot(True)

        # configuring elements
        self.widget.actions_sel.addItems(list((self.actions or {}).keys()))

        self.widget.add_action.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.minus_action.setIcon(QIcon(import_("img/editors/actions/remove.png")))

        self.widget.add_action.clicked.connect(self.add_action)
        self.widget.src.textChanged.connect(self.src_text_changed)
        self.widget.src.returnPressed.connect(self.src_text_changed)
        self.src_info_timer.timeout.connect(self._check_src)

    def add_action(self):
        app_cls: Name = self.apps_loaded_from_src.get(self.widget.app.currentText())

        if not app_cls:
            return

        tree: QTreeWidget = self.widget.action_s
        item = QTreeWidgetItem()

        item.setText(0, self.widget.actions_sel.currentText())

        combo_func = QComboBox(tree)

        for dn in app_cls.defined_names():
            dn: Name
            # if not re.match(r"__.*.__", dn.name):
            combo_func.addItem(dn.name)

        self.items_map.update({
            id(item): {
                "widget": combo_func,

            }
        })

        tree.addTopLevelItem(item)
        tree.setItemWidget(item, 1, combo_func)

    def _check_src(self):
        text: str = str(self.widget.src.text())

        if not text.endswith(".py"):
            self.main.element("msg.pop")(f"'{os.path.basename(text)}' not a python file !", 2000)
            return

        if not os.path.isfile(text):
            self.main.element("msg.pop")(f"'{os.path.basename(text)}' not a file | not exist !", 2000)
            return

        self.analyser.on_finish.connect(self._looking_for_app_finished)
        self.analyser.trigger(text, KivyAnalyser.TARGETS.KivyApp)

    def _looking_for_app_finished(self, apps, script):
        self.widget.app.clear()
        self.widget.app.addItems(apps.keys())

        self.apps_loaded_from_src = apps
        self.app_script = script

    def src_text_changed(self):
        self.src_info_timer.start(500)

