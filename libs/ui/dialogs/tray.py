from ...pyqt import QWidget, QFrame, QLabel, QPushButton, QHBoxLayout, QColor, QSize, QIcon, \
    QPoint, QPainter, Qt, QRect, QPropertyAnimation, QTimer
from ...utils import theme, import_

import re


class Messenger(QWidget):
    default_size = [200, 35]
    ui = "body"
    ui_type = QFrame
    name = "msg"

    class POS:
        LEFT = 1
        RIGHT = 2

    def __init__(self, _=None, main=None):
        super(Messenger, self).__init__(main)
        self.main = main
        self.field = QLabel(self)
        self.__pos = self.POS.RIGHT
        self.close_btn = QPushButton(self)
        self.close_btn.setMaximumSize(QSize(25, 25))
        self.close_btn.leaveEvent = lambda _: self._close_leave()
        self.close_btn.enterEvent = lambda _: self._close_enter()
        self.close_btn.clicked.connect(self.close_)  # Type: ignore
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 2, 2, 2)
        lay.addWidget(self.field)
        lay.addWidget(self.close_btn)
        self.setLayout(lay)
        self.wbb = QColor(theme("head_c"))
        self._aim = QPropertyAnimation(self, b"pos")  # Type: ignore
        self.pw = self.parent().size().width()
        self.ph = self.parent().size().height()
        self.x = self.pw - self.default_size[0] - 10
        self.y = self.ph - self.default_size[1] - 10
        self.__closable__ = False
        self.resize(QSize(*self.default_size))
        self.move(QPoint(self.x, self.ph + self.default_size[1]))
        self.setStyleSheet("background: transparent; border: none;")

    def initialize(self, _p=None):
        self.restore()
        self._close_leave()
        self.close()

    def _close_enter(self):
        self.close_btn.setIcon(QIcon(import_("img/editors/actions/close-hover.png")))

    def _close_leave(self):
        self.close_btn.setIcon(QIcon(import_("img/editors/actions/close.png")))

    def close_(self):
        self._aim.setEndValue(QPoint(self.x, self.ph + self.default_size[1]))
        self._aim.setDuration(200)
        self._aim.start()

    def _pop(self):
        if self.__pos == self.POS.RIGHT:
            self.x = self.pw - self.default_size[0] - 10
            self.move(QPoint(self.x, self.ph + self.default_size[1]))
        else:
            self.x = 10
            self.move(QPoint(self.x, self.ph + self.default_size[1]))

        self.y = self.ph - self.default_size[1] - 10
        self.show()
        self._aim.setEndValue(QPoint(self.x, self.y))
        self._aim.setDuration(200)
        self._aim.start()

    def set_pos(self, p):
        self.__pos = p

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.__closable__:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.default_size
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.wbb)
        painter.drawRoundedRect(QRect(0, 0, w, h), 4, 4)

        super(Messenger, self).paintEvent(event)

    def pop(self, msg, delay=-1, parent=None):

        if parent:
            self.setParent(parent)

        self.default_size[0] = int(len(msg) * 7.5 + 35)
        self.restore()
        self._pop()
        self.resize(QSize(*self.default_size))
        self.field.setText(re.sub(r"(\\+)", r"\\", str(msg)))
        if delay <= 0:
            self.__closable__ = True
            self.close_btn.setVisible(True)
        else:
            self.__closable__ = False
            self.close_btn.setVisible(False)
            QTimer(self).singleShot(delay, self.close)  # Type: ignore
        self.raise_()
        self.main.on_resize(self.restore)

    def restore(self, v=0):
        self.pw = self.parent().size().width()
        self.ph = self.parent().size().height()

        if self.__pos == self.POS.RIGHT:
            self.x = self.pw - self.default_size[0] - 10
        else:
            self.x = 10

        self.y = self.ph - self.default_size[1] - 10
        point = QPoint(self.x, self.y)
        if v is True:
            return point

        self.move(point)
        self.raise_()
