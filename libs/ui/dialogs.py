import re

from ..utils import *


class Dialog(QWidget):
    def __init__(self, parent, main):
        super(Dialog, self).__init__(parent)
        self.draw_frame = True
        self.x, self.y = 0, 0
        self.__use_anim = False
        self.p_fac = main.size().height()
        self._close = False
        self.pop_anim = QPropertyAnimation(self, b"pos")
        self.setObjectName("dialog")

    def paintEvent(self, a0):
        painter = QPainter(self)

        k = 2
        w = self.size().width() - k
        h = self.size().height() - k

        painter.setBrush(QBrush(theme("background_c")))
        painter.setPen(QPen(theme("border_c"), k))

        rect = QRect(QPoint(k//2, k//2), QSize(w, h))
        painter.drawRoundedRect(rect, 5, 5)

        painter.setBrush(QBrush(theme("head_c")))
        painter.setPen(Qt.PenStyle.NoPen)
        head = QRect(QPoint(k, k), QSize(w-k, 30))
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
            QTimer(self).singleShot(1000, self.close)
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

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.m_dragging = True
            self.m_last_position = event.globalPosition()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.m_dragging:
            diff = event.globalPosition() - self.m_last_position
            mp = self.target_widget.pos()  # Type: ignore
            mvp = QPointF(mp.x(), mp.y()) + diff
            self.target_widget.move(int(mvp.x()), int(mvp.y()))  # Type: ignore
            self.m_last_position = event.globalPosition()
            event.accept()


class InformUser(Dialog):
    ui = "$"
    name = "inform"

    ERROR = -1
    WARNING = 0
    INFO = 1

    def __init__(self, parent, main, i=False):
        super(InformUser, self).__init__(parent, main)
        self.main = main
        self.eno = None
        self.sts_icons = {
            -1: QIcon(import_("img/dialog/error.png")),
            0: QIcon(import_("img/dialog/warning.png")),
            1: QIcon(import_("img/dialog/info.png"))
        }
        self.widget = loadUi(import_("ui/ask-user.ui", 'io'))
        if i:
            self.initialize()

    def initialize(self, _p=None):
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.widget.cancel.clicked.connect(self.close)

    def no_cancel(self):
        self.widget.cancel.close()

    def closeEvent(self, a0):
        (self.eno or self.main).setEnabled(True)
        super(InformUser, self).closeEvent(a0)

    def inform(self, msg, title="Prompt", on_accept=None, on_deny=None, dis=None, res=None, sz=(300, 130), sts=4, args=None):
        self.widget.text.setText(msg)
        self.widget.title.setText(title.upper())

        if on_deny:
            self.widget.refuse.clicked.connect(lambda: on_deny(self, *(args or ())))
        else:
            self.widget.refuse.clicked.connect(self.close)

        if on_accept:
            self.widget.accept.clicked.connect(lambda: on_accept(self, *(args or ())))
        else:
            self.widget.accept.clicked.connect(self.close)

        self.eno = dis or self.main

        self.setParent(dis.parent() if dis else None)

        # self.eno.setEnabled(False)
        if self.sts_icons.get(sts):
            self.widget.icon.setIcon(self.sts_icons.get(sts))
        else:
            self.widget.icon.close()

        restore(self, *sz, sz=res)

        self.show_up(self.main)

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Y:
            self.widget.accept.click()

        if a0.key() == Qt.Key.Key_N:
            self.widget.refuse.click()

        if a0.key() == Qt.Key.Key_C:
            self.widget.cancel.click()


class KivyInnerWindow(Dialog):
    ui = "body"
    ui_type = QFrame
    name = "kv_win"

    def __init__(self, parent, main, d=False):
        super(KivyInnerWindow, self).__init__(parent, main)
        self.main = main
        self.widget = loadUi(import_("ui/kv-win.ui", 'io'))
        self.setFixedSize(self.widget.size())
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.close()
        if d:
            self.widget.win_head.layout().addWidget(DraggableFrame(parent))

    def set_title(self, t):
        self.widget.label.setText(t)

    def set_body(self, wid):
        self.widget.win_body.layout().addWidget(wid)


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
        self.close_btn.setIcon(QIcon(import_("img/style/close.svg")))
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
        self.close()

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


class SearchTip(DraggableFrame):
    ui = "body"
    ui_type = QFrame
    name = "search"

    def __init__(self, parent, main):
        super(SearchTip, self).__init__(main)
        self.target_widget = self
        self.main = main
        self.target = parent
        self.find_pos = None
        self.current_pos = 0
        self.widget = loadUi(import_("ui/find-in-editor.ui", 'io'))
        set_shadow(self)

    def initialize(self, _):
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.resize(self.widget.size())
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("dialog")

        self.widget.search.textChanged.connect(self._search)
        self.widget.next.clicked.connect(lambda: self._load_next(1))
        self.widget.previous.clicked.connect(lambda: self._load_next(-1))
        self.widget.cancel.clicked.connect(self.close)
        self.widget.replace_all.clicked.connect(self.replace_in_text)
        self.widget.replace_one.clicked.connect(lambda: self.replace_in_text(one=True))

        self.widget.next.setIcon(QIcon(import_("img/widgets/next.png")))
        self.widget.previous.setIcon(QIcon(import_("img/widgets/previous.png")))
        self.widget.cancel.setIcon(QIcon(import_("img/widgets/cancel.png")))
        self.widget.replace_one.setIcon(QIcon(import_("img/widgets/replace.png")))
        self.widget.replace_all.setIcon(QIcon(import_("img/widgets/replace_all.png")))
        self.close()

    def replace_in_text(self, *_, one=False):
        if not hasattr(self.target, "editor"):
            return

        old = getattr(self.target, "text")()
        old_rep = self.widget.search.text()
        new_rep = self.widget.replace_with.text()
        args = [old_rep, new_rep, old]

        if one:
            args.append(1)

        getattr(self.target, "setText")(re.sub(*args))

    def keyPressEvent(self, a0: QKeyEvent):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

        super(SearchTip, self).keyPressEvent(a0)

    def _load_next(self, k=1):
        if hasattr(self.target, "editor"):
            if self.find_pos:
                if len(self.find_pos) > abs(self.current_pos+k):
                    pos = self.find_pos[self.current_pos+k]
                    self.target.select(*pos)  # Type: ignore

                    if self.current_pos+k < 0:
                        self.current_pos = len(self.find_pos)

                    self.current_pos += k
                    self.widget.found.setText(f"{self.current_pos+1}/{len(self.find_pos)}")
                else:
                    self.current_pos = 0
                    self._load_next(0)

    def pop(self, _p=None):
        self.target = _p or self.target
        self.show()
        self.widget.search.setFocus()
        self.widget.search.setText(self.target.selectedText())
        self.widget.search.selectAll()

        curp: QPoint = self.cursor().pos()

        myw = self.size().width()
        myh = self.size().height()
        mnx = self.main.pos().x()
        mny = self.main.pos().y()
        mnw = self.main.size().width()
        mnh = self.main.size().height()

        if curp.x() + myw > mnx + mnw:
            curp.setX((mnw - myw) - 4)

        if curp.x() < mnx:
            curp.setX(4)

        if curp.y() > mnh:
            curp.setY(mnh - myh - 4)
        else:
            curp.setY(max(curp.y() - mny, 4))

        self.move(curp)
        self.raise_()

    def _search(self):
        query = self.widget.search.text()

        if not query:
            self.widget.found.setText(f"0/0")
            self.current_pos = 0
            self.find_pos = None
            return

        if isinstance(self.widget, QTreeWidget):
            self.widget.clearSelection()
            matching_items = self.widget.findItems(query, Qt.MatchFlag.MatchRecursive)
            for item in matching_items:
                item.setSelected(True)
                parent = item.parent()
                if parent:
                    parent.setExpanded(True)

        if hasattr(self.target, "editor"):
            pos = []
            text = self.target.text()  # Type: ignore
            try:
                color = "white"
                search_p = re.compile(query, re.M)
            except Exception as e:
                _ = e
                color = "red"
                search_p = None

            self.widget.search.setStyleSheet(f"color: {color}")
            if not search_p:
                return

            self.find_pos = 0
            for i in search_p.finditer(text):  # Type: ignore
                pos.append((i.start(), i.end()))
            if pos:
                self.widget.found.setText(f"1/{len(pos)}")
                self.find_pos = pos
                self._load_next(0)
            else:
                self.find_pos = None
                self.widget.found.setText(f"Not found!")

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QPen(QColor("#333")))
        painter.setBrush(QBrush(theme("background_c")))
        rect = QRect(QPoint(0, 0), self.widget.size())

        painter.drawRect(rect)

        super(SearchTip, self).paintEvent(a0)


class AppScene(QWidget):
    title = "None"
    path = ""
    editor = None

    def __init__(self, parent, main):
        super(AppScene, self).__init__(parent)
        self.main = main
        self.widget = loadUi(import_("ui/scene.ui", 'io'))

    def init(self, _, wid):
        set_layout(self, QGridLayout)

        window = QWindow.fromWinId(wid)  # Type: ignore
        container = QWidget(self).createWindowContainer(window, self)

        container.setFixedSize(QSize(*settings.pull("kivy/window-resolution").values()))
        self.widget.holder.layout().addWidget(container)
        self.layout().addWidget(self.widget)


class Pointer(QWidget):
    def __init__(self, obj):
        super(Pointer, self).__init__(obj.parent())
        self.obj = obj
        self.setStyleSheet("background: red")
        self.resize(QSize(150, 100))
        self.widget = QTextBrowser(self)
        set_layout(self, QVBoxLayout).addWidget(self.widget)
        self.close()

    def point(self, msg, k=1):
        pos = self.obj.pos()
        pos = self.parent().mapToParent(pos)
        x, y = pos.x(), pos.y()
        y += (self.size().height() * 1.4) * k
        self.move(QPoint(int(x), int(y)))
        self.widget.setText(msg)
        self.show()
        self.raise_()


class InLineInput(QLineEdit):
    def __init__(self, parent, callback=None, place_holder=None, args=None, mf=None):
        super(InLineInput, self).__init__(parent)
        self.callback = callback
        self.check_method = mf
        self.args = args
        action = QAction(self)
        action.triggered.connect(self.close)
        action.setShortcut("Esc")
        self.returnPressed.connect(self._enter)
        self.addAction(action)
        self.setStyleSheet("border: 1px solid #333")
        self.set_placeholder(place_holder)
        self.textChanged.connect(self._text_changed)
        self.close()

    def set_callback(self, fn):
        self.callback = fn

    def set_placeholder(self, tx):
        self.setPlaceholderText(tx or "")

    def set_args(self, args):
        self.args = args

    def check(self, m):
        self.check_method = m

    def _text_changed(self):
        k = self._check()
        if k or k == 8:
            self.setStyleSheet("color: white")
        else:
            self.setStyleSheet("color: red")

    def _check(self):
        if self.check_method:
            if callable(self.check_method):
                return self.check_method(self.text())
        return 8

    def done(self):
        self.clear()
        self.set_args(None)
        self.set_placeholder("")
        self.set_callback(None)
        self.close()

    def _enter(self):
        if self.callback and self._check():
            self.callback(self, *(self.args or ()))

    def read_at(self, pos):
        self.move(QPoint(pos.x() - 100, pos.y() + 18))
        self.show()
        self.raise_()
        self.setFocus()
