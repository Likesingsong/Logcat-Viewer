"""设备信息面板 — 展示 logcat 文件的设备元数据."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class DevicePanel(QWidget):
    """设备信息展示面板。

    以表单形式展示设备名称、型号、序列号、Android 版本、SDK 等元数据。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QFormLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # 标题
        title = QLabel("Device Information")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4472C4; padding-bottom: 8px;")
        layout.addRow(title)

        fields = [
            "Device Name", "Model", "Serial", "Android Release",
            "SDK", "Feature Level", "Type", "Emulator", "Online",
            "Device ID", "Log Filter",
        ]

        for name in fields:
            label = QLabel("—")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
            layout.addRow(f"{name}:", label)
            self._labels[name] = label

        # Project Apps 区域
        self._apps_label = QLabel("")
        self._apps_label.setWordWrap(True)
        self._apps_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addRow("Project Apps:", self._apps_label)

        scroll.setWidget(container)
        root.addWidget(scroll)

    def load_metadata(self, metadata: dict[str, Any]) -> None:
        """加载设备元数据并更新显示。

        Args:
            metadata: parser.read_logcat_json 返回的 metadata 字典。
        """
        device = metadata.get("device", {}) or {}
        filter_str = metadata.get("filter", "")
        project_ids = metadata.get("projectApplicationIds", [])

        values: dict[str, str] = {
            "Device Name":      str(device.get("name", "—")),
            "Model":            str(device.get("model", "—")),
            "Serial":           str(device.get("serialNumber", "—")),
            "Android Release":  str(device.get("release", "—")),
            "SDK":              str(device.get("sdk", "—")),
            "Feature Level":    str(device.get("featureLevel", "—")),
            "Type":             str(device.get("type", "—")),
            "Emulator":         str(device.get("isEmulator", "—")),
            "Online":           str(device.get("isOnline", "—")),
            "Device ID":        str(device.get("deviceId", "—")),
            "Log Filter":       str(filter_str or "—"),
        }

        for name, label in self._labels.items():
            label.setText(values.get(name, "—"))

        if project_ids:
            self._apps_label.setText("\n".join(
                f"#{i}: {app}" for i, app in enumerate(project_ids, start=1)
            ))
        else:
            self._apps_label.setText("—")

    def clear(self) -> None:
        """清空面板显示。"""
        for label in self._labels.values():
            label.setText("—")
        self._apps_label.setText("—")
