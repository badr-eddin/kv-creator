import os.path
import pathlib
import magic
import psutil
import pyperclip

from .dialogs import AppScene
from ..utils import *


class DefaultTheme:
    font_size = 12
    
    background = "#080808"
    foreground = "#ffffff"
    selection_bg = "#FFFFFF"
    selection_fore = "#000000"
    margins_fore = "gray"
    margins_bg = "#0b0b0b"
    line = "#FFFFFF"
    error = "#ff3333"
    transparent = "transparent"

    background_c = QColor(background)
    foreground_c = QColor(foreground)
    selection_bg_c = QColor(selection_bg)
    selection_fore_c = QColor(selection_fore)
    margins_fore_c = QColor(margins_fore)
    margins_back_c = QColor(margins_bg)
    line_c = QColor(line)
    error_c = QColor(error)
    transparent_c = QColor(transparent)

    line_c.setAlpha(15)
    selection_bg_c.setAlpha(30)


class Default(QsciLexerCustom):
    def __init__(self, parent):
        super(Default, self).__init__(parent)
        self.setDefaultPaper(DefaultTheme.background_c)
        self.setDefaultColor(DefaultTheme.foreground_c)

    def description(self, *_):
        return "Default Lexer"

    def styleText(self, start=0, end=0):
        pass


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
        self.act_hand = Handler(main, self)
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
        lxr = Default(self)
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

        self._setup_default_lexer(lxr)
        self.setLexer(lxr)

    def set_path(self, path):
        self.path = path
        self.config_lexer()

    def _setup_default_lexer(self, lxr):
        lxr.setDefaultPaper(color("background"))
        lxr.setDefaultColor(color("foreground"))
        lxr.setPaper(color("background"))
        self.setStyleSheet(f'background: {color("background", 0)}; padding-top: 12px;')

        self.setMarginsBackgroundColor(color("background"))
        self.setMarginsForegroundColor(color("foreground"))
        self.setCaretForegroundColor(color("foreground"))

        sec = color("selection")
        sec.setAlpha(50)
        self.setIndicatorForegroundColor(sec, self.SELECTION_IND)

        font = QFont()
        font.setFamily(settings.pull("editor/font-name") or "Fira Code Medium")
        font.setPointSize(settings.pull("editor/font-size") or DefaultTheme.font_size)
        lxr.setFont(font)

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
                    target=dialog.Targets.Files,
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
        footer = f"Col {_config(_ind+1)} | Row {_config(_ln+1)} | Lines {_config(self.lines())}"
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


