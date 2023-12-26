import os.path

from ..dialogs import CustomDockWidget
from ...pyqt import QFrame, QIcon, loadUi, QTreeWidgetItem, QTreeWidget, Qt
from ...utils import import_, settings, comp_update_inspector, translate


class EventsEditor(CustomDockWidget):
    ui = "head"
    ui_type = QFrame
    name = "actions"

    class ActionType:
        Function = 0
        Property = 1

    def __init__(self, parent, main):
        super(EventsEditor, self).__init__(parent)
        self.main = main
        self.events_map = {}
        self.events_parents = {}
        self.events_line_map = {}
        self.line_events_map = {}
        self.event_callback_going_to_change = None
        self._added_sub_items = []
        self.added_events = []
        self.events = settings.pull("kivy/actions")
        self.widget = loadUi(import_("ui/actions-editor.ui", 'io'))

        self.setWidget(self.widget)

    def initialize(self, _):
        self.main.dock_it(self, "ra")
        self.setWindowTitle(translate("Events"))
        # configuring elements
        self.widget.event.addItems(list((self.events or {}).keys()))
        self.widget.add_event.setIcon(QIcon(import_("img/editors/actions/add.png")))
        self.widget.minus_event.setIcon(QIcon(import_("img/editors/actions/remove.png")))

        self.widget.add_event.clicked.connect(self.add_event)
        self.widget.minus_event.clicked.connect(self.remove_event)
        self.widget.events.itemChanged.connect(self._event_item_changed)
        self.widget.events.itemDoubleClicked.connect(self._event_item_going_to_change)

    # ---------------
    def _event_item_going_to_change(self, item):
        self.event_callback_going_to_change = item.text(0)

    def _event_item_changed(self, item: QTreeWidgetItem):
        line = self.events_line_map.get(id(item))
        ins_item = self.main.element("inspector.tree").selectedItems()

        if not ins_item:
            return

        ins_item = ins_item[0]

        event = self.events_parents.get(id(item))

        self.events_map[id(ins_item)][event.text(0)].remove(self.event_callback_going_to_change)
        self.events_map[id(ins_item)][event.text(0)].append(item.text(0))

        self.main.on("update_event", {"callback": item.text(0)})
        os.environ["editor-editing"] = "0"
        comp_update_inspector(line)

    # ---------------
    def done(self, n=True):
        self.widget.events.clear()
        self._added_sub_items.clear()
        self.added_events.clear()

        if n:
            self.events_line_map.clear()
            self.line_events_map.clear()
            self.events_map.clear()

    def load_events(self, events, parent):
        self.done(False)

        self.events_parents.clear()

        for event in events:
            values = events[event].value.split("\n")
            item = self.add_event(action=event, parent=[parent])
            self.line_events_map.update({events[event].line: item})

            for value in values:
                item2 = self.add_event([item], value, [parent])
                self.events_line_map.update({id(item2): events[event].line})

    def events_of(self, item, lv1, lv2, tab):
        events = self.events_map.get(id(item))

        if not events:
            return

        events_l = ""

        for event in events:
            if len(events[event]) == 0:
                events_l += lv1 * tab + f"{event}: print()\n"

            elif len(events[event]) == 1:
                events_l += lv1 * tab + f"{event}: {events[event][0]}\n"

            else:
                events_l += lv1 * tab + f"{event}:\n"
                for item in events[event]:
                    events_l += lv2 * tab + item + "\n"

        return events_l

    # ---------------
    def remove_event(self):
        ins_item = self.main.element("inspector.tree").selectedItems()
        tree: QTreeWidget = self.widget.events

        if not ins_item:
            return

        ins_item = ins_item[0]

        item: [QTreeWidgetItem] = tree.selectedItems()
        if not item:
            return

        item = item[0]
        line = self.events_line_map.get(id(item))

        events = self.events_map.get(id(ins_item))

        if not events:
            return

        # this means that the current item is not property | event, but it is a callback
        if id(item) in self.events_parents:
            parent: QTreeWidgetItem | None = self.events_parents.get(id(item))

            if parent:
                parent.removeChild(item)

            self.events_map[id(ins_item)][parent.text(0)].remove(item.text(0))

        else:
            self.events_map[id(ins_item)] = {}
            tree.takeTopLevelItem(tree.indexOfTopLevelItem(item))

        os.environ["editor-editing"] = "0"

        comp_update_inspector(line)

    def add_event(self, event_item=None, action=None, parent=None):
        ins_item = parent or self.main.element("inspector.tree").selectedItems()
        action = action or self.widget.event.currentText()

        if not ins_item:
            return

        ins_item = ins_item[0]

        tree: QTreeWidget = self.widget.events
        event_item: [QTreeWidgetItem] = event_item or tree.selectedItems()

        # add sub item
        ps = False
        if event_item:
            event_item = event_item[0]
            ps = True

        if ps and id(event_item) not in self._added_sub_items:

            item = QTreeWidgetItem()
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setText(0, action or 'print("event callback")')

            self.events_map[id(ins_item)][event_item.text(0)].append(item.text(0))
            self.events_parents.update({id(item): event_item})

            event_item.addChild(item)
            tree.expandItem(event_item)

            self._added_sub_items.append(id(item))

        else:
            item = QTreeWidgetItem()

            item.setText(0, action)
            self.added_events.append(action)
            if id(ins_item) not in self.events_map:
                self.events_map[id(ins_item)] = {}

            self.events_map[id(ins_item)].update({action: []})

            tree.addTopLevelItem(item)

        return item
