from ..pyqt import QAction, QMenu, QDockWidget


class ComponentsAction(QAction):
    def __init__(self, parent=None, text="", on_trigger=None, dock=None):
        super(ComponentsAction, self).__init__(parent)
        self.setText(text)
        self.on_trigger = on_trigger
        self.dock = dock
        self.triggered.connect(self.__tr)  # Type: ignore

    def __tr(self, ch):
        if self.on_trigger:
            self.on_trigger(ch, self.dock)


class ComponentsMenu(QMenu):
    def __init__(self, parent=None):
        super(ComponentsMenu, self).__init__(parent)

    def load(self, components, callback):
        for nm in components:
            if isinstance(components[nm], QDockWidget):
                dock: QDockWidget = components[nm]
                action = ComponentsAction(self, dock.windowTitle(), callback, dock)
                dock.visibilityChanged.connect(action.setChecked)  # Type: ignore
                action.setCheckable(True)
                action.setChecked(not dock.isHidden())
                self.addAction(action)
