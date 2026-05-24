"""过滤栏组件 — 提供日志级别、Tag、Message、PID/TID 的实时过滤."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

logger = logging.getLogger(__name__)


class FilterBar(QWidget):
    """日志条目过滤器工具栏。

    支持:
    - Level 多选过滤（V/D/I/W/E/F/S 复选框）
    - Tag 子串搜索
    - Message 关键词搜索
    - PID / TID 精确或子串匹配

    Signals:
        filters_changed(dict): 过滤器发生变化时发射，携带所有过滤条件。
    """

    filters_changed = Signal(dict)

    LEVELS = ["V", "D", "I", "W", "E", "F", "S"]
    LEVEL_LABELS = {
        "V": "Verbose", "D": "Debug", "I": "Info",
        "W": "Warn",   "E": "Error", "F": "Fatal",
        "S": "Silent/Assert",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._tag_edit: QLineEdit | None = None
        self._msg_edit: QLineEdit | None = None
        self._pid_edit: QLineEdit | None = None
        self._tid_edit: QLineEdit | None = None
        self._setup_ui()
        self._emit_filters()

    # ── 公共接口 ────────────────────────────────────────────────────────────
    def current_filters(self) -> dict:
        """返回当前所有过滤条件的字典。"""
        enabled = {lv for lv, cb in self._checkboxes.items() if cb.isChecked()}
        return {
            "levels":      enabled,
            "tag":         self._tag_edit.text() if self._tag_edit else "",
            "message":     self._msg_edit.text() if self._msg_edit else "",
            "pid":         self._pid_edit.text() if self._pid_edit else "",
            "tid":         self._tid_edit.text() if self._tid_edit else "",
            "application": "",
            "process":     "",
        }

    def reset(self) -> None:
        """重置所有过滤器到默认状态（全选，搜索框清空）。"""
        for cb in self._checkboxes.values():
            cb.setChecked(True)
        if self._tag_edit:
            self._tag_edit.clear()
        if self._msg_edit:
            self._msg_edit.clear()
        if self._pid_edit:
            self._pid_edit.clear()
        if self._tid_edit:
            self._tid_edit.clear()
        self._emit_filters()

    # ── UI 构建 ─────────────────────────────────────────────────────────────
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # --- Level 复选框 ---
        layout.addWidget(QLabel("Level:"))
        for lv in self.LEVELS:
            cb = QCheckBox(lv)
            cb.setChecked(True)
            cb.setToolTip(self.LEVEL_LABELS.get(lv, lv))
            cb.toggled.connect(self._emit_filters)
            self._checkboxes[lv] = cb
            layout.addWidget(cb)

        layout.addSpacing(12)

        # --- Tag 搜索 ---
        layout.addWidget(QLabel("Tag:"))
        self._tag_edit = QLineEdit()
        self._tag_edit.setPlaceholderText("搜索 Tag…")
        self._tag_edit.setMaximumWidth(140)
        self._tag_edit.textChanged.connect(self._emit_filters)
        layout.addWidget(self._tag_edit)

        # --- Message 搜索 ---
        layout.addWidget(QLabel("Msg:"))
        self._msg_edit = QLineEdit()
        self._msg_edit.setPlaceholderText("搜索 Message…")
        self._msg_edit.setMaximumWidth(160)
        self._msg_edit.textChanged.connect(self._emit_filters)
        layout.addWidget(self._msg_edit)

        # --- PID ---
        layout.addWidget(QLabel("PID:"))
        self._pid_edit = QLineEdit()
        self._pid_edit.setPlaceholderText("PID")
        self._pid_edit.setMaximumWidth(80)
        self._pid_edit.textChanged.connect(self._emit_filters)
        layout.addWidget(self._pid_edit)

        # --- TID ---
        layout.addWidget(QLabel("TID:"))
        self._tid_edit = QLineEdit()
        self._tid_edit.setPlaceholderText("TID")
        self._tid_edit.setMaximumWidth(80)
        self._tid_edit.textChanged.connect(self._emit_filters)
        layout.addWidget(self._tid_edit)

        layout.addStretch()

    def _emit_filters(self, _unused: object = None) -> None:
        """发射 filters_changed 信号。"""
        # 若所有级别都未选中，则等价于全选（不隐藏所有行）
        filters = self.current_filters()
        if not filters["levels"]:
            filters["levels"] = set(self.LEVELS)
        self.filters_changed.emit(filters)
