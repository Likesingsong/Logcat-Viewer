"""日志表格数据模型 — QAbstractTableModel 实现."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QBrush, QColor

from logcat_viewer.parser import (
    COLUMNS,
    COL_LEVEL,
    COL_INDEX,
    COL_TIMESTAMP,
    COL_APPLICATION,
    COL_TAG,
    COL_MESSAGE,
    level_color,
)

logger = logging.getLogger(__name__)


class LogcatTableModel(QAbstractTableModel):
    """logcat 日志条目的表格数据模型。

    提供 DisplayRole 文本、BackgroundRole 着色、对齐等。
    配合 QTableView 实现虚拟滚动，支持百万级条目。
    """

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._entries: list[dict[str, Any]] = []
        self._metadata: dict[str, Any] = {}
        self._level_counts: dict[str, int] = {}

    @property
    def entries(self) -> list[dict[str, Any]]:
        return self._entries

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def level_counts(self) -> dict[str, int]:
        return self._level_counts

    def get_entry(self, row: int) -> dict[str, Any] | None:
        """返回指定行的条目，越界返回 None。"""
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def load_data(self, metadata: dict[str, Any], entries: list[dict[str, Any]]) -> None:
        """加载新数据，替换现有数据并通知视图刷新。"""
        self.beginResetModel()
        self._metadata = metadata
        self._entries = entries
        self._level_counts = self._compute_level_counts(entries)
        self.endResetModel()

    def clear(self) -> None:
        """清空所有数据。"""
        self.beginResetModel()
        self._metadata = {}
        self._entries = []
        self._level_counts = {}
        self.endResetModel()

    @staticmethod
    def _compute_level_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
        """预先计算各级别日志数量。"""
        counts: dict[str, int] = {}
        for entry in entries:
            lv = str(entry.get("level", "")).upper().strip()
            if lv:
                counts[lv] = counts.get(lv, 0) + 1
        return counts

    # ── QAbstractTableModel 接口 ─────────────────────────────────────────
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row < 0 or row >= len(self._entries):
            return None
        entry = self._entries[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(entry, col)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._background_brush(entry, col)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == COL_INDEX:
                return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._tooltip_value(entry, col)

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(COLUMNS):
            return COLUMNS[section]
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    # ── 内部辅助 ──────────────────────────────────────────────────────────
    @staticmethod
    def _display_value(entry: dict[str, Any], col: int) -> str:
        """根据列索引返回显示文本。"""
        keys = [
            "index", "timestamp", "level", "pid", "tid",
            "application", "process", "tag", "message",
        ]
        if 0 <= col < len(keys):
            return str(entry.get(keys[col], ""))
        return ""

    @staticmethod
    def _background_brush(entry: dict[str, Any], col: int) -> QBrush | None:
        """返回列专用或级别专用的背景色刷。"""
        if col == COL_LEVEL:
            lc = level_color(str(entry.get("level", "")))
            if lc:
                return QBrush(QColor(lc))

        col_colors: dict[int, str] = {
            COL_TIMESTAMP:   "#DAEEF3",
            COL_APPLICATION: "#E2EFDA",
            COL_TAG:         "#E4DFEC",
            COL_MESSAGE:     "#FFF2CC",
        }
        color = col_colors.get(col)
        if color:
            return QBrush(QColor(color))
        return None

    @staticmethod
    def _tooltip_value(entry: dict[str, Any], col: int) -> str:
        """返回 ToolTip 文本，Message 列显示完整内容。"""
        if col == COL_MESSAGE:
            msg = str(entry.get("message", ""))
            if len(msg) > 200:
                return msg[:500] + "\n…(截断，详情请选中查看)"
            return msg
        return ""
