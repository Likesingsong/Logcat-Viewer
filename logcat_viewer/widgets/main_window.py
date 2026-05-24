"""主窗口 — 组装所有组件，处理文件打开、导出、主题切换."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from logcat_viewer.parser import read_logcat, ParseError
from logcat_viewer.exporter import export_excel, ExportError
from logcat_viewer.models.logcat_model import LogcatTableModel
from logcat_viewer.widgets.filter_bar import FilterBar
from logcat_viewer.widgets.log_table import LogTableView
from logcat_viewer.widgets.device_panel import DevicePanel
from logcat_viewer.widgets.detail_panel import DetailPanel
from logcat_viewer.widgets.stats_bar import StatsBar
from logcat_viewer.utils import (
    detect_system_theme,
    get_light_theme,
    get_dark_theme,
    LOGCAT_FILE_FILTER,
    format_count,
)

logger = logging.getLogger(__name__)


class _ParseWorker(QThread):
    """后台解析线程，避免 UI 冻结。"""

    finished = Signal(object, object)   # (metadata, entries)
    error = Signal(str)

    def __init__(self, filepath: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._filepath = filepath

    def run(self) -> None:
        try:
            metadata, entries = read_logcat(self._filepath)
            self.finished.emit(metadata, entries)
        except Exception as exc:
            self.error.emit(str(exc))


class _ExportWorker(QThread):
    """后台导出线程。"""

    finished = Signal(str)   # output_path
    error = Signal(str)

    def __init__(
        self,
        metadata: dict,
        entries: list[dict],
        output_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._metadata = metadata
        self._entries = entries
        self._output_path = output_path

    def run(self) -> None:
        try:
            export_excel(self._metadata, self._entries, self._output_path)
            self.finished.emit(self._output_path)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Logcat Viewer 主窗口。"""

    def __init__(self, open_file: str | None = None) -> None:
        super().__init__()
        self._model = LogcatTableModel(self)
        self._current_file: str | None = None
        self._dark_mode = False
        self._worker: _ParseWorker | None = None
        self._export_worker: _ExportWorker | None = None
        self._progress: QProgressDialog | None = None
        self._export_progress: QProgressDialog | None = None

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()

        QTimer.singleShot(0, self._filter_bar._do_emit_filters)

        if open_file:
            QTimer.singleShot(100, lambda: self._open_file(open_file))

    # ── UI 构建 ──────────────────────────────────────────────────────────
    def _setup_ui(self) -> None:
        self.setWindowTitle("Logcat Viewer")
        self.setMinimumSize(1100, 680)
        self.resize(1400, 900)
        self.setAcceptDrops(True)

        # --- 菜单栏 ---
        menu = self.menuBar()

        file_menu = menu.addMenu("文件(&F)")
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        export_action = QAction("导出 Excel(&E)...", self)
        export_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("退出(&Q)", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menu.addMenu("视图(&V)")
        theme_action = QAction("切换暗色模式(&T)", self)
        theme_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(theme_action)

        # --- 工具栏 ---
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(export_action)

        # --- 主体布局 ---
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 过滤栏
        self._filter_bar = FilterBar(self)
        root_layout.addWidget(self._filter_bar)

        # 水平分割：左 = 表格 + 详情，右 = 设备信息
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：垂直分割（表格 + 详情面板）
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = LogTableView(self)
        self._table.set_source_model(self._model)
        v_splitter.addWidget(self._table)

        self._detail_panel = DetailPanel(self)
        v_splitter.addWidget(self._detail_panel)

        v_splitter.setStretchFactor(0, 3)
        v_splitter.setStretchFactor(1, 1)

        h_splitter.addWidget(v_splitter)

        # 右侧：Tab 页（设备信息）
        right_tabs = QTabWidget()
        self._device_panel = DevicePanel(self)
        right_tabs.addTab(self._device_panel, "Device Info")
        h_splitter.addWidget(right_tabs)

        h_splitter.setStretchFactor(0, 4)
        h_splitter.setStretchFactor(1, 1)

        root_layout.addWidget(h_splitter, stretch=1)

        # 状态栏
        self._stats_bar = StatsBar(self)
        sb = QStatusBar(self)
        sb.addPermanentWidget(self._stats_bar)
        # 文件名显示
        self._file_label = QLabel(" 未打开文件")
        sb.addWidget(self._file_label)
        self.setStatusBar(sb)

    # ── 信号连接 ──────────────────────────────────────────────────────────
    def _connect_signals(self) -> None:
        self._filter_bar.filters_changed.connect(self._on_filters_changed)
        self._table.row_selected.connect(self._on_row_selected)

        # 代理模型行数变化 → 更新统计
        self._table.proxy_model.rowsInserted.connect(self._update_stats)
        self._table.proxy_model.rowsRemoved.connect(self._update_stats)
        self._table.proxy_model.modelReset.connect(self._update_stats)

    # ── 文件操作 ──────────────────────────────────────────────────────────
    def _on_open(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, "打开 Logcat 文件", "", LOGCAT_FILE_FILTER,
        )
        if filepath:
            self._open_file(filepath)

    def _open_file(self, filepath: str) -> None:
        """打开并解析 logcat 文件（后台线程）。"""
        logger.info(f"打开文件: {filepath}")
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"文件不存在: {filepath}")
            QMessageBox.warning(self, "文件不存在", f"找不到文件:\n{filepath}")
            return
        if not path.is_file():
            logger.warning(f"路径不是文件: {filepath}")
            QMessageBox.warning(self, "无效文件", f"路径不是文件:\n{filepath}")
            return

        self._progress = QProgressDialog(
            f"正在解析 {path.name}…", "取消", 0, 0, self,
        )
        self._progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress.setCancelButton(None)
        self._progress.show()

        self._worker = _ParseWorker(filepath, self)
        self._worker.finished.connect(self._on_parse_done)
        self._worker.error.connect(self._on_parse_error)
        self._worker.start()

    def _on_parse_done(self, metadata: dict, entries: list[dict]) -> None:
        """解析完成回调。"""
        if self._progress:
            self._progress.close()
        logger.info(f"解析完成: {len(entries)} 条日志")

        filepath = ""
        if self._worker:
            filepath = self._worker._filepath
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except RuntimeError:
                pass
            self._worker.deleteLater()
            self._worker = None

        self._model.load_data(metadata, entries)
        self._device_panel.load_metadata(metadata)
        self._detail_panel.clear()
        
        self._table.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
        self._table.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        
        self._filter_bar.reset()

        self._current_file = filepath
        path = Path(filepath) if filepath else Path(".")
        self._file_label.setText(f" {path.name}  ({format_count(len(entries))} 条)")
        self.setWindowTitle(f"Logcat Viewer — {path.name}")

        self._update_stats()

    def _on_parse_error(self, error_msg: str) -> None:
        """解析错误回调。"""
        if self._progress:
            self._progress.close()
        if self._worker:
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except RuntimeError:
                pass
            self._worker.deleteLater()
            self._worker = None
        logger.error(f"解析错误: {error_msg}")
        QMessageBox.critical(self, "解析错误", error_msg)

    # ── 导出 ──────────────────────────────────────────────────────────────
    def _on_export(self) -> None:
        if self._model.entry_count == 0:
            QMessageBox.information(self, "无数据", "没有日志数据可导出。请先打开一个 logcat 文件。")
            return

        default_name = ""
        if self._current_file:
            default_name = str(Path(self._current_file).with_suffix(".xlsx"))

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", default_name, "Excel 文件 (*.xlsx)",
        )
        if not filepath:
            return

        self._export_progress = QProgressDialog(
            "正在导出 Excel…", "取消", 0, 0, self,
        )
        self._export_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._export_progress.setCancelButton(None)
        self._export_progress.show()

        self._export_worker = _ExportWorker(
            self._model.metadata, self._model.entries, filepath, self,
        )
        self._export_worker.finished.connect(self._on_export_done)
        self._export_worker.error.connect(self._on_export_error)
        self._export_worker.start()

    def _on_export_done(self, output_path: str) -> None:
        if self._export_progress:
            self._export_progress.close()
        if self._export_worker:
            try:
                self._export_worker.finished.disconnect()
                self._export_worker.error.disconnect()
            except RuntimeError:
                pass
            self._export_worker.deleteLater()
            self._export_worker = None
        QMessageBox.information(
            self, "导出成功",
            f"已导出 {format_count(self._model.entry_count)} 条日志 →\n{output_path}",
        )

    def _on_export_error(self, error_msg: str) -> None:
        if self._export_progress:
            self._export_progress.close()
        if self._export_worker:
            try:
                self._export_worker.finished.disconnect()
                self._export_worker.error.disconnect()
            except RuntimeError:
                pass
            self._export_worker.deleteLater()
            self._export_worker = None
        QMessageBox.critical(self, "导出错误", error_msg)

    # ── 过滤 ──────────────────────────────────────────────────────────────
    def _on_filters_changed(self, filters: dict) -> None:
        """应用过滤条件，显示进度。"""
        total = self._model.entry_count
        if total < 1000:
            self._table.apply_filters(filters)
            self._update_stats()
            return

        progress = QProgressDialog("正在过滤日志...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("搜索")
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        QApplication.processEvents()

        self._table.apply_filters(filters)
        self._update_stats()

        progress.close()

    def _on_row_selected(self, row: int) -> None:
        entry = self._model.get_entry(row)
        self._detail_panel.show_entry(entry)

    def _update_stats(self, _unused: object = None) -> None:
        """更新统计栏。"""
        total = self._model.entry_count
        visible = self._table.proxy_model.rowCount()
        logger.info(f"更新统计栏: 总数={total}, 可见={visible}")

        self._stats_bar.update_stats(total, visible, self._model.level_counts)
        if self._current_file:
            path = Path(self._current_file)
            self._file_label.setText(f" {path.name}  ({format_count(total)} 条)")

    # ── 主题 ──────────────────────────────────────────────────────────────
    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        if self._dark_mode:
            app.setStyleSheet(get_dark_theme())
        else:
            # 检测系统主题
            system = detect_system_theme()
            if system == "dark":
                app.setStyleSheet(get_dark_theme())
                self._dark_mode = True
            else:
                app.setStyleSheet(get_light_theme())

    # ── 拖放支持 ──────────────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath:
                self._open_file(filepath)

    # ── 窗口关闭 ──────────────────────────────────────────────────────────
    def closeEvent(self, event) -> None:
        for worker_attr in ("_worker", "_export_worker"):
            worker = getattr(self, worker_attr, None)
            if worker and worker.isRunning():
                worker.quit()
                if not worker.wait(1000):
                    worker.terminate()
                    worker.wait()
                try:
                    worker.finished.disconnect()
                    worker.error.disconnect()
                except RuntimeError:
                    pass
                worker.deleteLater()
                setattr(self, worker_attr, None)
        super().closeEvent(event)
