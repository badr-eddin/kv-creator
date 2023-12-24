from .dialog import DraggableFrame
from ...pyqt import loadUi, QVBoxLayout, pyqtSignal, QIcon
from ...utils import import_, set_layout, theme


class AppTip(DraggableFrame):
    on_fit_toggled = pyqtSignal(bool)

    def __init__(self, parent):
        super(AppTip, self).__init__(parent)
        self.target_widget = self
        self.fit_toggled = False
        self.widget = loadUi(import_("ui/kivy-app-tip.ui", 'io'))
        set_layout(self, QVBoxLayout, (0, 12, 0, 0)).addWidget(self.widget)
        self.close()
        self.setFixedWidth(102)
        self.setFixedHeight(46)
        self.widget.fit.clicked.connect(self.fit_percentage)
        self.widget.fit.setObjectName("bar-button")
        self.widget.break_app.setObjectName("bar-button")
        self.widget.reload.setObjectName("bar-button")
        self.widget.fit.setIcon(QIcon(import_("img/dialog/fit.png")))
        self.widget.break_app.setIcon(QIcon(import_("img/dialog/break.png")))
        self.widget.reload.setIcon(QIcon(import_("img/dialog/reload.png")))

    def fit_percentage(self):
        self.widget.fit.setStyleSheet(
            f"background: {theme('background_c', False) if self.fit_toggled else theme('primary_c', False)}")
        self.fit_toggled = not self.fit_toggled
        self.on_fit_toggled.emit(self.fit_toggled)

    def load_tip(self):
        self.move(self.parent().cursor().pos())
        self.show()
        self.raise_()
