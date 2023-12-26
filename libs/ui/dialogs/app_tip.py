from .dialog import DraggableFrame
from ...pyqt import loadUi, QVBoxLayout, pyqtSignal, QIcon, QPoint
from ...utils import import_, set_layout, theme


class AppTip(DraggableFrame):
    on_fit_toggled = pyqtSignal(bool)
    index = -1

    def __init__(self, parent, main, index):
        super(AppTip, self).__init__(parent)
        self.target_widget = self
        self.main = main
        self.visible = False
        self.index = index
        self.fit_toggled = False
        self.widget = loadUi(import_("ui/kivy-app-tip.ui", 'io'))

        self.close()
        self.double_clicked(None)

        self.setProperty("type", "container")

        self.widget.fit.setObjectName("bar-button")
        # self.widget.reload.setObjectName("bar-button")
        self.widget.break_app.setObjectName("bar-button")

        self.widget.fit.clicked.connect(self.fit_percentage)
        self.widget.break_app.clicked.connect(self.break_app)

        self.mouseDoubleClickEvent = lambda _: self.double_clicked(_)

        self.widget.fit.setIcon(QIcon(import_("img/dialog/fit.png")))
        # self.widget.reload.setIcon(QIcon(import_("img/dialog/reload.png")))
        self.widget.break_app.setIcon(QIcon(import_("img/dialog/break.png")))

        set_layout(self, QVBoxLayout, (2, 12, 2, 2)).addWidget(self.widget)

    def double_clicked(self, _):
        w = 104
        if self.visible:
            self.widget.close()
            h = 20
        else:
            self.widget.show()
            h = 50

        self.setFixedWidth(w)
        self.setFixedHeight(h)
        self.visible = not self.visible

    def fit_percentage(self):
        self.widget.fit.setStyleSheet(
            f"background: {theme('background_c', False) if self.fit_toggled else theme('primary_c', False)}")
        self.fit_toggled = not self.fit_toggled
        self.on_fit_toggled.emit(self.fit_toggled)

    def break_app(self):
        self.main.element("editor.close_editor_tab")(self.index)

    def load_tip(self):
        self.move(QPoint(2, 2))
        self.show()
        self.raise_()
