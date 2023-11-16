_THEME = """
QWidget {
    selection-background-color: "$MAIN";
    selection-color: "$SELECTION-COLOR";
    font-size: "$FONT-SIZE";
    font-family: "$FONT";
    color: "$FOREGROUND"
}
#head, #footer {
    background: "$WIDGET-1";
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
}
#body, QMainWindow {
    background: "$BACKGROUND";
}
#line {
    border-top: 1px solid "$BACKGROUND";
    background: transparent;
}
QTreeWidget {
    background: transparent;
    padding-right: 2px;
}
QTreeWidget::item, QListWidget::item {
    min-height: 25px;
    background: rgba(255, 255, 255, 10);
    padding: 2px 1px;
    margin-top: 1px;
}
QTreeWidget::item:hover, QListWidget::item:hover {
    background: rgba(255, 255, 255, 5);
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background: "$MAIN";
    color: white;
}
QTreeView::branch:hover, QTreeView::branch:selected, QTreeView::branch {
    background: transparent;
}
QTreeWidget QHeaderView {
    background: "$WIDGET-2";
    border: none;
    min-height: 22px;
    padding: 2px;
}
QTreeWidget QHeaderView::section {
    border: none;
    background: "$WIDGET-2";
    padding: 2px 4px;
    min-height: 23px;
    border-right: 1px solid "$BACKGROUND";
}
QTreeWidget QHeaderView::section:last {
    border: none;
}
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url($/img/style/arrow-right.svg);
}
QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url($/img/style/arrow-down.svg);
}
QListWidget::item QLineEdit, QTreeWidget::item QLineEdit,
QListWidget::item QComboBox, QTreeWidget::item QComboBox {
     min-height: 20px;
     border: none;
     border-radius: none;
}
QListWidget::item QComboBox, QTreeWidget::item QComboBox{
    background: transparent;
}
QPushButton {
    background: "$WIDGET-2";
    border: 1px double transparent;
    border-radius: 1px;
}
QPushButton:hover {
    background: "$WIDGET-2-H";
}
QPushButton:pressed {
    color: "$MAIN";
}
QComboBox{
    border: none;
    padding: 0px 4px;
    background: "$WIDGET-2";
    border-radius: 2px;
    padding-right: 10px;
}
QComboBox:hover{
    padding: 0px 4px;
    border-radius: 2px;
    border: none;
    background: "$WIDGET-2-H";
}
QComboBox::indicator:checked,
QComboBox::indicator:checked:editable,
QMenu::indicator:checked,
QComboBox::indicator:checked:editable{
    width: 16px;
    height: 16px;
    padding-left: 2px;
    image: url($/img/style/check-icon.svg);
}
QComboBox::drop-down,
QComboBox::drop-down:editable{
    border: none;
    padding-right: 0px;
    padding-right: 10px;
}
QComboBox::down-arrow,
QComboBox::down-arrow:editable{
    image: url($/img/style/arrow-down.svg);
    width: 16px;
    height: 16px;
}
QComboBox::down-arrow:disabled,
QComboBox::down-arrow:disabled:editable{
    image: url($/img/style/arrow-down.svg);
}
QCompleter::item:selected,
QComboBox::item:selected,
QComboBox::item:selected:editable{
    border: none;
    background: "$MAIN";
    color: black;
}
QComboBox::item{
    min-height: 25px;
    background: "$WIDGET-2";
}
QAbstractItemView {
    border: none;
    background: "$WIDGET-2";
    selection-background-color: "$MAIN";
    padding: 4px;
}
QAbstractItemView::item{
    min-height: 20px;
}

#bar-button {
    background: none;
    border: none;
    font-family: "Ubuntu Mono";
}
#bar-button:hover {
    background: rgba(255, 255, 255, 0.1);
}
#bar-button:pressed {
    color: "$MAIN";
}
QLineEdit, QTextEdit{
    background: #000;
    border: 1px solid #333;
    border-radius: 1px;
    min-height: 25px;
    padding: 0 4px;
}
QLineEdit:focus, QLineEdit:hover, QTextEdit:focus, QTextEdit:hover{
    border: 1px solid "$MAIN";
}
QStackedWidget {
    border: 1px solid #333;
}
QTabWidget::pane {
    border: none;
    background: #000;
    top: -2px;
}
QTabWidget {
    border: none;
}
QTabBar{
    background: transparent;
}
QTabBar QToolButton {
    background-color: "$WIDGET-1";
    border: none;
    border-radius: 4px;
    margin: 2px;
}
QTabBar QToolButton::left-arrow {
    image: url($/img/style/arrow-left.svg);
}
QTabBar QToolButton::right-arrow {
    image: url($/img/style/arrow-right.svg);
}
QTabBar::tab {
    border: none;
    background: "$WIDGET-2-H";
    padding: 2px 4px;
    margin: 2px;
    min-height: 22px;
    min-width: 100px;
    margin-bottom: 4px;
    border-bottom: 1px solid transparent;
}
QTabBar::tab:hover {
    background: "$WIDGET-2";
}
QTabBar::tab:selected {
    background: "$WIDGET-2";
    border-bottom: 1px solid "$MAIN";
}
QTabBar::close-button{
    image: url($/img/style/close.png);
}
QTabBar::close-button:hover{
    image: url($/img/style/close-active.png);
}
#editor-tab-widget {
    background: transparent;
}
#editor-widget {
    background: transparent;

}
#inspector {
    background: transparent;
}
QListWidget, QTreeWidget {
    background: transparent;
    padding-right: 0px;
}
QListWidget[type="cont"], QTreeWidget[type="cont"] {
    background: #020202;
    border: 1px solid #333;
}
QDockWidget, #dockBody {
    background: "$BACKGROUND";
    color: "$FOREGROUND";
    border: 1px solid #191c1f;
    titlebar-close-icon: url($/img/style/close.svg);
    titlebar-normal-icon: url($/img/style/dock.svg);
}
QDockWidget::close-button {
    background: transparent;
    border: none;
    padding: 0px;
}
QDockWidget::float-button {
    background: transparent;
    border: none;
    padding: 0px;
}
QDockWidget::title {
    background: #191c1f;
    min-height: 80px;
    padding: 5px;
}
QToolTip {
    background: #191c1f;
    border: 1px solid black;
    color: wheat;
    padding: 2px;
}
#dialog {
    background: transparent;
    font-size: 15px;
}
QProgressBar {
    background: "$BACKGROUND";
    border-radius: 2px;
    padding: 1px;
    min-width: 50px;
    text-align: center;
}
QProgressBar::chunk{
    width: 10px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 13px;
    border-radius: 2px;
    padding: 1px;
}
QScrollBar::handle:horizontal {
    background: "$BACKGROUND";
    border-radius: 2px;
    width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #333;
    border-radius: 2px;
    width: 20px;
}
QScrollBar::add-line:horizontal {
    border: none;
    background: transparent;
    height: 0px;
    width: 20px;
}
QScrollBar::sub-line:horizontal {
    border: none;
    background: transparent;
    height: 0px;
    width: 20px;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 13px;
    border-radius: 2px;
    padding: 1px;
    padding-left: 3px;
}
QScrollBar::handle:vertical {
    background: #333;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: #444;
}
QScrollBar::add-line:vertical {
    border: none;
    background: transparent;
    height: 0px;
    width: 0px;
}
QScrollBar::sub-line:vertical {
    border: none;
    background: transparent;
    height: 0px;
    width: 0px;
}
QProgressBar::chunk {
    background: "$MAIN";
    height: 20px;
}
QsciScintilla > QListWidget {
    background: "$BACKGROUND";
    border: 1px solid #252525;
    border-radius: 1px;
    font-size: 14px;
    min-width: 300px;
    padding: 0px 5px;
    margin: 0;
}
QsciScintilla > QListWidget::item{
    border: 1px solid transparent;
    background: transparent;
    color: "$FOREGROUND";
    margin: 0;
}
QsciScintilla QListWidget QScrollBar:vertical{
    width: 0px;
}
QsciScintilla > QListWidget::item:selected{
    border: none;
    outline: none;
    background: rgba(255, 255, 255, 20);
}
QsciScintilla > QListWidget:focus{
    outline: none;
}
QScrollArea {
    background: transparent;
}
QWidget[type="container"]{
    border: 1px solid #333;
    background: #020202;
}
QSpinBox::up-button, QDateTimeEdit::up-button, QDoubleSpinBox::up-button  {
    padding: 0px;
    background: transparent;
}
QSpinBox::down-button, QDateTimeEdit::down-button, QDoubleSpinBox::down-button {
    padding: 0px;
    background: transparent;
}
QSpinBox::down-arrow, QDateTimeEdit::down-arrow, QDoubleSpinBox::down-arrow {
    image: url($/img/style/arrow-down.svg);
    width: 16px;
    height: 16px;
    padding-right: 10px;
}
QSpinBox::up-arrow, QDateTimeEdit::up-arrow, QDoubleSpinBox::up-arrow {
    image: url($/img/style/arrow-up.svg);
    width: 16px;
    height: 16px;
    padding-right: 10px;
}
QAbstractSpinBox,
QDoubleSpinBox,
QDateTimeEdit{
    border: none;
    padding: 0px 4px;
    background-color: "109";
    border-radius: 2px;
    padding-right: 10px;
}

QAbstractSpinBox:hover,
QDoubleSpinBox:hover{
    padding: 0px 4px;
    border-radius: 2px;
    border: none;
    background: "$WIDGET-2-H";
}
QAbstractSpinBox,
QDoubleSpinBox,
QDateTimeEdit{
    border: none;
    padding: 0px 4px;
    background: "$WIDGET-2";
    border-radius: 2px;
    padding-right: 10px;
}

QAbstractSpinBox:hover,
QDoubleSpinBox:hover{
    padding: 0px 4px;
    border-radius: 2px;
    border: none;
    background: "$WIDGET-2-H";
}

QAbstractSpinBox:focus,
QDoubleSpinBox:focus
{
    border: 0px solid "$MAIN";
    border-radius: 2px;
    padding: 0px 4px;
}
QWidget[type="view"]::item{
    background: transparent;
}
QWidget[type="view"]::item:hover{
    background: rgba(255, 255, 255, 5);
}
QWidget[type="popup"]{
    background: #0d0d0d;
    border: 1px solid #191c1f;
}
QWidget[type="icon-button"]:pressed{
    background: "$MAIN";
}

QMenu {
    background: "$WIDGET-2";
    border: 1px solid "$BORDER";
    padding: 0px;
}
QMenu::item {
    margin: 0;
    min-height: 25px;
    border-left: 5px solid transparent;
}
QMenu::item:selected {
    background: "$MAIN";
}

"""


class MintLeaf:
    FUNCTIONS = ["on_save_settings"]

    colors = {
        "background_c": "#0d0d0d",
        "head_c": "#191C1F",
        "border_c": "#97B0B8",
        "shadow_c": "#000000",
        "primary_c": "#32926F"
    }

    palette = {
        "$MAIN": colors.get("primary_c"),
        "$WIDGET-1": colors.get("head_c"),
        "$BACKGROUND": colors.get("background_c"),
        "$BORDER": colors.get("border_c"),
        "$WIDGET-2": "#0D1117",
        "$WIDGET-2-H": "#13181E",
        "$FONT": "Ubuntu Mono",
        "$FONT-SIZE": "13px",
        "$FOREGROUND": "#FFFFFF",
        "$SELECTION-COLOR": "#000000"
    }

    name = "Mint Leaf"

    def load(self):
        theme = _THEME

        for k in self.palette:
            v = self.palette[k]
            theme = theme.replace('"' + k + '"', v)

        return theme

    @staticmethod
    def on_save_settings(kw):
        if not kw.get("self"):
            return

        kw.get("self").main.load_theme()


CLASS = MintLeaf
VERSION = 0.1
TYPE = "theme/qss"
NAME = "MintLeaf"
