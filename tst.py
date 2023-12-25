import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTranslator

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        btn = QPushButton()
        btn.setText(self.tr("Hello World"))
        label = QLabel()
        label.setText(self.tr("How are you doing !"))

        layout.addWidget(btn)
        layout.addWidget(label)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator = QTranslator()
    translator.load("/home/badr_eddin/Desktop/github/qtpyeditor/translations/qt_zh_CN.ts")
    app.installTranslator(translator)
    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
