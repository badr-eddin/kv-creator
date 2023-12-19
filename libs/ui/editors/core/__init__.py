from ....kivy import KivyParser
from ....utils import debug


class GlobalComposer:
    def __init__(self, main):
        self.__events = {}
        self.thread = KivyParser(main)
        self.main = main

        self.thread.on_error.connect(self.parsing_crashed)
        self.thread.on_finish.connect(self.parsing_finished)

    def on(self, name, func=None):
        if func:
            if not self.__events.get(name):
                self.__events[str(name)] = [func]

            self.__events[str(name)].append(func)

    def parse(self, code, path):
        self.thread.trigger(code, path)
        self.update(code, path, True)

    def parsing_crashed(self,  _, errors):
        debug("kivy::parsing crashed !", _c="w")
        self._on_event("error", (errors, ))

    def parsing_finished(self, parsed, obj):
        debug("kivy::parsing finished .")
        self._on_event("finish", (parsed, obj))

    def _on_event(self, event, args):
        for func in self.__events.get(event) or []:
            if callable(func):
                func(*args)

    def update_inspector(self, line=0):
        func = self.main.element("inspector.save")
        rem = self.main.element("inspector.select_last_element")

        func()
        rem(self.main.element("editor.widget").currentWidget(), line)

    def update(self, code, path, rec=False):
        self._on_event("update", (code, path))

        if not rec:
            self.thread.trigger(code, path)
