from ...pyqt import QUndoCommand


class _Text(QUndoCommand):
    def __init__(self, current_text, new_text):
        super().__init__()
        self.current_text = current_text
        self.new_text = new_text

    def redo(self):
        return self.new_text

    def undo(self):
        return self.current_text


class Clipboard:
    def __init__(self):
        self.text = [0]
        self.index = 0
        self._man = False

    def register(self, text):
        if text and self.text[self.index] != text:
            self.text.append(text)
            self.index += 1

    def undo(self):
        if self.index-1 >= 0:
            self.index -= 1
            return self.text[self.index]
        return 0

    def redo(self):
        if self.index+1 < len(self.text):
            self.index += 1
            return self.text[self.index]
        return 0
