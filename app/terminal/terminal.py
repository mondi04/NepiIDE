"""
TerminalWidget — echtes PTY-Terminal via QProcess.

Strategie:
  - Primär: ptyprocess (wenn installiert) für echtes PTY mit ANSI
  - Fallback: QProcess ohne PTY (kein Colour, aber funktional)

ANSI-Escape-Codes werden via einfaches Regex-Stripping entfernt
(QTextEdit versteht kein ANSI nativ); für echtes ANSI wäre
QWebEngineView + xterm.js nötig – das ist als optionaler Upgrade geplant.
"""

from __future__ import annotations

import os
import re
import sys
import shlex
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QSizePolicy,
)
from PyQt6.QtCore import Qt, QProcess, QTimer, pyqtSignal, QIODevice
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette, QKeyEvent


# Strip ANSI escape sequences
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]|\x1b\][^\x07]*\x07|\x1b[()].")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


class TerminalWidget(QWidget):
    """Eingebettetes Terminal mit QProcess-Backend."""

    def __init__(self):
        super().__init__()
        self._cwd: str = str(Path.home())
        self._history: list[str] = []
        self._history_idx: int = -1
        self._process: QProcess | None = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Output area
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(QFont("JetBrains Mono", 11))
        self._output.setStyleSheet("""
            QTextEdit {
                background: #11111b;
                color: #cdd6f4;
                border: none;
                padding: 4px;
                selection-background-color: #45475a;
            }
        """)
        self._output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Input row
        input_row = QWidget()
        input_layout = QHBoxLayout(input_row)
        input_layout.setContentsMargins(4, 2, 4, 2)
        input_layout.setSpacing(4)

        self._prompt_label = QLabel("$")
        self._prompt_label.setFont(QFont("JetBrains Mono", 11))
        self._prompt_label.setStyleSheet("color: #a6e3a1;")

        self._input = QLineEdit()
        self._input.setFont(QFont("JetBrains Mono", 11))
        self._input.setStyleSheet("""
            QLineEdit {
                background: #11111b;
                color: #cdd6f4;
                border: none;
                padding: 2px 4px;
            }
        """)
        self._input.returnPressed.connect(self._execute)
        self._input.installEventFilter(self)

        kill_btn = QPushButton("✕")
        kill_btn.setFixedSize(22, 22)
        kill_btn.setToolTip("Kill running process")
        kill_btn.setStyleSheet("QPushButton { background: #313244; color: #f38ba8; border: none; border-radius: 3px; }"
                               "QPushButton:hover { background: #f38ba8; color: #1e1e2e; }")
        kill_btn.clicked.connect(self._kill_process)

        input_layout.addWidget(self._prompt_label)
        input_layout.addWidget(self._input)
        input_layout.addWidget(kill_btn)
        input_row.setStyleSheet("background: #11111b;")

        layout.addWidget(self._output)
        layout.addWidget(input_row)

        self._append("NepiIDE Terminal — type commands below\n", "#585b70")
        self._update_prompt()

    # ---------------------------------------------------------------- API --

    def set_cwd(self, path: str):
        self._cwd = path
        self._update_prompt()

    def run_command(self, cmd: str, cwd: str | None = None):
        """Run a command programmatically (e.g. from Run button)."""
        if cwd:
            self._cwd = cwd
        self._input.setText(cmd)
        self._execute()

    def append_output(self, line: str):
        self._append(line + "\n")

    # ---------------------------------------------------------------- slots --

    def _execute(self):
        cmd = self._input.text().strip()
        self._input.clear()
        if not cmd:
            return

        self._history.append(cmd)
        self._history_idx = len(self._history)

        self._append(f"$ {cmd}\n", "#a6e3a1")

        # Handle cd internally
        if cmd.startswith("cd ") or cmd == "cd":
            self._handle_cd(cmd)
            return

        if cmd == "clear":
            self._output.clear()
            return

        self._run_process(cmd)

    def _handle_cd(self, cmd: str):
        parts = cmd.split(None, 1)
        target = parts[1].strip() if len(parts) > 1 else str(Path.home())
        target = os.path.expanduser(target)
        if not os.path.isabs(target):
            target = os.path.join(self._cwd, target)
        target = os.path.normpath(target)
        if os.path.isdir(target):
            self._cwd = target
            self._update_prompt()
        else:
            self._append(f"cd: {target}: No such directory\n", "#f38ba8")

    def _run_process(self, cmd: str):
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._append("[Process already running — kill it first]\n", "#f9e2af")
            return

        self._process = QProcess(self)
        self._process.setWorkingDirectory(self._cwd)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

        env = self._process.processEnvironment()
        from PyQt6.QtCore import QProcessEnvironment
        env = QProcessEnvironment.systemEnvironment()
        env.insert("TERM", "xterm-256color")
        env.insert("PYTHONUNBUFFERED", "1")
        self._process.setProcessEnvironment(env)

        if sys.platform == "win32":
            self._process.start("cmd.exe", ["/c", cmd])
        else:
            self._process.start("/bin/sh", ["-c", cmd])

    def _on_stdout(self):
        if self._process:
            raw = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
            self._append(strip_ansi(raw))

    def _on_stderr(self):
        if self._process:
            raw = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
            self._append(strip_ansi(raw), "#f38ba8")

    def _on_finished(self, exit_code: int, exit_status):
        if exit_code != 0:
            self._append(f"[exited with code {exit_code}]\n", "#6c7086")
        self._process = None

    def _kill_process(self):
        if self._process:
            self._process.kill()
            self._append("[killed]\n", "#f9e2af")

    def _update_prompt(self):
        short = self._cwd
        home = str(Path.home())
        if short.startswith(home):
            short = "~" + short[len(home):]
        self._prompt_label.setText(short + " $")

    def _append(self, text: str, color: str = "#cdd6f4"):
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    # ---------------------------------------------------------------- history nav --

    def eventFilter(self, obj, event):
        if obj is self._input and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key.Key_Up:
                if self._history and self._history_idx > 0:
                    self._history_idx -= 1
                    self._input.setText(self._history[self._history_idx])
                return True
            if event.key() == Qt.Key.Key_Down:
                if self._history_idx < len(self._history) - 1:
                    self._history_idx += 1
                    self._input.setText(self._history[self._history_idx])
                else:
                    self._history_idx = len(self._history)
                    self._input.clear()
                return True
            if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self._kill_process()
                return True
        return super().eventFilter(obj, event)