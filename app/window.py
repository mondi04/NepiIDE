"""
MainWindow — clean, focused Python IDE layout.
Native toolbar at top, minimal chrome, no noise.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QLabel,
    QTabWidget, QPushButton, QMenu, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont, QColor, QPalette

from app.filetree.filetree import FileTree
from app.editor.editor_tab import EditorTabWidget
from app.terminal.terminal import TerminalWidget
from app.git.git_panel import GitPanel
from app.flask.flask_runner import FlaskRunner
from app.style import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self, start_path: str | None = None):
        super().__init__()
        self.setWindowTitle("NepiIDE")
        self.resize(1400, 900)
        self.setStyleSheet(DARK_STYLE)

        self._settings = QSettings("NepiIDE", "NepiIDE")
        self._current_project: str | None = None

        self._build_toolbar()
        self._build_ui()
        self._build_menu()
        self._restore_state()

        if start_path:
            self.open_folder(start_path)
        else:
            last = self._settings.value("last_project")
            if last and Path(last).exists():
                self.open_folder(last)

    # ---------------------------------------------------------------- Toolbar (native) --

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setObjectName("mainToolbar")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(16, 16))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        # Open folder
        open_act = QAction("󰝰  Open", self)
        open_act.setToolTip("Open project folder  Ctrl+K")
        open_act.setShortcut(QKeySequence("Ctrl+K"))
        open_act.triggered.connect(self.prompt_open_folder)
        tb.addAction(open_act)

        # Save
        save_act = QAction("  Save", self)
        save_act.setToolTip("Save current file  Ctrl+S")
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self.editor_tabs_save)
        tb.addAction(save_act)

        tb.addSeparator()

        # Run
        run_act = QAction("▶  Run", self)
        run_act.setToolTip("Run current Python file  F5")
        run_act.setShortcut(QKeySequence("F5"))
        run_act.triggered.connect(self._run_current)
        tb.addAction(run_act)

        # Flask
        flask_act = QAction("🌶  Flask", self)
        flask_act.setToolTip("Start / stop Flask app  F6")
        flask_act.setShortcut(QKeySequence("F6"))
        flask_act.triggered.connect(self._flask_toggle)
        tb.addAction(flask_act)

        tb.addSeparator()

        # Git refresh
        git_act = QAction("⎇  Git", self)
        git_act.setToolTip("Refresh Git status")
        git_act.triggered.connect(self._refresh_git)
        tb.addAction(git_act)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        # Project name label (right-aligned)
        self._project_label = QLabel("no project")
        self._project_label.setStyleSheet(
            "color: #30363d; font-size: 11px; padding-right: 12px;"
        )
        tb.addWidget(self._project_label)

        # Store refs for later wiring
        self._toolbar = tb

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Outer horizontal splitter: sidebar | main ──────────────────────
        self._outer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._outer_splitter.setHandleWidth(1)
        self._outer_splitter.setChildrenCollapsible(False)

        # ── Left sidebar: file-tree + git-panel ────────────────────────────
        self._sidebar_splitter = QSplitter(Qt.Orientation.Vertical)
        self._sidebar_splitter.setHandleWidth(1)
        self._sidebar_splitter.setChildrenCollapsible(False)

        # File tree with header
        filetree_container = QWidget()
        filetree_container.setStyleSheet("background: #0d1117;")
        ft_layout = QVBoxLayout(filetree_container)
        ft_layout.setContentsMargins(0, 0, 0, 0)
        ft_layout.setSpacing(0)

        ft_header = QLabel("EXPLORER")
        ft_header.setObjectName("section_label")
        ft_layout.addWidget(ft_header)

        self.file_tree = FileTree()
        self.file_tree.setMinimumWidth(160)
        ft_layout.addWidget(self.file_tree)

        # Git panel with header
        git_container = QWidget()
        git_container.setStyleSheet("background: #0d1117;")
        git_layout = QVBoxLayout(git_container)
        git_layout.setContentsMargins(0, 0, 0, 0)
        git_layout.setSpacing(0)

        git_header = QLabel("SOURCE CONTROL")
        git_header.setObjectName("section_label")
        git_layout.addWidget(git_header)

        self.git_panel = GitPanel()
        self.git_panel.setMinimumHeight(120)
        git_layout.addWidget(self.git_panel)

        self._sidebar_splitter.addWidget(filetree_container)
        self._sidebar_splitter.addWidget(git_container)
        self._sidebar_splitter.setSizes([520, 220])
        self._sidebar_splitter.setMinimumWidth(180)

        # ── Center+bottom splitter: editor | terminal ──────────────────────
        self._center_splitter = QSplitter(Qt.Orientation.Vertical)
        self._center_splitter.setHandleWidth(1)
        self._center_splitter.setChildrenCollapsible(False)

        self.editor_tabs = EditorTabWidget()
        self.editor_tabs.setMinimumHeight(200)
        self.editor_tabs.setStyleSheet("""
            QTabBar { background: #0d1117; border-bottom: 1px solid #1c1f26; }
            QTabBar::tab { padding: 7px 18px; font-size: 12px; }
        """)

        self._bottom_widget = self._build_bottom_panel()
        self._bottom_widget.setMinimumHeight(100)

        self._center_splitter.addWidget(self.editor_tabs)
        self._center_splitter.addWidget(self._bottom_widget)
        self._center_splitter.setSizes([620, 240])

        self._outer_splitter.addWidget(self._sidebar_splitter)
        self._outer_splitter.addWidget(self._center_splitter)
        self._outer_splitter.setSizes([210, 1190])

        root_layout.addWidget(self._outer_splitter)

        # ── Status bar ─────────────────────────────────────────────────────
        self._status = QStatusBar()
        self._status.setFixedHeight(22)
        self.setStatusBar(self._status)

        self._status_label = QLabel("No project open")
        self._status_label.setStyleSheet("color: #6e7681; padding-left: 4px;")
        self._status.addWidget(self._status_label)

        # Right-side status indicators
        self._python_label = QLabel("Python 3")
        self._python_label.setStyleSheet(
            "color: #3b82f6; padding: 0 10px; font-size: 11px;"
        )
        self._status.addPermanentWidget(self._python_label)

        # ── Wire signals ───────────────────────────────────────────────────
        self.file_tree.file_opened.connect(self.editor_tabs.open_file)
        self.editor_tabs.status_changed.connect(self._on_editor_changed)
        self.git_panel.refresh_requested.connect(self._refresh_git)
        self.flask_runner.log_line.connect(self._terminal.append_output)

    def _build_bottom_panel(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._bottom_tabs = QTabWidget()
        self._bottom_tabs.setTabPosition(QTabWidget.TabPosition.South)
        self._bottom_tabs.setDocumentMode(True)
        self._bottom_tabs.setStyleSheet("""
            QTabBar::tab { padding: 5px 14px; font-size: 11px; }
            QTabWidget::pane { border-top: 1px solid #1c1f26; }
        """)

        self._terminal = TerminalWidget()
        self._bottom_tabs.addTab(self._terminal, "Terminal")

        self.flask_runner = FlaskRunner()
        self._bottom_tabs.addTab(self.flask_runner, "Flask")

        # New terminal button
        new_term_btn = QPushButton("+")
        new_term_btn.setFixedSize(22, 22)
        new_term_btn.setToolTip("New terminal tab")
        new_term_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #6e7681; border: none; font-size: 14px; }"
            "QPushButton:hover { color: #e6edf3; }"
        )
        new_term_btn.clicked.connect(self._add_terminal_tab)
        self._bottom_tabs.setCornerWidget(new_term_btn, Qt.Corner.TopLeftCorner)

        layout.addWidget(self._bottom_tabs)
        return widget

    # ---------------------------------------------------------------- Menu --

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")
        self._act(file_menu, "&Open Folder…", self.prompt_open_folder, QKeySequence("Ctrl+K"))
        self._act(file_menu, "&New File", self._new_file, QKeySequence.StandardKey.New)
        self._act(file_menu, "&Save", self.editor_tabs_save, QKeySequence.StandardKey.Save)
        self._act(file_menu, "Save &As…", self._save_as, QKeySequence.StandardKey.SaveAs)
        file_menu.addSeparator()
        self._act(file_menu, "&Quit", self.close, QKeySequence.StandardKey.Quit)

        view_menu = mb.addMenu("&View")
        self._act(view_menu, "Toggle &Sidebar",   self._toggle_sidebar, QKeySequence("Ctrl+B"))
        self._act(view_menu, "Toggle &Terminal",  self._toggle_terminal, QKeySequence("Ctrl+`"))
        self._act(view_menu, "Toggle &Git Panel", self._toggle_git, QKeySequence("Ctrl+Shift+G"))

        git_menu = mb.addMenu("&Git")
        self._act(git_menu, "&Refresh Status", self._refresh_git, QKeySequence("Ctrl+Shift+R"))
        self._act(git_menu, "&Stage All",      self.git_panel.stage_all)
        self._act(git_menu, "&Commit…",        self.git_panel.commit)
        self._act(git_menu, "&Pull",           self.git_panel.pull)
        self._act(git_menu, "P&ush",           self.git_panel.push)

        run_menu = mb.addMenu("&Run")
        self._act(run_menu, "&Run Current File", self._run_current, QKeySequence("F5"))
        self._act(run_menu, "Run &Flask App",    self._flask_toggle,  QKeySequence("F6"))

    def _act(self, menu: QMenu, label: str, slot, shortcut=None) -> QAction:
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # ------------------------------------------------------------- Slots --

    def editor_tabs_save(self):
        if hasattr(self, "editor_tabs"):
            self.editor_tabs.save_current()

    def _new_file(self):
        if hasattr(self, "editor_tabs"):
            self.editor_tabs.new_file()

    def _save_as(self):
        if hasattr(self, "editor_tabs"):
            self.editor_tabs.save_as()

    def prompt_open_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Open Project Folder", str(Path.home())
        )
        if path:
            self.open_folder(path)

    def open_folder(self, path: str):
        self._current_project = path
        name = Path(path).name
        self.setWindowTitle(f"NepiIDE — {name}")
        self.file_tree.set_root(path)
        self.git_panel.set_repo(path)
        self.flask_runner.set_cwd(path)
        self._terminal.set_cwd(path)
        self._settings.setValue("last_project", path)
        self._status_label.setText(path)
        self._project_label.setText(name)

    def _run_current(self):
        filepath = self.editor_tabs.current_filepath()
        if not filepath:
            self._status_label.setText("No file to run")
            return
        self.editor_tabs.save_current()
        cwd = self._current_project or str(Path(filepath).parent)
        self._terminal.run_command(f'python "{filepath}"', cwd=cwd)
        self._bottom_tabs.setCurrentIndex(0)

    def _flask_toggle(self):
        self.flask_runner.start_or_stop()
        self._bottom_tabs.setCurrentWidget(self.flask_runner)

    def _refresh_git(self):
        if self._current_project:
            self.git_panel.set_repo(self._current_project)

    def _toggle_sidebar(self):
        self._sidebar_splitter.setVisible(not self._sidebar_splitter.isVisible())

    def _toggle_terminal(self):
        self._bottom_widget.setVisible(not self._bottom_widget.isVisible())

    def _toggle_git(self):
        # find git_container (parent of git_panel)
        c = self.git_panel.parent()
        if c:
            c.setVisible(not c.isVisible())

    def _add_terminal_tab(self):
        t = TerminalWidget()
        if self._current_project:
            t.set_cwd(self._current_project)
        n = self._bottom_tabs.count()  # before insert
        idx = self._bottom_tabs.insertTab(n - 1, t, f"Terminal {n}")
        self._bottom_tabs.setCurrentIndex(idx)

    def _on_editor_changed(self, filepath: str):
        self._status_label.setText(filepath)

    # -------------------------------------------------------- State restore --

    def _restore_state(self):
        geo = self._settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)
        for key, splitter in [
            ("outerSplitter",   self._outer_splitter),
            ("centerSplitter",  self._center_splitter),
            ("sidebarSplitter", self._sidebar_splitter),
        ]:
            saved = self._settings.value(key)
            if saved:
                splitter.restoreState(saved)

    def closeEvent(self, event):
        self._settings.setValue("geometry",       self.saveGeometry())
        self._settings.setValue("windowState",    self.saveState())
        self._settings.setValue("outerSplitter",  self._outer_splitter.saveState())
        self._settings.setValue("centerSplitter", self._center_splitter.saveState())
        self._settings.setValue("sidebarSplitter",self._sidebar_splitter.saveState())
        if not self.editor_tabs.close_all():
            event.ignore()
            return
        self.flask_runner.stop()
        event.accept()