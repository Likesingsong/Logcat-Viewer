"""统计栏组件 — 显示日志条目总数及各级别分布."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from logcat_viewer.parser import LEVEL_COLORS
from logcat_viewer.utils import format_count

logger = logging.getLogger(__name__)


class StatsBar(QWidget):
    """日志统计状态栏。

    显示当前可视条目数、总条目数，以及各级别计数。
    """

    _LEVEL_ORDER = ["V", "D", "I", "W", "E", "F", "S"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total_label: QLabel | None = None
        self._visible_label: QLabel | None = None
        self._level_labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(12)

        # 总数
        self._total_label = QLabel("共 0 条")
        self._total_label.setObjectName("statsLabel")
        layout.addWidget(self._total_label)

        # 可见数
        self._visible_label = QLabel("显示 0 条")
        self._visible_label.setObjectName("statsLabel")
        layout.addWidget(self._visible_label)

        layout.addStretch()

        # 各级别计数（带颜色标识）
        for lv in self._LEVEL_ORDER:
            label = QLabel(f"{lv}:0")
            label.setObjectName("statsLabel")
            lc = LEVEL_COLORS.get(lv, "")
            if lc:
                label.setStyleSheet(
                    f"QLabel {{ color: #333; padding: 1px 4px; "
                    f"background-color: {lc}; border-radius: 2px; font-size: 11px; }}"
                )
            self._level_labels[lv] = label
            layout.addWidget(label)

    def update_stats(
        self,
        total: int,
        visible: int = 0,
        level_counts: dict[str, int] | None = None,
    ) -> None:
        """更新统计显示。

        Args:
            total: 日志总条目数。
            visible: 当前过滤后可见条目数（默认同 total）。
            level_counts: 各级别计数字典，如 {"I": 123, "E": 5}。
        """
        self._total_label.setText(f"共 {format_count(total)} 条")
        if visible != total:
            self._visible_label.setText(f"显示 {format_count(visible)} 条")
            self._visible_label.setVisible(True)
        else:
            self._visible_label.setVisible(False)

        counts = level_counts or {}
        for lv in self._LEVEL_ORDER:
            cnt = counts.get(lv, 0)
            self._level_labels[lv].setText(f"{lv}:{format_count(cnt)}")

    def reset(self) -> None:
        """重置统计为 0。"""
        self._total_label.setText("共 0 条")
        self._visible_label.setVisible(False)
        for lv in self._LEVEL_ORDER:
            self._level_labels[lv].setText(f"{lv}:0")
