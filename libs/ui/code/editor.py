from .theme import DefaultTheme
from .lexer import DefaultLexer
from ...pyqt import QsciScintilla, QFrame, QFontMetrics, QColor, Qt, QKeySequence, QDropEvent,\
    QIcon, QTimer, QAction, QsciLexer, QKeyEvent, QFont, QMouseEvent, QMenu
from ...utils import color, import_, settings, debug, Clipboard, EditorKeysHandler

import pyperclip
import os
import pathlib


class Editor(QsciScintilla):
    path = ""
    saved = True
    index = 0
    editor = True

    ERROR_INDICATOR = 14500
    WARNING_INDICATOR = 14600
    DEFAULT_INDICATOR = 14700

    SELECTION_IND = 3

    def __init__(self, parent, main, tabs=None):
        super(Editor, self).__init__(parent)
        self.main = main
        self.clip = Clipboard()
        self.tabs = tabs
        self.actions_menu = QMenu(self)
        self.selected = []
        self.selection_beg = [-1, -1]
        self.is_selecting = False
        self.selection_going_backward = False
        self.widget = parent
        self.reload = True
        self.selection_timer = QTimer(self)
        self.cursor_pos = (0, 0)
        self.minus_cur_pos = 0
        self.selection_start = None
        self.keys_functions = settings.pull(f"editor/keys")
        self.act_hand = EditorKeysHandler(main, self)
        self.setTabWidth(4)
        self.load_actions()
        self.setCaretWidth(2)
        self.setTabIndents(True)
        self.setAutoIndent(True)
        self.setMarginWidth(0, 35)
        self.setCallTipsVisible(0)
        self.setCaretLineVisible(True)
        self.setIndentationGuides(True)
        self.setIndentationsUseTabs(True)
        self.setMarginLineNumbers(0, True)
        self.setObjectName("editor-widget")
        self.actions_menu.setFixedWidth(200)
        self.selection_timer.setSingleShot(True)
        self.SendScintilla(self.CARETSTYLE_LINE)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setCallTipsHighlightColor(color("c2"))
        self.SendScintilla(self.SCI_SETHSCROLLBAR, 0)
        self.SendScintilla(self.SCI_SETHSCROLLBAR, 0)
        self.SendScintilla(self.SC_SEL_RECTANGLE, 1, 20)
        self.setCallTipsBackgroundColor(color("background"))
        self.setCallTipsForegroundColor(color("foreground"))
        self.textChanged.connect(self._config_margins_width)  # Type: ignore
        self.cursorPositionChanged.connect(self.cursor_move)  # Type: ignore
        self.setCaretLineBackgroundColor(DefaultTheme.line_c)
        self.selectionChanged.connect(self._selection_changed)
        self.SendScintilla(self.SCI_SETMULTIPLESELECTION, True)
        self.setCaretForegroundColor(DefaultTheme.foreground_c)
        self.setSelectionBackgroundColor(DefaultTheme.background_c)
        self.setIndentationGuidesForegroundColor(color("foreground"))
        self.setIndentationGuidesBackgroundColor(color("foreground"))
        self.setSelectionForegroundColor(DefaultTheme.selection_bg_c)
        self.actions_menu.setStyleSheet("QMenu::item{margin: 0 1px}")
        self.setAutoCompletionSource(self.AutoCompletionSource.AcsAll)
        self.SendScintilla(self.SCI_SETADDITIONALSELECTIONTYPING, True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_requested)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setIndicatorForegroundColor(QColor("#FF3333"), self.ERROR_INDICATOR)
        self.setIndicatorForegroundColor(QColor("#FF5600"), self.WARNING_INDICATOR)
        self.setIndicatorForegroundColor(QColor("#E5C07B"), self.DEFAULT_INDICATOR)
        self.setIndicatorOutlineColor(DefaultTheme.transparent_c, self.SELECTION_IND)
        self.indicatorDefine(self.IndicatorStyle.FullBoxIndicator, self.SELECTION_IND)
        self.setIndicatorForegroundColor(DefaultTheme.selection_bg_c, self.SELECTION_IND)
        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, self.ERROR_INDICATOR)
        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, self.WARNING_INDICATOR)
        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, self.DEFAULT_INDICATOR)

        self.main.on("editor_context_menu_requested", {"editor": self})

    def _sel(self, start, end):
        self.fillIndicatorRange(
            *self.lineIndexFromPosition(start),
            *self.lineIndexFromPosition(end),
            self.SELECTION_IND
        )

        self.selected = [start, end]
        self.is_selecting = True

    def _selection_changed(self):
        pos = self.getSelection()

        if not self.is_selecting:
            self.selection_beg = pos[0], pos[1]

        if sum(self.getSelection()) < 0:
            return

        pos = self.getCursorPosition()
        self.is_selecting = True
        self.SendScintilla(self.SCI_CLEARSELECTIONS)
        self.setCursorPosition(*pos)

    def _config_margins_width(self):
        self.main.on("editor_text_changed", kwargs={"editor": self})

        fm = QFontMetrics(self.font())
        c = len(str(self.lines()))

        if c > 2:
            self.setMarginWidth(0, int(fm.averageCharWidth() * c * 1.9))

        self.load_cls()
        self.saved = False
        os.environ["editor-editing"] = "1"

        if self.tabs:
            mi = self.tabs.indexOf(self)
            tit = self.tabs.tabText(mi)
            tit = tit + " *" if not tit.endswith("*") else tit
            self.saved = False
            self.tabs.setTabText(mi, tit)

        self.clip.register(self.text())

    # ****************************************
    def config_lexer(self):
        lxr = DefaultLexer(self)
        self.main.on("lexer_setup_start", {"editor": self})

        if self.path:
            ext = os.path.splitext(os.path.basename(self.path))[1]
            lexers = (self.main.ui_plugins.get("editor") or {}).get("support") or []
            for lexer in lexers:
                if ext in lexer.FILES:
                    lxr = lexer(self, self.main)
                    if settings.pull("user-prefs/autocomplete"):
                        if hasattr(lxr, "config_auto_complete"):
                            lxr.config_auto_complete()
                    break

        _lxr = self.main.on("lexer_setup_done", {"color": color, "path": self.path})
        _lxr = (_lxr[0] if len(_lxr) >= 1 else _lxr) if type(_lxr) is list else _lxr
        lxr = _lxr if isinstance(_lxr, QsciLexer) else lxr

        self.setLexer(lxr)
        self._setup_default_lexer(lxr)

    def set_path(self, path):
        self.path = path
        self.config_lexer()

    def _setup_default_lexer(self, lxr):
        lxr.setDefaultPaper(color("background"))
        lxr.setDefaultColor(color("foreground"))
        lxr.setPaper(color("background"))
        self.setStyleSheet(f'background: {color("background", 0)}; padding-top: 12px;')

        self.setCaretForegroundColor(color("foreground"))

        sec = color("selection")
        sec.setAlpha(50)
        self.setIndicatorForegroundColor(sec, self.SELECTION_IND)

        font = QFont()
        font.setFamily(settings.pull("editor/font-name") or "Fira Code Medium")
        font.setPointSize(settings.pull("editor/font-size") or DefaultTheme.font_size)
        lxr.setFont(font)

        self.setMarginsBackgroundColor(color("background"))
        self.setMarginsForegroundColor(color("foreground"))

    def load_actions(self):
        for _action in self.keys_functions:
            action = QAction(self)
            action.setShortcut(_action)
            func = self.keys_functions.get(_action)
            if func and hasattr(self.act_hand, func):
                action.triggered.connect(getattr(self.act_hand, func))
            self.addAction(action)

    # ****************************************
    def select(self, start, end):
        self.clear_selection(True)
        self.setCursorPosition(*self.lineIndexFromPosition(end))

        self.selection_timer.singleShot(50, lambda: self._sel(start, end))

    def save_content(self, index):
        if self.path:
            try:
                with open(self.path, "w") as file:
                    file.write(self.text())
                if self.tabs:
                    self.tabs.setTabText(index, os.path.basename(self.path))
                self.saved = True
            except Exception as e:
                _ = e
        else:
            def _save(path):
                if path:
                    self.path = path.as_posix()
                    self.save_content(index)
                    self.config_lexer()

            dialog, plg = self.main.get_file_dialog()
            if plg:
                dialog = dialog(main=self.main, std=self.main.std)
                dialog.open_save_file(
                    callback=_save,
                    selection=dialog.Selection.Single,
                    mode=dialog.Mode.Save,
                    target=dialog.TARGETS.Files,
                    entry=self.main.project_path
                )
            else:
                dialog = dialog(self)
                path_ = dialog.getSaveFileName(directory=self.main.project_path)

                path_ = pathlib.Path(path_[0])
                _save(path_)

    def reload_it(self):
        self.reload = True

    def load_cls(self):
        func1 = self.main.element("imports.load")
        if func1 and self.reload:
            func1(self)

        func = self.main.element("inspector.load_class")

        if func and self.reload:
            func(self)

    def get_selected_text(self):
        if self.is_selecting:
            text = self.text()[self.selected[0]:self.selected[1]]
        else:
            text = self.text().splitlines(False)[self.getCursorPosition()[0]]
        return text

    def point_under(self, *args):
        self.fillIndicatorRange(*args)

    def unpoint(self, *args):
        # QImage("green_dot.png").scaled(QSize(16, 16))
        self.clearIndicatorRange(*args)

    def context_menu_requested(self):
        actions = settings.pull("editor/menu")
        self.actions_menu.clear()

        for exa in self.main.plugins_actions:
            if (self.main.plugins_actions.get(exa) or {}).get("@type") == "lexer":
                if isinstance(self.lexer(), exa):
                    actions.update(self.main.plugins_actions.get(exa) or {})

        for ac in actions:
            try:
                if ac.startswith("@type"):
                    continue

                action = QAction(self.actions_menu)

                func = str(ac).replace(" ", "_")
                obj = self.act_hand
                text = ac

                if func.startswith("$"):
                    obj = self.lexer()
                    func = str(actions.get(ac))
                    func, icon = func.split("@")
                    func = func.replace(" ", "_")
                    text = ac[1:]
                    icon = QIcon(import_(icon))
                else:
                    icon = QIcon(import_(actions.get(ac)))

                action.setIcon(icon)
                action.setText(text)

                if hasattr(obj, func):
                    action.triggered.connect(getattr(obj, func))

                self.actions_menu.addAction(action)

            except Exception as e:
                debug(f"editor-context:: {e}")

        self.actions_menu.exec(self.cursor().pos())

    def cursor_move(self, _ln, _ind):
        self.cursor_pos = (_ln, _ind)

        self.main.on("cursor_moved", {"editor": self, "pos": self.cursor_pos})

        def _config(_t, _m=8):
            return str(_t) + " " * (_m - len(str(_t)))

        # update footer
        footer = f"Col: {_config(_ind + 1)} | Row: {_config(_ln + 1)} | Lines: {_config(self.lines())}"
        self.main.widget.editor_inspect.setText(footer)

        if self.is_selecting:
            self.setCaretLineVisible(False)
            self.select_using_indicator((_ln, _ind))
        else:
            self.setCaretLineVisible(True)
            self.clear_selection()

    def remove_selected_text(self, k=""):
        if not self.is_selecting:
            return

        text = self.text()
        pos = self.lineIndexFromPosition(self.selected[0] + len(k))
        text = text[:self.selected[0]] + k + text[self.selected[1]:]
        self.clear_selection(True)
        self.clear()
        self.setText(text)
        self.setCursorPosition(*pos)

    def select_using_indicator(self, pos):
        self.clear_selection()

        if self.positionFromLineIndex(*self.selection_beg) > self.positionFromLineIndex(*pos):
            selection = (*pos, self.selection_beg[0], self.selection_beg[1] + 1)
        else:
            selection = (*self.selection_beg, *pos)

        self.selected = [self.positionFromLineIndex(*selection[:2]), self.positionFromLineIndex(*selection[2:])]
        self.fillIndicatorRange(*selection, self.SELECTION_IND)

    def clear_selection(self, _f=False):
        if _f:
            self.is_selecting = False
            self.selection_beg = [-1, -1]

        self.clearIndicatorRange(0, 0, *self.lineIndexFromPosition(self.length()), self.SELECTION_IND)

    # ****************************************

    def dropEvent(self, e: QDropEvent):
        self.widget.dropped_from(e)  # Type: ignore

        super(Editor, self).dropEvent(e)

    def mousePressEvent(self, e: QMouseEvent):
        if not e.modifiers() and e.button() != Qt.MouseButton.RightButton:
            self.setCaretLineVisible(True)
            self.clear_selection(True)

        super(Editor, self).mousePressEvent(e)

    def keyPressEvent(self, e: QKeyEvent):
        if e.matches(QKeySequence.StandardKey.Undo):
            txt = self.clip.undo()
            if type(txt) is int:
                return

            pos = self.positionFromLineIndex(*self.getCursorPosition())
            otl = len(self.text())
            self.setText(txt)
            pos = self.lineIndexFromPosition(abs(pos + abs(otl - len(txt))))
            self.setCursorPosition(*pos)
            return

        elif e.matches(QKeySequence.StandardKey.Redo):
            txt = self.clip.redo()
            if type(txt) is int:
                return

            pos = self.positionFromLineIndex(*self.getCursorPosition())
            otl = len(self.text())
            self.setText(txt)
            pos = self.lineIndexFromPosition(abs(pos + abs(otl + len(txt))))
            self.setCursorPosition(*pos)
            return

        if e.modifiers() == Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_Space:
            self.main.on("asked_for_completion", {"editor": self})

        if e.key() == Qt.Key.Key_Backspace:
            if self.is_selecting:
                self.remove_selected_text()
                return

            pos = self.getCursorPosition()
            self.cursor_pos = (pos[0], pos[1] - 1 if pos[1] else pos[0])

        if e.key() == Qt.Key.Key_Tab:
            self.insert(" " * 4)
            pos = self.getCursorPosition()
            self.setCursorPosition(pos[0], pos[1] + 4)
            return

        if e.text() and e.modifiers() != Qt.KeyboardModifier.ControlModifier:
            if self.is_selecting:
                self.remove_selected_text(e.text())
                return

        if e.matches(QKeySequence.StandardKey.Copy):
            pyperclip.copy(self.get_selected_text())
            return

        if e.matches(QKeySequence.StandardKey.Cut):
            pyperclip.copy(self.get_selected_text())
            self.remove_selected_text()
            return

        if e.matches(QKeySequence.StandardKey.Paste):
            if self.is_selecting:
                self.remove_selected_text(pyperclip.paste())
                return

        if e.matches(QKeySequence.StandardKey.SelectAll):
            self.select(0, self.length())
            return

        if e.modifiers() != Qt.KeyboardModifier.ShiftModifier and e.key() in [
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down
        ] and self.is_selecting:
            self.clear_selection(True)
            return

        super(Editor, self).keyPressEvent(e)
