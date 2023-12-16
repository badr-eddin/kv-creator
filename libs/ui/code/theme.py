from ...pyqt import QColor


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
