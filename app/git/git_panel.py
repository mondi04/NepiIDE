"""
GitPanel — kompaktes Git-Panel.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QColor


def _git(args: list[str], cwd: str) -> tuple[str, str, int]:
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.stdout, r.stderr, r.returncode
    except FileNotFoundError:
        return "", "git not found", 1


class GitWorker(QObject):
    done = pyqtSignal(str, str)

    def __init__(self, args: list[str], cwd: str):
        super().__init__()
        self._args = args
        self._cwd = cwd

    def run(self):
        out, err, _ = _git(self._args, self._cwd)
        self.done.emit(out, err)


class GitPanel(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._repo: str | None = None
        self._thread: QThread | None = None
        self._worker: GitWorker | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("Git")
        title.setStyleSheet("font-weight: bold; color: #cba6f7;")
        self._branch_label = QLabel("")
        self._branch_label.setStyleSheet("color: #a6e3a1; font-size: 11px;")
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(lambda: self.set_repo(self._repo) if self._repo else None)
        header.addWidget(title)
        header.addWidget(self._branch_label)
        header.addStretch()
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Vertical)

        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(2)

        self._file_list = QListWidget()
        self._file_list.setFont(QFont("JetBrains Mono", 10))
        self._file_list.setStyleSheet("""
            QListWidget { background: #181825; border: none; color: #cdd6f4; }
            QListWidget::item:selected { background: #313244; }
            QListWidget::item:hover { background: #262637; }
        """)
        self._file_list.currentItemChanged.connect(self._on_file_selected)
        list_layout.addWidget(self._file_list)

        btn_row = QHBoxLayout()
        for label, slot in [
            ("Stage All", self.stage_all),
            ("Stage", self._stage_selected),
            ("Unstage", self._unstage_selected),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        list_layout.addLayout(btn_row)

        commit_row = QHBoxLayout()
        self._commit_msg = QLineEdit()
        self._commit_msg.setPlaceholderText("Commit message…")
        self._commit_msg.setStyleSheet(
            "background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; padding: 2px 4px;"
        )
        self._commit_msg.returnPressed.connect(self.commit)
        commit_row.addWidget(self._commit_msg)

        commit_btn = QPushButton("Commit")
        commit_btn.setFixedWidth(60)
        commit_btn.clicked.connect(self.commit)
        commit_row.addWidget(commit_btn)
        list_layout.addLayout(commit_row)

        push_row = QHBoxLayout()
        for label, slot in [("Pull", self.pull), ("Push", self.push)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            push_row.addWidget(btn)
        list_layout.addLayout(push_row)

        splitter.addWidget(list_widget)

        self._diff_view = QTextEdit()
        self._diff_view.setReadOnly(True)
        self._diff_view.setFont(QFont("JetBrains Mono", 10))
        self._diff_view.setStyleSheet(
            "QTextEdit { background: #11111b; color: #cdd6f4; border: none; }"
        )
        splitter.addWidget(self._diff_view)
        splitter.setSizes([300, 200])

        layout.addWidget(splitter)

    # ---------------------------------------------------------------- API --

    def set_repo(self, path: str | None):
        self._repo = path
        self._file_list.clear()
        self._diff_view.clear()
        self._branch_label.setText("")
        if not path:
            return

        out, _, _ = _git(["branch", "--show-current"], path)
        self._branch_label.setText(out.strip())

        out, err, code = _git(["status", "--porcelain"], path)
        if code != 0:
            self._file_list.addItem(f"Not a git repo: {err.strip()}")
            return

        for line in out.splitlines():
            if not line.strip():
                continue
            xy = line[:2]
            fname = line[3:]
            item = QListWidgetItem(f"{xy} {fname}")
            if "?" in xy:
                item.setForeground(QColor("#a6e3a1"))
            elif "M" in xy or "A" in xy:
                item.setForeground(QColor("#89b4fa"))
            elif "D" in xy:
                item.setForeground(QColor("#f38ba8"))
            else:
                item.setForeground(QColor("#f9e2af"))
            item.setData(Qt.ItemDataRole.UserRole, fname.strip())
            self._file_list.addItem(item)

    def stage_all(self):
        if not self._repo:
            return
        _git(["add", "-A"], self._repo)
        self.set_repo(self._repo)

    def commit(self):
        if not self._repo:
            return
        msg = self._commit_msg.text().strip()
        if not msg:
            QMessageBox.warning(self, "Commit", "Please enter a commit message.")
            return
        out, err, code = _git(["commit", "-m", msg], self._repo)
        if code == 0:
            self._commit_msg.clear()
            self.set_repo(self._repo)
        else:
            QMessageBox.warning(self, "Commit failed", err or out)

    def pull(self):
        self._run_background(["pull"])

    def push(self):
        self._run_background(["push"])

    # ---------------------------------------------------------------- internal --

    def _stage_selected(self):
        item = self._file_list.currentItem()
        if item and self._repo:
            fname = item.data(Qt.ItemDataRole.UserRole)
            _git(["add", fname], self._repo)
            self.set_repo(self._repo)

    def _unstage_selected(self):
        item = self._file_list.currentItem()
        if item and self._repo:
            fname = item.data(Qt.ItemDataRole.UserRole)
            _git(["restore", "--staged", fname], self._repo)
            self.set_repo(self._repo)

    def _on_file_selected(self, current: QListWidgetItem | None, _prev):
        if not current or not self._repo:
            return
        fname = current.data(Qt.ItemDataRole.UserRole)
        if not fname:
            return
        out, _, code = _git(["diff", "HEAD", "--", fname], self._repo)
        if not out:
            out, _, _ = _git(["diff", "--cached", "--", fname], self._repo)
        self._show_diff(out or f"# No diff available for {fname}")

    def _show_diff(self, diff: str):
        self._diff_view.clear()
        cursor = self._diff_view.textCursor()
        for line in diff.splitlines(keepends=True):
            fmt = cursor.charFormat()
            if line.startswith("+") and not line.startswith("+++"):
                fmt.setForeground(QColor("#a6e3a1"))
            elif line.startswith("-") and not line.startswith("---"):
                fmt.setForeground(QColor("#f38ba8"))
            elif line.startswith("@@"):
                fmt.setForeground(QColor("#89dceb"))
            else:
                fmt.setForeground(QColor("#585b70"))
            cursor.setCharFormat(fmt)
            cursor.insertText(line)
        self._diff_view.setTextCursor(cursor)

    def _run_background(self, args: list[str]):
        if not self._repo:
            return
        self._thread = QThread()
        self._worker = GitWorker(args, self._repo)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_bg_done)
        self._worker.done.connect(self._thread.quit)
        self._thread.start()

    def _on_bg_done(self, out: str, err: str):
        msg = (out + err).strip()
        QMessageBox.information(self, "Git", msg or "Done")
        self.set_repo(self._repo)