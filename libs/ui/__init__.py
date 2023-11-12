from .editor import EditorWidget
from .inspector import Inspector, DemoParserRule
from .imports_editor import ImportsEditor
from .property_editor import PropertyEditor
from .dialogs import InformUser, KivyInnerWindow, Messenger, SearchTip, Dialog, DraggableFrame, Pointer, InLineInput
from .toolbar import Bar
from .project_tree import PTree
from .demo_kv_app import get_kivy_window_id
from .console import Console
from .project_manager import PCreator

COMPONENTS = [InformUser, Inspector, PTree, Console, Messenger, PropertyEditor, ImportsEditor, EditorWidget,
              KivyInnerWindow, SearchTip, Bar]

