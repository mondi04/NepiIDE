"""
MainWindow — frei konfigurierbare Splits:
  - Links:   Dateibaum + Git-Panel (vertikaler Splitter)
  - Mitte:   Editor-Tabs
  - Unten:   Terminal-Tabs + Flask-Runner
  - Alle Splits per QSplitter frei verschiebbar
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QLabel,
    QTabWidget, QPushButton, QMenu, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont

from core.filetree import FileTree
from core.editor_tab import EditorTabWidget
from core.terminal import TerminalWidget
from core.git_panel import GitPanel
from core.flask_runner import FlaskRunner
from core.style import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self, start_path: str | None = None):
        super().__init__()
        self.setWindowTitle("PyIDE")
        self.resize(1400, 900)
        self.setStyleSheet(DARK_STYLE)

        self._settings = QSettings("pyide", "PyIDE")
        self._current_project: str | None = None

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._restore_state()

        if start_path:
            self.open_folder(start_path)
        else:
            last = self._settings.value("last_project")
            if last and Path(last).exists():
                self.open_folder(last)

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Outer horizontal splitter: sidebar | main ──────────────────────
        self._outer_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._outer_splitter.setHandleWidth(4)
        self._outer_splitter.setChildrenCollapsible(False)

        # ── Left sidebar: file-tree + git-panel ────────────────────────────
        self._sidebar_splitter = QSplitter(Qt.Orientation.Vertical)
        self._sidebar_splitter.setHandleWidth(4)
        self._sidebar_splitter.setChildrenCollapsible(False)

        self.file_tree = FileTree()
        self.file_tree.setMinimumWidth(160)
        self.git_panel = GitPanel()
        self.git_panel.setMinimumHeight(120)

        self._sidebar_splitter.addWidget(self.file_tree)
        self._sidebar_splitter.addWidget(self.git_panel)
        self._sidebar_splitter.setSizes([500, 200])
        self._sidebar_splitter.setMinimumWidth(180)

        # ── Center+bottom splitter: editor | terminal ──────────────────────
        self._center_splitter = QSplitter(Qt.Orientation.Vertical)
        self._center_splitter.setHandleWidth(4)
        self._center_splitter.setChildrenCollapsible(False)

        self.editor_tabs = EditorTabWidget()
        self.editor_tabs.setMinimumHeight(200)

        # Bottom: terminal tabs + flask runner
        self._bottom_widget = self._build_bottom_panel()
        self._bottom_widget.setMinimumHeight(100)

        self._center_splitter.addWidget(self.editor_tabs)
        self._center_splitter.addWidget(self._bottom_widget)
        self._center_splitter.setSizes([600, 250])

        self._outer_splitter.addWidget(self._sidebar_splitter)
        self._outer_splitter.addWidget(self._center_splitter)
        self._outer_splitter.setSizes([220, 1180])

        root_layout.addWidget(self._outer_splitter)

        # ── Status bar ─────────────────────────────────────────────────────
        self._status = QStatusBar()
        self._status.setFixedHeight(24)
        self.setStatusBar(self._status)
        self._status_label = QLabel("No project open")
        self._status.addWidget(self._status_label)

        # ── Wire signals ───────────────────────────────────────────────────
        self.file_tree.file_opened.connect(self.editor_tabs.open_file)
        self.editor_tabs.status_changed.connect(self._status_label.setText)
        self.git_panel.refresh_requested.connect(self._refresh_git)
        self.flask_runner.log_line.connect(self._terminal_tabs.append_output)

    def _build_bottom_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab bar for terminal instances + flask runner
        self._bottom_tabs = QTabWidget()
        self._bottom_tabs.setTabPosition(QTabWidget.TabPosition.South)
        self._bottom_tabs.setDocumentMode(True)

        # Terminal(s)
        self._terminal_tabs = TerminalWidget()
        self._bottom_tabs.addTab(self._terminal_tabs, "Terminal")

        # Flask runner
        self.flask_runner = FlaskRunner()
        self._bottom_tabs.addTab(self.flask_runner, "Flask")

        # "+ New Terminal" button in tab bar
        new_term_btn = QPushButton("+")
        new_term_btn.setFixedSize(24, 24)
        new_term_btn.setToolTip("New terminal")
        new_term_btn.clicked.connect(self._add_terminal_tab)
        self._bottom_tabs.setCornerWidget(new_term_btn, Qt.Corner.TopLeftCorner)

        layout.addWidget(self._bottom_tabs)
        return widget

    # ---------------------------------------------------------------- Menu --

    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        self._act(file_menu, "&Open Folder…", self.prompt_open_folder,
                  QKeySequence("Ctrl+K"))
        self._act(file_menu, "&New File", self.editor_tabs.new_file,
                  QKeySequence.StandardKey.New)
        self._act(file_menu, "&Save", self.editor_tabs.save_current,
                  QKeySequence.StandardKey.Save)
        self._act(file_menu, "Save &As…", self.editor_tabs.save_as,
                  QKeySequence.StandardKey.SaveAs)
        file_menu.addSeparator()
        self._act(file_menu, "&Quit", self.close, QKeySequence.StandardKey.Quit)

        # View
        view_menu = mb.addMenu("&View")
        self._act(view_menu, "Toggle &Sidebar", self._toggle_sidebar,
                  QKeySequence("Ctrl+B"))
        self._act(view_menu, "Toggle &Terminal", self._toggle_terminal,
                  QKeySequence("Ctrl+`"))
        self._act(view_menu, "Toggle &Git Panel", self._toggle_git,
                  QKeySequence("Ctrl+Shift+G"))

        # Git
        git_menu = mb.addMenu("&Git")
        self._act(git_menu, "&Refresh Status", self._refresh_git,
                  QKeySequence("Ctrl+Shift+R"))
        self._act(git_menu, "&Stage All", self.git_panel.stage_all)
        self._act(git_menu, "&Commit…", self.git_panel.commit)
        self._act(git_menu, "&Pull", self.git_panel.pull)
        self._act(git_menu, "P&ush", self.git_panel.push)

        # Run
        run_menu = mb.addMenu("&Run")
        self._act(run_menu, "&Run Current File", self._run_current,
                  QKeySequence("F5"))
        self._act(run_menu, "Run &Flask App", self.flask_runner.start_or_stop,
                  QKeySequence("F6"))

    def _act(self, menu: QMenu, label: str, slot, shortcut=None) -> QAction:
        a = QAction(label, self)
        if shortcut:
            a.setShortcut(shortcut)
        a.triggered.connect(slot)
        menu.addAction(a)
        return a

    # -------------------------------------------------------------- Toolbar --

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(tb)

        open_act = QAction("📂 Open", self)
        open_act.triggered.connect(self.prompt_open_folder)
        tb.addAction(open_act)

        save_act = QAction("💾 Save", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self.editor_tabs.save_current)
        tb.addAction(save_act)

        tb.addSeparator()

        run_act = QAction("▶ Run", self)
        run_act.setShortcut(QKeySequence("F5"))
        run_act.triggered.connect(self._run_current)
        tb.addAction(run_act)

        flask_act = QAction("🌶 Flask", self)
        flask_act.setShortcut(QKeySequence("F6"))
        flask_act.triggered.connect(self.flask_runner.start_or_stop)
        tb.addAction(flask_act)

        tb.addSeparator()

        git_act = QAction("⎇ Git", self)
        git_act.triggered.connect(self._refresh_git)
        tb.addAction(git_act)

    # ------------------------------------------------------------- Actions --

    def prompt_open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Open Project Folder",
                                                str(Path.home()))
        if path:
            self.open_folder(path)

    def open_folder(self, path: str):
        self._current_project = path
        self.setWindowTitle(f"PyIDE — {Path(path).name}")
        self.file_tree.set_root(path)
        self.git_panel.set_repo(path)
        self.flask_runner.set_cwd(path)
        self._terminal_tabs.set_cwd(path)
        self._settings.setValue("last_project", path)
        self._status_label.setText(f"Project: {path}")

    def _run_current(self):
        filepath = self.editor_tabs.current_filepath()
        if not filepath:
            self._status_label.setText("No file selected")
            return
        self.editor_tabs.save_current()
        cwd = self._current_project or str(Path(filepath).parent)
        self._terminal_tabs.run_command(f"python \"{filepath}\"", cwd=cwd)
        self._bottom_tabs.setCurrentIndex(0)

    def _refresh_git(self):
        if self._current_project:
            self.git_panel.set_repo(self._current_project)

    def _toggle_sidebar(self):
        w = self._sidebar_splitter
        w.setVisible(not w.isVisible())

    def _toggle_terminal(self):
        w = self._bottom_widget
        w.setVisible(not w.isVisible())

    def _toggle_git(self):
        self.git_panel.setVisible(not self.git_panel.isVisible())

    def _add_terminal_tab(self):
        t = TerminalWidget()
        if self._current_project:
            t.set_cwd(self._current_project)
        idx = self._bottom_tabs.insertTab(
            self._bottom_tabs.count() - 1, t,
            f"Terminal {self._bottom_tabs.count()}"
        )
        self._bottom_tabs.setCurrentIndex(idx)

    # -------------------------------------------------------- State restore --

    def _restore_state(self):
        geo = self._settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)
        outer = self._settings.value("outerSplitter")
        if outer:
            self._outer_splitter.restoreState(outer)
        center = self._settings.value("centerSplitter")
        if center:
            self._center_splitter.restoreState(center)
        sidebar = self._settings.value("sidebarSplitter")
        if sidebar:
            self._sidebar_splitter.restoreState(sidebar)

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        self._settings.setValue("outerSplitter", self._outer_splitter.saveState())
        self._settings.setValue("centerSplitter", self._center_splitter.saveState())
        self._settings.setValue("sidebarSplitter", self._sidebar_splitter.saveState())
        # Check unsaved files
        if not self.editor_tabs.close_all():
            event.ignore()
            return
        self.flask_runner.stop()
        event.accept()