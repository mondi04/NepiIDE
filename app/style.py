"""
Dark stylesheet — refined minimal IDE palette.
Inspired by: Zed, Helix, modern terminal-first editors.
Font stack: JetBrains Mono for code, 'Geist' / system sans for UI.
"""

DARK_STYLE = """
/* ── Reset & Base ───────────────────────────────────────────────────── */
* {
    outline: none;
}
QWidget {
    background-color: #0f1117;
    color: #c9d1d9;
    font-family: "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
    font-size: 12px;
    border: none;
}
QMainWindow, QDialog {
    background: #0f1117;
}

/* ── Splitter ────────────────────────────────────────────────────────── */
QSplitter::handle {
    background: #1c1f26;
}
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
QSplitter::handle:hover       { background: #3b82f6; }

/* ── Menu bar ────────────────────────────────────────────────────────── */
QMenuBar {
    background: #0f1117;
    border-bottom: 1px solid #1c1f26;
    padding: 0px 2px;
    spacing: 0px;
}
QMenuBar::item {
    padding: 5px 10px;
    background: transparent;
    color: #8b949e;
    border-radius: 4px;
}
QMenuBar::item:selected, QMenuBar::item:pressed {
    background: #1c1f26;
    color: #e6edf3;
}

QMenu {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 5px 28px 5px 12px;
    border-radius: 4px;
    color: #c9d1d9;
}
QMenu::item:selected {
    background: #1f2937;
    color: #e6edf3;
}
QMenu::separator {
    height: 1px;
    background: #21262d;
    margin: 3px 8px;
}
QMenu::indicator {
    width: 14px;
    height: 14px;
}

/* ── Toolbar ─────────────────────────────────────────────────────────── */
QToolBar {
    background: #0f1117;
    border-bottom: 1px solid #1c1f26;
    padding: 3px 8px;
    spacing: 2px;
}
QToolBar::separator {
    width: 1px;
    background: #1c1f26;
    margin: 4px 6px;
}
QToolButton {
    background: transparent;
    border: none;
    border-radius: 5px;
    padding: 4px 10px;
    color: #8b949e;
    font-size: 12px;
    font-weight: 500;
}
QToolButton:hover {
    background: #1c1f26;
    color: #e6edf3;
}
QToolButton:pressed {
    background: #21262d;
    color: #3b82f6;
}
QToolButton:checked {
    background: #1f2937;
    color: #3b82f6;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #0f1117;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #6e7681;
    padding: 6px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
}
QTabBar::tab:selected {
    background: transparent;
    color: #e6edf3;
    border-bottom: 2px solid #3b82f6;
}
QTabBar::tab:hover:!selected {
    color: #c9d1d9;
    background: #161b22;
}
QTabBar::close-button {
    subcontrol-position: right;
}

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #21262d;
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #30363d; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #21262d;
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background: #30363d; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {
    background: #161b22;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 5px;
    padding: 4px 12px;
    font-size: 12px;
}
QPushButton:hover {
    background: #1c1f26;
    border-color: #30363d;
    color: #e6edf3;
}
QPushButton:pressed {
    background: #21262d;
}
QPushButton:disabled {
    color: #30363d;
    border-color: #1c1f26;
}

/* ── LineEdit ────────────────────────────────────────────────────────── */
QLineEdit {
    background: #161b22;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 5px;
    padding: 4px 8px;
    selection-background-color: #1f2937;
}
QLineEdit:focus {
    border-color: #3b82f6;
    background: #0d1117;
}
QLineEdit::placeholder {
    color: #30363d;
}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel { color: #8b949e; }

/* ── Status bar ──────────────────────────────────────────────────────── */
QStatusBar {
    background: #0d1117;
    border-top: 1px solid #1c1f26;
    color: #6e7681;
    font-size: 11px;
    padding: 0 8px;
}
QStatusBar::item { border: none; }

/* ── Tree view ───────────────────────────────────────────────────────── */
QTreeView {
    background: #0d1117;
    border: none;
    color: #c9d1d9;
    show-decoration-selected: 1;
    font-size: 12px;
}
QTreeView::item {
    padding: 3px 6px;
    border-radius: 3px;
    height: 22px;
}
QTreeView::item:selected {
    background: #1f2937;
    color: #e6edf3;
}
QTreeView::item:hover:!selected {
    background: #161b22;
}
QTreeView::branch {
    background: #0d1117;
}

/* ── List widget ─────────────────────────────────────────────────────── */
QListWidget {
    background: #0d1117;
    border: none;
    color: #c9d1d9;
    font-size: 12px;
}
QListWidget::item {
    padding: 3px 6px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background: #1f2937;
    color: #e6edf3;
}
QListWidget::item:hover:!selected {
    background: #161b22;
}

/* ── TextEdit ────────────────────────────────────────────────────────── */
QTextEdit {
    background: #0d1117;
    color: #c9d1d9;
    border: none;
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", Consolas, monospace;
    font-size: 12px;
    selection-background-color: #1f2937;
}

/* ── Checkbox ────────────────────────────────────────────────────────── */
QCheckBox {
    color: #8b949e;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #30363d;
    border-radius: 3px;
    background: #0d1117;
}
QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}
QCheckBox::indicator:hover {
    border-color: #58a6ff;
}

/* ── ComboBox ────────────────────────────────────────────────────────── */
QComboBox {
    background: #161b22;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 5px;
    padding: 3px 8px;
}
QComboBox:focus { border-color: #3b82f6; }
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 4px;
    selection-background-color: #1f2937;
}

/* ── Splitter sidebar label ──────────────────────────────────────────── */
QLabel#section_label {
    color: #30363d;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 8px 10px 4px 10px;
}

/* ── Message box ─────────────────────────────────────────────────────── */
QMessageBox { background: #161b22; }
QMessageBox QPushButton { min-width: 72px; }

/* ── Input dialog ────────────────────────────────────────────────────── */
QInputDialog { background: #161b22; }
"""