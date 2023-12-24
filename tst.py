import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create a child widget to embed xterm
        xterm_container = QWidget(self)
        xterm_container.setGeometry(0, 0, 640, 480)  # Set the size as needed
        xterm_container.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)

        # Get the native window ID of the child widget
        window_id = int(xterm_container.winId())
        print(window_id)
        # Use xterm with the -embed option
        xterm_command = f"xterm -embed {window_id}"
        # You may need to adjust the xterm options based on your requirements

        # Start xterm as a subprocess
        import subprocess
        subprocess.Popen(xterm_command, shell=True)

        layout.addWidget(xterm_container)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
