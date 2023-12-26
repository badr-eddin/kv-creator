from .app_tip import AppTip
from ...pyqt import QWidget, loadUi, QGridLayout, QSize, QWindow
from ...utils import settings, import_, load_from_project, set_layout


class AppScene(QWidget):
    title = "None"
    path = ""
    editor = None
    index = -1

    def __init__(self, parent, main):
        super(AppScene, self).__init__(parent)
        self.main = main
        self.container = None
        self.tip = AppTip(self, main, self.index)
        self.widget = loadUi(import_("ui/scene.ui", 'io'))
        self.reso = (load_from_project("configuration", self.main.project_path) or {}).get("resolution")

    def index_is(self, ind):
        self.index = ind
        self.tip.index = ind

    def init(self, _, wid):
        set_layout(self, QGridLayout)

        window = QWindow.fromWinId(wid)  # Type: ignore
        window.setObjectName("cont-win")
        self.container = QWidget(self).createWindowContainer(window, self)

        self.widget.holder.layout().addWidget(self.container)
        self.layout().addWidget(self.widget)
        self.tip.on_fit_toggled.connect(self.setup_size)
        self.tip.load_tip()

    def setup_size(self, s):
        if not self.container:
            return

        def_ = settings.pull("kivy/window-resolution").values()
        psz = self.widget.size()

        if s:
            size = self.reso or def_
            scaling_factor = min(psz.width() / size[0], psz.height() / size[1])
            scaling_factor -= 0.02
            size = [
                int(size[0] * scaling_factor),
                int(size[1] * scaling_factor)
            ]

        else:
            size = self.reso or def_

        self.container.setFixedSize(QSize(*size))
