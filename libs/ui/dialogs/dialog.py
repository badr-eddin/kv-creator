from ...pyqt import QWidget, QPainter, QPen, QSize, QRect, QBrush, Qt, QPoint, \
    QCloseEvent, QPointF, QFrame, QPropertyAnimation
from ...utils import theme, bald, translate


class Dialog(QWidget):
    def __init__(self, parent, main):
        super(Dialog, self).__init__(parent)
        self.draw_frame = True
        self.x, self.y = 0, 0
        self.__use_anim = False
        self.p_fac = main.size().height()
        self._close = False
        self.pop_anim = QPropertyAnimation(self, b"pos")  # Type: ignore
        self.setObjectName("dialog")

    def paintEvent(self, a0):
        painter = QPainter(self)

        w = self.size().width()
        h = self.size().height()

        painter.setBrush(QBrush(theme("background_c")))
        painter.setPen(Qt.PenStyle.NoPen)

        rect = QRect(QPoint(0, 0), QSize(w, h))
        painter.drawRect(rect)

        painter.setBrush(QBrush(theme("head_c")))
        painter.setPen(Qt.PenStyle.NoPen)
        head = QRect(QPoint(0, 0), QSize(w, 30))
        painter.drawRect(head)

        super(Dialog, self).paintEvent(a0)

    def show_up(self, m=None):
        bald(self)

        if self.__use_anim:
            if m:
                self.move(QPoint(m.size().width() // 2 - self.size().width() // 2, - m.size().height()))
            self.pop_anim.setEndValue(QPoint(self.x, self.y))
            self.pop_anim.setDuration(200)
            self.pop_anim.start()
        self.show()
        self.raise_()

    def initialize(self, _p):
        pass

    def set_anim_on(self, on):
        self.__use_anim = on

    def closeEvent(self, a0: QCloseEvent):
        if not self._close and self.__use_anim:
            self.pop_anim.setEndValue(QPoint(self.x, self.y - self.p_fac))
            self.pop_anim.setDuration(200)
            self.pop_anim.start()
            QTimer(self).singleShot(1000, self.close)  # Type: ignore
            self._close = True
            a0.ignore()
        else:
            super(Dialog, self).closeEvent(a0)
            self._close = False


class DraggableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_dragging = False
        self.target_widget = parent
        self.offset = QPoint()
        self.setObjectName("drag-frame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.m_dragging = False
        self.m_last_position = QPointF()

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.m_dragging = True
            self.m_last_position = event.globalPosition()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.m_dragging:
            diff = event.globalPosition() - self.m_last_position
            mp = self.target_widget.pos()  # Type: ignore
            mvp = QPointF(mp.x(), mp.y()) + diff
            self.target_widget.move(int(mvp.x()), int(mvp.y()))  # Type: ignore
            self.m_last_position = event.globalPosition()
            event.accept()

