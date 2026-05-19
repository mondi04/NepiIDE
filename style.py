"""
Dark stylesheet — Catppuccin Mocha palette.
"""

DARK_STYLE = """
/* ── Global ─────────────────────────────────────────────────────────── */
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", "SF Pro Text", sans-serif;
    font-size: 12px;
}

QMainWindow {
    background: #1e1e2e;
}

/* ── Splitter ────────────────────────────────────────────────────────── */
QSplitter::handle {
    background: #313244;
}
QSplitter::handle:horizontal {
    width: 4px;
}
QSplitter::handle:vertical {
    height: 4px;
}
QSplitter::handle:hover {
    background: #585b70;
}

/* ── Menu bar ────────────────────────────────────────────────────────── */
QMenuBar {
    background: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px 4px;
}
QMenuBar::item {
    padding: 4px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #313244;
}

QMenu {
    background: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #313244;
}
QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 4px 8px;
}

/* ── Toolbar ─────────────────────────────────────────────────────────── */
QToolBar {
    background: #181825;
    border-bottom: 1px solid #313244;
    padding: 2px 6px;
    spacing: 4px;
}
QToolButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QToolButton:hover {
    background: #313244;
}
QToolButton:pressed {
    background: #45475a;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #1e1e2e;
}
QTabBar {
    background: #181825;
}
QTabBar::tab {
    background: #181825;
    color: #6c7086;
    padding: 5px 14px;
    border: none;
    border-right: 1px solid #313244;
    min-width: 80px;
}
QTabBar::tab:selected {
    background: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 2px solid #cba6f7;
}
QTabBar::tab:hover:!selected {
    background: #262637;
    color: #bac2de;
}
QTabBar::close-button {
    image: none;
    subcontrol-position: right;
}

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #1e1e2e;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1e1e2e;
    height: 8px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #585b70;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {
    background: #313244;
    color: #cdd6f4;
    border: none;
    border-radius: 4px;
    padding: 4px 12px;
}
QPushButton:hover {
    background: #45475a;
}
QPushButton:pressed {
    background: #585b70;
}
QPushButton:disabled {
    color: #45475a;
}

/* ── Input / LineEdit ────────────────────────────────────────────────── */
QLineEdit {
    background: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus {
    border-color: #cba6f7;
}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel {
    color: #cdd6f4;
}

/* ── Status bar ──────────────────────────────────────────────────────── */
QStatusBar {
    background: #181825;
    border-top: 1px solid #313244;
    color: #6c7086;
    font-size: 11px;
}

/* ── Tree view (file tree) ───────────────────────────────────────────── */
QTreeView {
    background: #181825;
    border: none;
    color: #cdd6f4;
    show-decoration-selected: 1;
}
QTreeView::item {
    padding: 2px 4px;
    border-radius: 3px;
}
QTreeView::item:selected {
    background: #313244;
}
QTreeView::item:hover {
    background: #262637;
}
QTreeView::branch {
    background: #181825;
}
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

/* ── Checkbox ────────────────────────────────────────────────────────── */
QCheckBox {
    color: #cdd6f4;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #585b70;
    border-radius: 3px;
    background: #1e1e2e;
}
QCheckBox::indicator:checked {
    background: #cba6f7;
    border-color: #cba6f7;
}

/* ── ComboBox ────────────────────────────────────────────────────────── */
QComboBox {
    background: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 4px;
    padding: 3px 8px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #181825;
    border: 1px solid #313244;
    selection-background-color: #313244;
}

/* ── Message box ─────────────────────────────────────────────────────── */
QMessageBox {
    background: #1e1e2e;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ── Input dialog ────────────────────────────────────────────────────── */
QInputDialog {
    background: #1e1e2e;
}
"""