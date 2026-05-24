"""过滤栏组件 — 提供日志级别、Tag、Message、PID/TID 的过滤."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
    - 点击搜索按钮或按回车执行搜索

    Signals:
        filters_changed(dict): 点击搜索按钮时发射，携带所有过滤条件。
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
        self.blockSignals(True)
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
        self.blockSignals(False)
        self._do_emit_filters()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Level:"))
        for lv in self.LEVELS:
            cb = QCheckBox(lv)
            cb.setChecked(True)
            cb.setToolTip(self.LEVEL_LABELS.get(lv, lv))
            cb.toggled.connect(self._do_emit_filters)
            self._checkboxes[lv] = cb
            layout.addWidget(cb)

        layout.addSpacing(12)

        layout.addWidget(QLabel("Tag:"))
        self._tag_edit = QLineEdit()
        self._tag_edit.setPlaceholderText("搜索 Tag…")
        self._tag_edit.setMaximumWidth(140)
        self._tag_edit.returnPressed.connect(self._do_emit_filters)
        layout.addWidget(self._tag_edit)

        layout.addWidget(QLabel("Msg:"))
        self._msg_edit = QLineEdit()
        self._msg_edit.setPlaceholderText("搜索 Message…")
        self._msg_edit.setMaximumWidth(160)
        self._msg_edit.returnPressed.connect(self._do_emit_filters)
        layout.addWidget(self._msg_edit)

        layout.addWidget(QLabel("PID:"))
        self._pid_edit = QLineEdit()
        self._pid_edit.setPlaceholderText("PID")
        self._pid_edit.setMaximumWidth(80)
        self._pid_edit.returnPressed.connect(self._do_emit_filters)
        layout.addWidget(self._pid_edit)

        layout.addWidget(QLabel("TID:"))
        self._tid_edit = QLineEdit()
        self._tid_edit.setPlaceholderText("TID")
        self._tid_edit.setMaximumWidth(80)
        self._tid_edit.returnPressed.connect(self._do_emit_filters)
        layout.addWidget(self._tid_edit)

        layout.addSpacing(8)

        search_btn = QPushButton("搜索")
        search_btn.setFixedWidth(60)
        search_btn.clicked.connect(self._do_emit_filters)
        layout.addWidget(search_btn)

        reset_btn = QPushButton("重置")
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(self.reset)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _do_emit_filters(self) -> None:
        """发射 filters_changed 信号。"""
        filters = self.current_filters()
        if not filters["levels"]:
            filters["levels"] = set(self.LEVELS)
        logger.info(f"发射过滤条件: levels={filters['levels']}, tag='{filters['tag']}', "
                    f"msg='{filters['message']}', pid='{filters['pid']}', tid='{filters['tid']}'")
        self.filters_changed.emit(filters)
