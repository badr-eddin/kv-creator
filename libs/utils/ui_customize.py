import pyautogui
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QScrollBar, QWidget

from .settman import theme


def set_layout(widget, layout, m=(0, 0, 0, 0), sp=2):
    """
    :param widget:
    :param layout:
    :param m: margins, default to (0, 0, 0, 0)
    :param sp:
    :return: layout
    """
    layout = layout(widget)
    layout.setSpacing(sp)
    layout.setContentsMargins(*m)
    widget.setLayout(layout)
    return layout


def find_in(_w, _e, _t):
    return _w.findChild(_t, _e)


def bald(obj, m=True):
    obj.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    obj.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    if m:
        obj.setWindowModality(Qt.WindowModality.ApplicationModal)


def restore(obj, w=300, h=100, sz=None):
    if isinstance(w, QSize):
        w, h = w.width(), w.height()

    if isinstance(h, QSize):
        w, h = h.width(), h.height()

    pw, ph = sz or pyautogui.size()

    obj.setFixedSize(w, h)

    w = pw // 2 - w // 2
    h = ph // 2 - h // 2

    obj.move(QPoint(int(w), int(h)))

    return [int(w), int(h)]


def set_shadow(w, offset=None, br=50):
    if offset is None:
        offset = [0, 0]
    qe = QGraphicsDropShadowEffect()
    qe.setColor(theme("shadow_c"))
    qe.setXOffset(offset[0])
    qe.setYOffset(offset[1])
    qe.setBlurRadius(br)
    w.setGraphicsEffect(qe)


class scroller(QScrollBar):
    def __init__(self, parent, main):
        super(scroller, self).__init__(parent)
        self.target = parent
        self.main = main
        self.__timer = QTimer(self.target)

        self.__timer.singleShot(200, self._setup)

    def _setup(self):
        self.target.resizeEvent = lambda _: self._restore()

        self.valueChanged.connect(self._on_scroll)
        self.target.verticalScrollBar().valueChanged.connect(self._tar_scroll)
        self.target.verticalScrollBar().rangeChanged.connect(self._range_fy)
        self.__timer.singleShot(20, self._restore)
        self.__timer.singleShot(2000, self._restore)
        self.main.on_resize(self._restore)

    def _range_fy(self):
        self.setMaximum(self.target.verticalScrollBar().maximum())

    def _restore(self, *_):
        w, m = 15, 1

        self.resize(QSize(w, self.target.size().height() - m * 2))
        self.move(QPoint(self.target.size().width() - w - m, m))

        self.show()
        self.raise_()

    def _on_scroll(self, value):
        self.target.verticalScrollBar().setValue(value)

    def _tar_scroll(self, value):
        self.setValue(value)


def resize_event(tar: QWidget, callback):
    tar.resizeEvent = lambda _: callback()
