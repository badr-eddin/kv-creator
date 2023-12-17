import re

import jedi
from jedi import Script
import ast

from jedi.api.classes import Name, BaseSignature

file_path = "hh.py"
text = """
import os
import re
import threading
# os.environ['KIVY_NO_CONSOLELOG'] = '0'
from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


Config.set('input', 'mouse', 'mouse,multi''touch_on_demand')

class KvApp(App):
    title = "KivyApp"
    
    def __init__(self, **kwargs):
        super(KvApp, self).__init__(**kwargs)
        self.file = "$FILE"
        self.f_root, self.f_name = os.path.split(self.file)
        self.event_handler = TxtFileHandler(self.f_name)
        self.observer = Observer()
        self.toggle_wdog()

    def build(self):
        return Builder.load_file(self.file)

    def toggle_wdog(self):
        m = self.observer.is_alive()
        if not m:
            threading.Thread(target=self._threaded_watcher).start()
        else:
            self.observer.stop()
            self.observer.join()

    def _threaded_watcher(self):
        self.event_handler.on_file_modified = self._kv_modified_hook
        self.observer.schedule(self.event_handler, self.f_root, recursive=True)
        self.observer.start()

    def _kv_modified_hook(self, *_):
        self.root.clear_widgets()
        Builder.unload_file(self.file)
        self.root = self.build()
        self.run()
        
    @property
    def init(self):
        return "init"

    @staticmethod
    def inits(self):
        return "init"

    def on_stop(self):
        self.toggle_wdog()


if __name__ == "__main__":
    app = KvApp()
    app.run()
"""

tree = ast.parse(text, filename=file_path)

# classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
# functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
# variables = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)]

#
# for node in ast.walk(tree):
#     if isinstance(node, ast.ClassDef):
#         node: ast.ClassDef
#         for it in node.bases:
#             for it2 in ast.walk(it):
#                 print(dir(it2))

# def show_info(functionNode):
#     print("Function name:", functionNode.name)
#     print("Args:")
#     for arg in functionNode.args.args:
#         #import pdb; pdb.set_trace()
#         print("\tParameter name:", arg.arg)


# filename = "/home/badr_eddin/Desktop/Projects/KivyCreator/.trash/test.py"
# with open(filename) as file:
#     node = ast.parse(file.read())

# functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
# classes = [n for n in node.body if isinstance(n, ast.ClassDef)]

# for function in functions:
#     show_info(function)

# for class_ in classes:
#     print(dir(class_.bases[0].id))
# print("Class name:", class_.name)
# methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
# for method in methods:
#     show_info(method)


KIVY_APP_SRC = "kivy.app.App"


script = jedi.Script(text)


# @staticmethod
def kivy_app_import(code):
    for imp in jedi.Script(code).get_names(definitions=True):

        if imp.full_name == KIVY_APP_SRC:
            return {imp.name: imp.full_name}


# imports = kivy_app_import(text)

# for name in script.get_names(references=True):
#     name: Name
#     if name.type == "class":
#         print(name.is_side_effect())

        # if name.full_name == KIVY_APP_SRC:
        #     print(name.name)


import ast


def get_classes(path):
    with open(path) as fh:
        root = ast.parse(fh.read(), path)
    classes = []
    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.ClassDef):
            classes.append(node)
        else:
            continue
    return classes


# for c in get_classes('/home/badr_eddin/Desktop/Projects/KivyCreator/.trash/test.py'):
#
#     for k in ast.walk(c):
#         if isinstance(k, ast.FunctionDef):
#             for d in k.decorator_list:
#                 print(getattr(d, "id", None) or getattr(d, "value").id)
#         # if isinstance(k):
#
#     print("-"*20)


tx = open('/home/badr_eddin/Desktop/Projects/KivyCreator/.trash/test.py', 'r').read()

sc = Script(tx)
apps = ['KvApp', 'Application']

app = None

for name in sc.get_names():
    if name.type == "class":
        name: Name

        inherit = re.finditer(r"^class\s+\w+\((?P<inherit>\w+)\):$", tx.splitlines(False)[name.line - 1])
        inherit = [inh.group("inherit") for inh in inherit]


