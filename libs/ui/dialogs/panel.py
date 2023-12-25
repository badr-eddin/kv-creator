from ...pyqt import QDockWidget, QIcon, Qt, QPoint, QSize, QPainter, QBrush, QRect
from ...utils import import_, theme


class CustomDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = import_("ui/dock""bar.ui")
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Warn: this is remove because of xterm
        self.createCustomTitleBar()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = self.size()
        head_height = 30
        f = 5
        bs = 0

        head_rect = QRect(QPoint(0, 0), QSize(size.width(), head_height + f))
        body_rect = QRect(QPoint(0, head_height - f), QSize(size.width(), size.height() - head_height + f))

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QBrush(theme("head_c")))
        painter.drawRoundedRect(head_rect, bs, bs)

        painter.setBrush(QBrush(theme("background_c")))
        painter.drawRect(body_rect)

        super(CustomDockWidget, self).paintEvent(event)

    def createCustomTitleBar(self):
        self.title.setObjectName("dockTitle")
        self.title.setStyleSheet("QPushButton{background: transparent; border: none;}")
        self.title.close_d.clicked.connect(self.close)
        self.title.dock_d.clicked.connect(self.undock)

        self.title.dock_d.enterEvent = lambda _: self.sic("-hover", btn=2)
        self.title.dock_d.leaveEvent = lambda _: self.sic(btn=2)

        self.title.close_d.enterEvent = lambda _: self.sic("-hover", btn=1)
        self.title.close_d.leaveEvent = lambda _: self.sic(btn=1)

        self.sic()
        self.setTitleBarWidget(self.title)

    def sic(self, k="", btn=0):
        if btn == 1 or btn == 0:
            self.title.close_d.setIcon(QIcon(import_(f"img/editors/actions/close{k}.png")))

        if btn == 2 or btn == 0:
            self.title.dock_d.setIcon(QIcon(import_(f"img/editors/actions/dock{k}.png")))

    def setWindowTitle(self, a0: str) -> None:
        self.title.title.setText(a0)
        super(CustomDockWidget, self).setWindowTitle(a0)

    def undock(self):
        self.setFloating(not self.isFloating())
