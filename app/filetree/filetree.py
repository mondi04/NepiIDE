"""
FileTree — QTreeView über QFileSystemModel.
Kontextmenü: Neue Datei, Neuer Ordner, Umbenennen, Löschen.
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QTreeView, QMenu, QInputDialog,
    QMessageBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QAction, QFileSystemModel


class HideFilter(QSortFilterProxyModel):
    """Blendet typische Python-Projekt-Junk-Ordner aus."""
    HIDDEN = {".git", "__pycache__", ".venv", "venv", "env",
              ".mypy_cache", ".ruff_cache", ".pytest_cache",
              "node_modules", ".DS_Store", "dist", "build"}

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        idx = model.index(source_row, 0, source_parent)
        name = model.fileName(idx)
        if name in self.HIDDEN:
            return False
        if name.endswith((".pyc", ".pyo", ".egg-info")):
            return False
        return True


class FileTree(QTreeView):
    file_opened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._root: str | None = None

        self._fs_model = QFileSystemModel()
        self._fs_model.setNameFilterDisables(False)

        self._proxy = HideFilter()
        self._proxy.setSourceModel(self._fs_model)
        self.setModel(self._proxy)

        for col in (1, 2, 3):
            self.hideColumn(col)

        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.doubleClicked.connect(self._on_double_click)

    def set_root(self, path: str):
        self._root = path
        fs_root = self._fs_model.setRootPath(path)
        proxy_root = self._proxy.mapFromSource(fs_root)
        self.setRootIndex(proxy_root)

    # ---------------------------------------------------------------- slots -

    def _on_double_click(self, proxy_idx: QModelIndex):
        src_idx = self._proxy.mapToSource(proxy_idx)
        if not self._fs_model.isDir(src_idx):
            path = self._fs_model.filePath(src_idx)
            self.file_opened.emit(path)

    def _context_menu(self, pos):
        proxy_idx = self.indexAt(pos)
        src_idx = self._proxy.mapToSource(proxy_idx) if proxy_idx.isValid() else QModelIndex()

        if src_idx.isValid():
            clicked_path = Path(self._fs_model.filePath(src_idx))
            context_dir = clicked_path if clicked_path.is_dir() else clicked_path.parent
        else:
            context_dir = Path(self._root) if self._root else Path.cwd()

        menu = QMenu(self)

        new_file = QAction("New File", self)
        new_file.triggered.connect(lambda: self._new_file(context_dir))
        menu.addAction(new_file)

        new_dir = QAction("New Folder", self)
        new_dir.triggered.connect(lambda: self._new_dir(context_dir))
        menu.addAction(new_dir)

        if src_idx.isValid():
            menu.addSeparator()
            rename = QAction("Rename", self)
            rename.triggered.connect(lambda: self._rename(src_idx, clicked_path))
            menu.addAction(rename)

            delete = QAction("Delete", self)
            delete.triggered.connect(lambda: self._delete(src_idx, clicked_path))
            menu.addAction(delete)

            if not self._fs_model.isDir(src_idx):
                menu.addSeparator()
                open_act = QAction("Open in Editor", self)
                open_act.triggered.connect(lambda: self.file_opened.emit(str(clicked_path)))
                menu.addAction(open_act)

        menu.exec(self.viewport().mapToGlobal(pos))

    def _new_file(self, directory: Path):
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name.strip():
            fp = directory / name.strip()
            try:
                fp.touch()
                self.file_opened.emit(str(fp))
            except OSError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _new_dir(self, directory: Path):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name.strip():
            fp = directory / name.strip()
            try:
                fp.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _rename(self, src_idx: QModelIndex, path: Path):
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=path.name)
        if ok and name.strip():
            new_path = path.parent / name.strip()
            try:
                path.rename(new_path)
            except OSError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _delete(self, src_idx: QModelIndex, path: Path):
        what = "folder" if path.is_dir() else "file"
        reply = QMessageBox.question(
            self, "Delete",
            f"Delete {what} '{path.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except OSError as e:
                QMessageBox.warning(self, "Error", str(e))