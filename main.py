"""
NepiIDE — Lightweight Python Desktop IDE
Run: python main.py [optional: path/to/project]
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NepiIDE")
    app.setOrganizationName("NepiIDE")

    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

    start_path = None
    if len(sys.argv) > 1:
        p = Path(sys.argv[1]).resolve()
        if p.exists():
            start_path = str(p)

    window = MainWindow(start_path=start_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()