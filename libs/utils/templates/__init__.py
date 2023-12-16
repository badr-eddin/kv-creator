from . import standard


class Addons:
    ICON: str


class Plugin:
    CLASS: object | Addons
    VERSION: int
    TYPE: str
    NAME: str
