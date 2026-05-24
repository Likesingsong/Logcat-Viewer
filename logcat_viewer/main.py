#!/usr/bin/env python3
"""Logcat Viewer — 跨平台 Android logcat 可视化工具入口。

支持 GUI 模式和命令行模式：
    # GUI 模式
    python -m logcat_viewer
    python -m logcat_viewer input.logcat

    # 命令行模式（直接导出 Excel，不启动 GUI）
    python -m logcat_viewer --cli input.logcat [output.xlsx]
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from logcat_viewer import __version__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _check_pyside6() -> None:
    """检查 PySide6 是否安装。"""
    try:
        import PySide6  # noqa: F401
    except ImportError:
        sys.exit(
            "错误：缺少 PySide6 库，无法启动 GUI。\n"
            "请执行: pip install pyside6\n\n"
            "或使用 CLI 模式直接导出 Excel:\n"
            "  python -m logcat_viewer --cli input.logcat"
        )


def run_cli(input_path: str, output_path: str | None) -> None:
    """命令行模式：直接导出 Excel，不启动 GUI。"""
    from logcat_viewer.parser import read_logcat
    from logcat_viewer.exporter import export_excel
    from logcat_viewer.utils import format_count

    input_path = str(Path(input_path).resolve())
    if output_path is None:
        output_path = str(Path(input_path).with_suffix(".xlsx"))
    else:
        output_path = str(Path(output_path).resolve())

    logger.info(f"CLI 模式: 解析 {input_path}")
    print(f"📖 解析 {input_path} ...")
    metadata, entries = read_logcat(input_path)

    if not entries:
        logger.warning("未解析到任何日志条目")
        print("⚠️  未解析到任何日志条目。")
        sys.exit(1)

    logger.info(f"CLI 模式: 导出 {len(entries)} 条日志到 {output_path}")
    print(f"📊 导出 {format_count(len(entries))} 条日志 → {output_path} ...")
    export_excel(metadata, entries, output_path)
    print(f"✅ 完成")


def run_gui(open_file: str | None = None) -> None:
    """启动 GUI 模式。"""
    _check_pyside6()
    logger.info("启动 GUI 模式")

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QTimer
    from logcat_viewer.widgets.main_window import MainWindow

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Logcat Viewer")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("LogcatViewer")
    app.setStyle("Fusion")

    window = MainWindow(open_file=open_file)
    window.show()
    logger.info("GUI 窗口已显示")

    def handle_sigint(*args):
        logger.info("收到 SIGINT 信号，正在关闭...")
        window.close()
        QTimer.singleShot(100, app.quit)

    def handle_sigtstp(*args):
        logger.info("收到 SIGTSTP 信号，正在关闭...")
        window.close()
        QTimer.singleShot(100, app.quit)

    signal.signal(signal.SIGINT, handle_sigint)
    if hasattr(signal, "SIGTSTP"):
        signal.signal(signal.SIGTSTP, handle_sigtstp)

    timer = QTimer()  # 保持 Qt 事件循环活跃，确保 Unix 信号能被处理
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Logcat Viewer — Android logcat 可视化工具",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="输入的 .logcat 文件路径（GUI 模式下直接打开，CLI 模式下必选）",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="输出的 .xlsx 文件路径（仅 CLI 模式，默认与输入同名）",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="命令行模式：直接导出 Excel，不启动 GUI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Logcat Viewer v{__version__}",
    )
    args = parser.parse_args()

    if args.cli:
        if not args.input:
            sys.exit("错误：CLI 模式需要指定输入文件。\n用法: python -m logcat_viewer --cli input.logcat [output.xlsx]")
        run_cli(args.input, args.output)
    else:
        run_gui(args.input)


if __name__ == "__main__":
    main()
