import psutil
from xdo import Xdo


class HookParserRule:
    name: str
    properties: dict
    id: str
    value: str


def get_kivy_window_id(pid):
    x = Xdo()
    parent = psutil.Process(pid)

    for child in parent.children(recursive=True):
        win = x.search_windows(pid=child.pid)
        if win:
            return win[0]

