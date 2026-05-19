"""
FlaskRunner — Panel zum Starten/Stoppen von Flask-Apps.

Features:
  - App-Datei wählbar (app.py, main.py, etc.)
  - Port konfigurierbar
  - Debug-Mode Toggle
  - Live-Logs im eingebetteten Terminal-Output
  - Browser-Button öffnet localhost:PORT
  - Prozess-Status-Anzeige
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QCheckBox, QComboBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QProcess, pyqtSignal, QProcessEnvironment
from PyQt6.QtGui import QFont, QColor, QTextCursor


COMMON_APP_FILES = ["app.py", "main.py", "server.py", "wsgi.py", "run.py"]


class FlaskRunner(QWidget):
    log_line = pyqtSignal(str)   # for routing to terminal if desired

    def __init__(self):
        super().__init__()
        self._cwd: str = str(Path.home())
        self._process: QProcess | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── Config row ─────────────────────────────────────────────────────
        config_row = QHBoxLayout()

        # App file
        config_row.addWidget(QLabel("App:"))
        self._app_file = QComboBox()
        self._app_file.setEditable(True)
        self._app_file.setMinimumWidth(120)
        self._app_file.setStyleSheet("background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244;")
        config_row.addWidget(self._app_file)

        browse_btn = QPushButton("…")
        browse_btn.setFixedSize(24, 24)
        browse_btn.clicked.connect(self._browse_app)
        config_row.addWidget(browse_btn)

        config_row.addSpacing(8)

        # Port
        config_row.addWidget(QLabel("Port:"))
        self._port = QLineEdit("5000")
        self._port.setFixedWidth(60)
        self._port.setStyleSheet("background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; padding: 2px 4px;")
        config_row.addWidget(self._port)

        config_row.addSpacing(8)

        # Debug toggle
        self._debug = QCheckBox("Debug")
        self._debug.setChecked(True)
        self._debug.setStyleSheet("color: #cdd6f4;")
        config_row.addWidget(self._debug)

        config_row.addStretch()
        layout.addLayout(config_row)

        # ── Control row ────────────────────────────────────────────────────
        ctrl_row = QHBoxLayout()

        self._start_btn = QPushButton("▶  Start Flask")
        self._start_btn.setFixedHeight(28)
        self._start_btn.setStyleSheet("""
            QPushButton { background: #a6e3a1; color: #1e1e2e; border: none;
                          border-radius: 4px; font-weight: bold; padding: 0 12px; }
            QPushButton:hover { background: #94e2d5; }
        """)
        self._start_btn.clicked.connect(self.start_or_stop)
        ctrl_row.addWidget(self._start_btn)

        self._browser_btn = QPushButton("🌐 Open Browser")
        self._browser_btn.setEnabled(False)
        self._browser_btn.clicked.connect(self._open_browser)
        ctrl_row.addWidget(self._browser_btn)

        self._status_label = QLabel("●  Stopped")
        self._status_label.setStyleSheet("color: #6c7086;")
        ctrl_row.addWidget(self._status_label)

        ctrl_row.addStretch()
        layout.addLayout(ctrl_row)

        # ── Log output ─────────────────────────────────────────────────────
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("JetBrains Mono", 10))
        self._log.setStyleSheet("""
            QTextEdit {
                background: #11111b; color: #cdd6f4;
                border: none; padding: 4px;
            }
        """)
        layout.addWidget(self._log)

        # Shared button style for non-special buttons
        for btn in [browse_btn, self._browser_btn]:
            btn.setStyleSheet("""
                QPushButton { background: #313244; color: #cdd6f4;
                              border: none; border-radius: 3px; padding: 2px 8px; }
                QPushButton:hover { background: #45475a; }
                QPushButton:disabled { color: #45475a; }
            """)

    # ---------------------------------------------------------------- API --

    def set_cwd(self, path: str):
        self._cwd = path
        self._refresh_app_list()

    def start_or_stop(self):
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self.stop()
        else:
            self.start()

    def start(self):
        app_file = self._app_file.currentText().strip()
        if not app_file:
            self._append("No app file selected.\n", "#f38ba8")
            return

        port = self._port.text().strip() or "5000"
        debug = self._debug.isChecked()

        full_path = app_file if os.path.isabs(app_file) else os.path.join(self._cwd, app_file)
        if not os.path.exists(full_path):
            self._append(f"File not found: {full_path}\n", "#f38ba8")
            return

        self._log.clear()
        self._process = QProcess(self)
        self._process.setWorkingDirectory(self._cwd)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("FLASK_APP", full_path)
        env.insert("FLASK_ENV", "development" if debug else "production")
        env.insert("PYTHONUNBUFFERED", "1")
        if debug:
            env.insert("FLASK_DEBUG", "1")
        self._process.setProcessEnvironment(env)

        # Build command: python -m flask run --port PORT
        # Fallback: python full_path directly
        cmd_args = ["-m", "flask", "run", "--port", port]
        if debug:
            cmd_args.append("--debug")

        python_exe = sys.executable
        self._process.start(python_exe, cmd_args)

        self._append(f"Starting: {python_exe} {' '.join(cmd_args)}\n", "#585b70")
        self._append(f"CWD: {self._cwd}\n", "#585b70")
        self._append(f"FLASK_APP: {full_path}\n\n", "#585b70")
        self._set_running(True, port)

    def stop(self):
        if self._process:
            self._process.kill()
            self._process = None
        self._set_running(False)

    # ---------------------------------------------------------------- internal --

    def _refresh_app_list(self):
        self._app_file.clear()
        for name in COMMON_APP_FILES:
            full = Path(self._cwd) / name
            if full.exists():
                self._app_file.addItem(name)
        # Also allow any .py
        for p in Path(self._cwd).glob("*.py"):
            if p.name not in COMMON_APP_FILES:
                self._app_file.addItem(p.name)

    def _browse_app(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Flask app", self._cwd, "Python files (*.py)"
        )
        if path:
            rel = os.path.relpath(path, self._cwd)
            self._app_file.setCurrentText(rel)

    def _set_running(self, running: bool, port: str = "5000"):
        if running:
            self._start_btn.setText("■  Stop Flask")
            self._start_btn.setStyleSheet("""
                QPushButton { background: #f38ba8; color: #1e1e2e; border: none;
                              border-radius: 4px; font-weight: bold; padding: 0 12px; }
                QPushButton:hover { background: #eba0ac; }
            """)
            self._status_label.setText(f"●  Running on :{port}")
            self._status_label.setStyleSheet("color: #a6e3a1;")
            self._browser_btn.setEnabled(True)
            self._browser_btn.setProperty("_port", port)
        else:
            self._start_btn.setText("▶  Start Flask")
            self._start_btn.setStyleSheet("""
                QPushButton { background: #a6e3a1; color: #1e1e2e; border: none;
                              border-radius: 4px; font-weight: bold; padding: 0 12px; }
                QPushButton:hover { background: #94e2d5; }
            """)
            self._status_label.setText("●  Stopped")
            self._status_label.setStyleSheet("color: #6c7086;")
            self._browser_btn.setEnabled(False)

    def _open_browser(self):
        import webbrowser
        port = self._browser_btn.property("_port") or "5000"
        webbrowser.open(f"http://127.0.0.1:{port}")

    def _on_stdout(self):
        if self._process:
            raw = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
            self._append(raw)
            self.log_line.emit(raw.strip())

    def _on_stderr(self):
        if self._process:
            raw = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
            # Flask logs to stderr — colour it subtly
            self._append(raw, "#f9e2af")
            self.log_line.emit(raw.strip())

    def _on_finished(self, code: int, _status):
        self._append(f"\n[Flask exited with code {code}]\n", "#6c7086")
        self._set_running(False)
        self._process = None

    def _append(self, text: str, color: str = "#cdd6f4"):
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()