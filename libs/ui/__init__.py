from .code import EditorWidget

from .dialogs import InformUser, Messenger, SearchTip
from .panels import ToolBar, Console
from .editors import Inspector, Properties, Imports
from .project import ProjectTree, ProjectCreator


COMPONENTS = [
    InformUser,
    Inspector,
    ProjectTree,
    Messenger,
    Properties,
    Console,
    Imports,
    EditorWidget,
    SearchTip,
    ToolBar
]

