"""工具模块 — 平台检测、主题管理、辅助函数."""

from __future__ import annotations

import logging
import platform
import sys

logger = logging.getLogger(__name__)


# ── 平台检测 ────────────────────────────────────────────────────────────────
def is_macos() -> bool:
    return sys.platform == "darwin"

def is_windows() -> bool:
    return sys.platform == "win32"

def is_linux() -> bool:
    return sys.platform.startswith("linux")

def platform_name() -> str:
    """返回人类可读的平台名。"""
    return platform.system()


# ── 暗色模式 ────────────────────────────────────────────────────────────────
_LIGHT_THEME = """
QMainWindow {
    background-color: #FAFAFA;
}
QTableWidget, QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #F5F5F5;
    gridline-color: #E0E0E0;
    selection-background-color: #BBDEFB;
    selection-color: #000000;
    border: 1px solid #D0D0D0;
}
QHeaderView::section {
    background-color: #E8E8E8;
    color: #333333;
    padding: 4px;
    border: 1px solid #D0D0D0;
    font-weight: bold;
}
QLineEdit, QComboBox {
    border: 1px solid #C0C0C0;
    border-radius: 3px;
    padding: 4px 6px;
    background-color: #FFFFFF;
}
QCheckBox {
    spacing: 4px;
}
QPushButton {
    background-color: #E0E0E0;
    border: 1px solid #C0C0C0;
    border-radius: 3px;
    padding: 5px 12px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #D0D0D0;
}
QPushButton:pressed {
    background-color: #C0C0C0;
}
QStatusBar {
    background-color: #F0F0F0;
    border-top: 1px solid #D0D0D0;
    color: #555555;
}
QMenuBar {
    background-color: #F0F0F0;
    border-bottom: 1px solid #D0D0D0;
}
QMenuBar::item:selected {
    background-color: #D0D0D0;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #C0C0C0;
}
QMenu::item:selected {
    background-color: #BBDEFB;
}
QTabWidget::pane {
    border: 1px solid #D0D0D0;
    background-color: #FFFFFF;
}
QTabBar::tab {
    background-color: #E8E8E8;
    padding: 6px 14px;
    border: 1px solid #D0D0D0;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #FFFFFF;
}
QSplitter::handle {
    background-color: #D0D0D0;
}
QToolBar {
    background-color: #F5F5F5;
    border-bottom: 1px solid #D0D0D0;
    spacing: 4px;
}
QLabel#statsLabel {
    color: #666666;
    font-size: 11px;
}
QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}
"""

_DARK_THEME = """
QMainWindow {
    background-color: #1E1E1E;
}
QTableWidget, QTableView {
    background-color: #252526;
    alternate-background-color: #2D2D30;
    gridline-color: #3E3E42;
    selection-background-color: #264F78;
    selection-color: #CCCCCC;
    border: 1px solid #3E3E42;
    color: #D4D4D4;
}
QHeaderView::section {
    background-color: #333333;
    color: #CCCCCC;
    padding: 4px;
    border: 1px solid #3E3E42;
    font-weight: bold;
}
QLineEdit, QComboBox {
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 4px 6px;
    background-color: #3C3C3C;
    color: #D4D4D4;
}
QCheckBox {
    spacing: 4px;
    color: #D4D4D4;
}
QPushButton {
    background-color: #3C3C3C;
    border: 1px solid #3E3E42;
    border-radius: 3px;
    padding: 5px 12px;
    min-height: 24px;
    color: #D4D4D4;
}
QPushButton:hover {
    background-color: #4A4A4A;
}
QPushButton:pressed {
    background-color: #505050;
}
QStatusBar {
    background-color: #007ACC;
    border-top: 1px solid #3E3E42;
    color: #FFFFFF;
}
QMenuBar {
    background-color: #2D2D30;
    border-bottom: 1px solid #3E3E42;
    color: #D4D4D4;
}
QMenuBar::item:selected {
    background-color: #3E3E42;
}
QMenu {
    background-color: #2D2D30;
    border: 1px solid #3E3E42;
    color: #D4D4D4;
}
QMenu::item:selected {
    background-color: #264F78;
}
QTabWidget::pane {
    border: 1px solid #3E3E42;
    background-color: #252526;
}
QTabBar::tab {
    background-color: #2D2D30;
    padding: 6px 14px;
    border: 1px solid #3E3E42;
    border-bottom: none;
    color: #D4D4D4;
}
QTabBar::tab:selected {
    background-color: #252526;
}
QSplitter::handle {
    background-color: #3E3E42;
}
QToolBar {
    background-color: #2D2D30;
    border-bottom: 1px solid #3E3E42;
    spacing: 4px;
}
QLabel#statsLabel {
    color: #CCCCCC;
    font-size: 11px;
}
QTextEdit {
    background-color: #1E1E1E;
    border: 1px solid #3E3E42;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
    color: #D4D4D4;
}
"""


def get_light_theme() -> str:
    return _LIGHT_THEME

def get_dark_theme() -> str:
    return _DARK_THEME


# ── 文件对话框过滤器 ────────────────────────────────────────────────────────
LOGCAT_FILE_FILTER = "Logcat 文件 (*.logcat *.json *.txt *.log *.new-log);;所有文件 (*)"


# ── 辅助函数 ────────────────────────────────────────────────────────────────
def format_count(n: int) -> str:
    """格式化数字，超过 1000 加千分位分隔符。"""
    return f"{n:,}"


def detect_system_theme() -> str:
    """尝试检测系统深色模式设置。

    Returns:
        "dark" 或 "light"（默认）。
    """
    if is_macos():
        try:
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode == 0 and "Dark" in result.stdout:
                return "dark"
        except Exception as e:
            logger.debug(f"检测 macOS 主题失败: {e}")
    elif is_windows():
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            if value == 0:
                return "dark"
        except Exception as e:
            logger.debug(f"检测 Windows 主题失败: {e}")
    elif is_linux():
        try:
            import subprocess
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=2,
            )
            if "dark" in result.stdout.lower():
                return "dark"
        except Exception as e:
            logger.debug(f"检测 Linux 主题失败: {e}")
    return "light"
