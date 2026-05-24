"""详情面板 — 显示选中日志条目的完整 Message."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logcat_viewer.parser import level_color


class DetailPanel(QWidget):
    """日志详情面板。

    展示选中行的完整信息：
    - 消息全文（等宽字体，可选择/复制）
    - 级别、Tag、PID/TID 等摘要信息
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 头部摘要
        self._header = QLabel("选中一条日志查看详情")
        self._header.setStyleSheet("padding: 4px 8px; font-weight: bold; font-size: 11px;")
        self._header.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # 消息正文
        self._message_edit = QTextEdit()
        self._message_edit.setReadOnly(True)
        self._message_edit.setFrameShape(QFrame.Shape.NoFrame)
        self._message_edit.setPlaceholderText("未选中日志条目")
        # 等宽字体
        self._message_edit.setStyleSheet(
            'font-family: "Consolas", "Monaco", "Menlo", monospace; font-size: 12px;'
        )

        layout.addWidget(self._header)
        layout.addWidget(self._message_edit, stretch=1)

    def show_entry(self, entry: dict | None) -> None:
        """显示指定条目的详情。

        Args:
            entry: 日志条目字典，或 None 表示清空。
        """
        if entry is None:
            self._header.setText("选中一条日志查看详情")
            self._header.setStyleSheet(
                "padding: 4px 8px; font-weight: bold; font-size: 11px;"
            )
            self._message_edit.clear()
            self._message_edit.setPlaceholderText("未选中日志条目")
            return

        level = str(entry.get("level", ""))
        tag = str(entry.get("tag", ""))
        pid = str(entry.get("pid", ""))
        tid = str(entry.get("tid", ""))
        ts = str(entry.get("timestamp", ""))
        app = str(entry.get("application", ""))
        process = str(entry.get("process", ""))
        message = str(entry.get("message", ""))

        # 头部着色
        lc = level_color(level)
        header_text = f"{ts}  [{level}]  {tag}  (PID:{pid} TID:{tid})  {app}"
        if lc:
            self._header.setStyleSheet(
                f"padding: 4px 8px; font-weight: bold; font-size: 11px; "
                f"background-color: {lc}; border-radius: 2px;"
            )
        else:
            self._header.setStyleSheet(
                "padding: 4px 8px; font-weight: bold; font-size: 11px;"
            )
        self._header.setText(header_text)

        # 消息正文
        if message:
            self._message_edit.setPlainText(message)
        else:
            self._message_edit.setPlainText("（空消息）")

    def clear(self) -> None:
        """清空详情面板。"""
        self.show_entry(None)
