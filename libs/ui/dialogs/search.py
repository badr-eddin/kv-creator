from ...pyqt import (QFrame, QTreeWidget,
                     QVBoxLayout, QPoint,
                     QIcon, QPainter, QPen,
                     QBrush, QRect, QKeyEvent,
                     Qt, loadUi, QColor)

from ...utils import import_, set_shadow, set_layout, theme
from .dialog import DraggableFrame

import re


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

        if not hasattr(self.target, "text"):
            return

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
                _color = "white"
                search_p = re.compile(query, re.M)
            except Exception as e:
                _ = e
                _color = "red"
                search_p = None

            self.widget.search.setStyleSheet(f"color: {_color}")
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