class EditorWidget(QWidget):
    ui = "body"
    ui_type = QFrame
    name = "editor"

    def __init__(self, parent, main):
        super(EditorWidget, self).__init__(parent)
        self.main = main
        self.editors = []
        self.opened_paths = {}
        self.widget = QTabWidget(self)

    def style_on_off(self, on=False):
        if on:
            k = f"1px solid {theme('border_2c', False)}"
        else:
            k = "none"

        self.widget.setStyleSheet("QStackedWidget{" f"border: {k};" "}")

    def config_window(self):
        set_layout(self, QVBoxLayout)
        self.layout().addWidget(self.widget)
        self.widget.setObjectName("editor-tab-widget")
        self.widget.setTabsClosable(True)
        self.widget.tabCloseRequested.connect(self.close_editor_tab)  # Type: ignore
        self.widget.currentChanged.connect(self._tab_changed)  # Type: ignore
        self.widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.widget.tabBar().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.widget.setAcceptDrops(True)
        self.setAcceptDrops(True)
        self.style_on_off()
        self.widget.dropEvent = lambda e: self.dropped_from(e)
        
    def dropEvent(self, e):
        self.dropped_from(e)
        super(EditorWidget, self).dropEvent(e)

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data: QMimeData = event.mimeData()
        if mime_data.hasUrls():
            event.acceptProposedAction()

    def dropped_from(self, e):
        mime: QMimeData = e.mimeData()
        mag = magic.Magic(True)
        if mime.hasUrls():
            for url in mime.urls():
                url: QUrl
                mmt = mag.from_file(url.path())
                if mmt.startswith("text") or "svg" in mmt:
                    self.add_editor(pathlib.Path(url.path()).read_text(), url.path())

    def search(self):
        self.main.search_in(self.widget.currentWidget())

    def close_editor_tab(self, index):
        tab = self.widget.widget(index)

        self.main.editor_closed(tab)

        if self.widget.count() == 1:
            self.style_on_off()

        if isinstance(tab, Editor):
            if not getattr(tab, "saved"):
                func = self.main.element("inform.inform")
                func("Changes have been made but haven't been saved. Would you like to save them now?", "Editor",
                     on_accept=lambda d: self._save_confirmed(tab, index, d),  # Type: ignore
                     on_deny=lambda d: self._single_deny(index, d, tab), sts=0)
            else:
                self.widget.removeTab(index)
                self.super_done()
                if tab.path in self.opened_paths:
                    self.opened_paths.pop(tab.path)

        elif hasattr(tab, "pid"):
            self.widget.removeTab(index)

            # remove tab before you kill the process, because it might be null
            if tab.pid > 0:
                process = psutil.Process(tab.pid)
                process.kill()
                process.terminate()
                debug(f"process: '{process.pid}' is dead °^° .")
        else:
            self.widget.removeTab(index)

    def _single_deny(self, index, d, tab):
        self.widget.removeTab(index)
        d.close()
        if tab in self.editors:
            self.editors.remove(tab)
        if tab.path in self.opened_paths:
            self.opened_paths.pop(tab.path)

    def add_external_window(self, wid, title="Kivy", path=None, pid=0, kwargs=None):
        debug("adding external window ... ")

        scene = AppScene(self.widget, self.main)
        scene.pid = pid
        scene.title = title
        scene.path = path
        scene.editor = (kwargs or {}).get("editor")
        scene.init(path, wid)

        index = self.widget.addTab(scene, title)
        self.widget.setCurrentWidget(scene)

        self.main.on("external_window_tab_created", {"editor": self.widget.widget(index)})

    def _save_confirmed(self, tab, index, _d, c=True):
        tab.save_content(index)
        _d.close()
        self.super_done()
        if c:
            self.widget.removeTab(index)
            if tab.path in self.opened_paths:
                self.opened_paths.pop(tab.path)

        if tab in self.editors:
            self.editors.remove(tab)

    def _save(self):
        editor = self.widget.currentWidget()
        if isinstance(editor, Editor):
            editor.save_content(self.widget.currentIndex())  # Type: ignore

    def super_done(self):
        self.main.element("inspector.done")()
        self.main.element("p-editor.done")()
        self.main.element("imports.done")()

        kvf = os.path.basename(str(getattr(self.widget.currentWidget(), "path", "0"))).endswith(".kv")

        self.main.element("inspector").setEnabled(kvf)
        self.main.element("p-editor").setEnabled(kvf)
        self.main.element("imports").setEnabled(kvf)

    def open_file(self):
        dialog, plg = self.main.get_file_dialog()

        if plg:
            dialog = dialog(main=self.main, std=self.main.std)
            dialog.open_save_file(
                callback=self._add_editor_on_open,
                selection=dialog.Selection.Single,
                encapsulate=pathlib.Path,
                mode=dialog.Mode.Open,
                custom_check=self._check_file_mimetype,
                entry=self.main.project_path
            )
        else:
            dialog = dialog(self)
            path_ = dialog.getOpenFileName(directory=self.main.project_path)

            if path_[0]:
                path_ = path_[0]

                if self._check_file_mimetype(path_):
                    self._add_editor_on_open(pathlib.Path(path_))

    def _add_editor_on_open(self, path: pathlib.Path):
        if path:
            self.add_editor(path.read_text(), path.as_posix())

    def point_under(self, *args):
        editor = self.editor()
        if editor:
            editor.point_under(*args)

    def editor(self, k=None, d=None) -> Editor | int:
        if isinstance(self.widget.currentWidget(), Editor):
            if not k:
                return self.widget.currentWidget()

            return getattr(self.widget.currentWidget(), str(k), d)
        return 0

    @staticmethod
    def _check_file_mimetype(path: str):
        try:
            pathlib.Path(path).read_text()
            return True
        except Exception as e:
            _ = e
            debug(f"{os.path.basename(path)}: expected 'text' got 'bytes'", _c="e")

    def _tab_changed(self, index: int):
        widget = self.widget.widget(index)
        if isinstance(widget, Editor):
            widget = widget
        elif isinstance(widget, AppScene):
            widget = widget.editor
        else:
            widget = None

        if widget:
            os.environ["building"] = "1"
            self.super_done()
            widget.reload_it()
            widget.load_cls()

        self.main.on("tab_changed", {"editor": widget})

    def on_main_close(self, mn):
        unsaved = []
        for editor in self.editors:
            if not editor.saved:
                unsaved.append(editor)

        if unsaved:
            mn.close_win = False
            func = self.main.element("inform.inform")
            func("Changes have been made but haven't been saved. Would you like to save them now?", "Editor",
                 on_accept=lambda d: self._save_all(d, unsaved), on_deny=lambda d: self._deny(d), sts=0)
        else:
            self._deny(mn)

    def _save_all(self, d, un):
        for ed in un:
            self._save_confirmed(ed, self.widget.indexOf(ed), d, False)

        self._deny(d)

    def _deny(self, d=None):
        self.main.super_close()
        if d:
            d.close()

    def add_editor(self, content="", path=None):
        if path in self.opened_paths:
            self.widget.setCurrentIndex(self.opened_paths.get(path))
            return

        debug(f"create new tab '{path or 'anonymous'}'")

        content = content if isinstance(content, str) else ""
        ed = Editor(self, self.main, self.widget)
        ed.reload = False
        ed.setText(content)
        ed.saved = True
        ed.set_path(path)
        index = self.widget.addTab(ed, os.path.basename(path) if path else "New Tab")
        ed.index = index

        self.style_on_off(True)
        self.editors.append(ed)
        self.widget.setTabToolTip(ed.index, path or "")
        self.widget.setCurrentWidget(ed)
        self.opened_paths.update({path: index})

        self.main.on("editor_tab_created", {"editor": self.widget.widget(index)})

    @staticmethod
    def get_text_editor(*args, path=""):
        ed = Editor(*args)
        ed.reload = False
        ed.index = -1
        ed.saved = True
        ed.set_path(path)
        return ed

    def initialize(self, _p):
        parent = _p or self.parent()
        parent.layout().addWidget(self)
        self.config_window()
