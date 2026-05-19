"""
EditorTabWidget — verwaltet mehrere offene Dateien als Tabs.
Jeder Tab ist eine EditorPane (QWebEngineView + CodeMirror).
"""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QFileDialog, QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, Qt, QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot
import json


EDITOR_HTML = Path(__file__).parent.parent / "resources" / "editor.html"

BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".whl", ".exe", ".dll", ".so",
    ".db", ".sqlite",
}


class JSBridge(QObject):
    """Python-side object exposed to JavaScript via QWebChannel."""
    content_changed = pyqtSignal(str)
    editor_ready = pyqtSignal()

    @pyqtSlot(str)
    def postMessage(self, msg: str):
        try:
            data = json.loads(msg)
            if data.get("type") == "ready":
                self.editor_ready.emit()
            elif data.get("type") == "changed":
                self.content_changed.emit(data.get("content", ""))
        except Exception:
            pass


class EditorPane(QWidget):
    """Single editor tab: WebEngineView + CodeMirror + WebChannel."""

    dirty_changed = pyqtSignal(bool)

    def __init__(self, filepath: str | None = None):
        super().__init__()
        self._filepath: str | None = filepath
        self._dirty = False
        self._ready = False
        self._pending_content: str | None = None
        self._pending_lang: str | None = None
        self._current_content: str = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QWebEngineView()
        self._view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        layout.addWidget(self._view)

        self._bridge = JSBridge()
        self._bridge.editor_ready.connect(self._on_ready)
        self._bridge.content_changed.connect(self._on_content_changed)

        self._channel = QWebChannel()
        self._channel.registerObject("NepiIDEChannel", self._bridge)
        self._view.page().setWebChannel(self._channel)

        url = QUrl.fromLocalFile(str(EDITOR_HTML))
        self._view.load(url)

    # ---------------------------------------------------------------- API --

    @property
    def filepath(self) -> str | None:
        return self._filepath

    @property
    def dirty(self) -> bool:
        return self._dirty

    def load_file(self, path: str):
        self._filepath = path
        ext = Path(path).suffix.lower()
        if ext in BINARY_EXT:
            self._set_content(f"# Binary file: {path}", path)
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            self._set_content(text, path)
        except OSError as e:
            self._set_content(f"# Error reading file: {e}", path)

    def get_content(self) -> str:
        return self._current_content

    def save(self) -> bool:
        if not self._filepath:
            return self.save_as()
        self._view.page().runJavaScript(
            "window.NepiIDE ? window.NepiIDE.getContent() : ''",
            lambda result: self._do_write(self._filepath, result or "")
        )
        return True

    def save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Save As", self._filepath or "")
        if path:
            self._filepath = path
            self._view.page().runJavaScript(
                "window.NepiIDE ? window.NepiIDE.getContent() : ''",
                lambda result: self._do_write(path, result or "")
            )
            return True
        return False

    def _do_write(self, path: str, content: str):
        try:
            Path(path).write_text(content, encoding="utf-8")
            self._dirty = False
            self._current_content = content
            self.dirty_changed.emit(False)
        except OSError as e:
            QMessageBox.critical(self, "Save Error", str(e))

    # ---------------------------------------------------------------- internal --

    def _set_content(self, text: str, filepath: str | None = None):
        self._current_content = text
        self._pending_content = text
        self._pending_lang = filepath
        if self._ready:
            self._apply_pending()

    def _on_ready(self):
        self._ready = True
        self._apply_pending()

    def _apply_pending(self):
        if self._pending_content is not None:
            # Escape backticks and backslashes for JS template literal
            escaped = (
                self._pending_content
                .replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("${", "\\${")
            )
            self._view.page().runJavaScript(
                f"window.NepiIDE && window.NepiIDE.setContent(`{escaped}`)"
            )
            self._dirty = False
            self.dirty_changed.emit(False)
            self._pending_content = None

        if self._pending_lang is not None:
            lang_escaped = self._pending_lang.replace("\\", "\\\\").replace("'", "\\'")
            self._view.page().runJavaScript(
                f"window.NepiIDE && window.NepiIDE.setLanguage('{lang_escaped}')"
            )
            self._pending_lang = None

    def _on_content_changed(self, content: str):
        self._current_content = content
        if not self._dirty:
            self._dirty = True
            self.dirty_changed.emit(True)

    def focus_editor(self):
        self._view.setFocus()
        self._view.page().runJavaScript("window.NepiIDE && window.NepiIDE.focus()")

    def goto_line(self, line: int):
        self._view.page().runJavaScript(
            f"window.NepiIDE && window.NepiIDE.gotoLine({line})"
        )


class EditorTabWidget(QTabWidget):
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self._close_tab)
        self.currentChanged.connect(self._on_tab_changed)
        self._filepath_to_idx: dict[str, int] = {}

    # ---------------------------------------------------------------- API --

    def open_file(self, filepath: str):
        if filepath in self._filepath_to_idx:
            self.setCurrentIndex(self._filepath_to_idx[filepath])
            return

        pane = EditorPane(filepath)
        pane.load_file(filepath)
        pane.dirty_changed.connect(
            lambda dirty, fp=filepath: self._update_tab_title(fp, dirty)
        )

        name = Path(filepath).name
        idx = self.addTab(pane, name)
        self._filepath_to_idx[filepath] = idx
        self.setCurrentIndex(idx)
        self.status_changed.emit(filepath)

    def new_file(self):
        pane = EditorPane()
        idx = self.addTab(pane, "untitled")
        self.setCurrentIndex(idx)

    def save_current(self):
        pane = self._current_pane()
        if pane:
            pane.save()

    def save_as(self):
        pane = self._current_pane()
        if pane:
            pane.save_as()

    def current_filepath(self) -> str | None:
        pane = self._current_pane()
        return pane.filepath if pane else None

    def close_all(self) -> bool:
        for i in range(self.count()):
            pane = self.widget(i)
            if isinstance(pane, EditorPane) and pane.dirty:
                self.setCurrentIndex(i)
                name = Path(pane.filepath).name if pane.filepath else "untitled"
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    f"Save changes to '{name}'?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return False
                if reply == QMessageBox.StandardButton.Save:
                    pane.save()
        return True

    # ---------------------------------------------------------------- slots --

    def _close_tab(self, idx: int):
        pane = self.widget(idx)
        if isinstance(pane, EditorPane) and pane.dirty:
            name = Path(pane.filepath).name if pane.filepath else "untitled"
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                f"Save changes to '{name}'?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                pane.save()

        if isinstance(pane, EditorPane) and pane.filepath:
            self._filepath_to_idx.pop(pane.filepath, None)

        self.removeTab(idx)
        self._rebuild_index()

    def _rebuild_index(self):
        self._filepath_to_idx.clear()
        for i in range(self.count()):
            pane = self.widget(i)
            if isinstance(pane, EditorPane) and pane.filepath:
                self._filepath_to_idx[pane.filepath] = i

    def _on_tab_changed(self, idx: int):
        pane = self.widget(idx)
        if isinstance(pane, EditorPane):
            fp = pane.filepath or "untitled"
            self.status_changed.emit(fp)
            QTimer.singleShot(100, pane.focus_editor)

    def _update_tab_title(self, filepath: str, dirty: bool):
        idx = self._filepath_to_idx.get(filepath)
        if idx is None:
            return
        name = Path(filepath).name
        self.setTabText(idx, ("● " if dirty else "") + name)

    def _current_pane(self) -> EditorPane | None:
        w = self.currentWidget()
        return w if isinstance(w, EditorPane) else None