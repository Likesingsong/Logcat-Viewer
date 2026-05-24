"""日志表格组件 — QTableView + 排序/过滤代理模型."""

from __future__ import annotations

import logging

from PySide6.QtCore import (
    QModelIndex,
    QObject,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
    QMenu,
    QWidget,
)

from logcat_viewer.parser import (
    COL_LEVEL,
    COL_TAG,
    COL_MESSAGE,
    COL_PID,
    COL_TID,
    COL_APPLICATION,
    COL_PROCESS,
    LEVEL_ABBREV,
)

logger = logging.getLogger(__name__)


class LogcatFilterProxy(QSortFilterProxyModel):
    """支持多列组合过滤的代理模型。

    支持按 Level（集合）、Tag、Message、PID、TID 过滤，
    Tag/Message 过滤大小写不敏感。
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._level_filter: set[str] = set()
        self._tag_filter: str = ""
        self._message_filter: str = ""
        self._pid_filter: str = ""
        self._tid_filter: str = ""
        self._application_filter: str = ""
        self._process_filter: str = ""
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setSortRole(Qt.ItemDataRole.DisplayRole)
        self.setDynamicSortFilter(False)

    def apply_filters(self, filters: dict) -> None:
        """一次应用所有过滤条件。

        Args:
            filters: FilterBar.current_filters() 返回的字典。
        """
        self._level_filter = filters.get("levels", set())
        self._tag_filter = filters.get("tag", "").lower()
        self._message_filter = filters.get("message", "").lower()
        self._pid_filter = filters.get("pid", "")
        self._tid_filter = filters.get("tid", "")
        self._application_filter = filters.get("application", "").lower()
        self._process_filter = filters.get("process", "").lower()
        
        logger.info(f"应用过滤条件: levels={self._level_filter}, tag='{self._tag_filter}', "
                    f"msg='{self._message_filter}', pid='{self._pid_filter}', tid='{self._tid_filter}'")
        
        self.invalidateFilter()
        
        is_reset = (
            not self._tag_filter
            and not self._message_filter
            and not self._pid_filter
            and not self._tid_filter
            and not self._application_filter
            and not self._process_filter
        )
        if is_reset:
            self.sort(0, Qt.SortOrder.AscendingOrder)
        
        visible = self.rowCount()
        total = self.sourceModel().rowCount() if self.sourceModel() else 0
        logger.info(f"过滤结果: {visible}/{total} 条")

    def reset_filter(self) -> None:
        """重置过滤器并刷新视图。"""
        self._level_filter = set()
        self._tag_filter = ""
        self._message_filter = ""
        self._pid_filter = ""
        self._tid_filter = ""
        self._application_filter = ""
        self._process_filter = ""
        self.invalidateFilter()
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex
    ) -> bool:
        model = self.sourceModel()
        if model is None:
            return True

        if self._level_filter:
            idx = model.index(source_row, COL_LEVEL)
            level = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "").upper().strip()
            abbrev = LEVEL_ABBREV.get(level, level[0] if len(level) > 0 else "")
            if abbrev not in self._level_filter and level not in self._level_filter:
                return False

        if self._tag_filter:
            idx = model.index(source_row, COL_TAG)
            tag = (model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self._tag_filter not in tag:
                return False

        if self._message_filter:
            idx = model.index(source_row, COL_MESSAGE)
            msg = (model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self._message_filter not in msg:
                return False

        if self._pid_filter:
            idx = model.index(source_row, COL_PID)
            pid = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "")
            if self._pid_filter not in pid:
                return False

        if self._tid_filter:
            idx = model.index(source_row, COL_TID)
            tid = str(model.data(idx, Qt.ItemDataRole.DisplayRole) or "")
            if self._tid_filter not in tid:
                return False

        if self._application_filter:
            idx = model.index(source_row, COL_APPLICATION)
            app = (model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self._application_filter not in app:
                return False

        if self._process_filter:
            idx = model.index(source_row, COL_PROCESS)
            proc = (model.data(idx, Qt.ItemDataRole.DisplayRole) or "").lower()
            if self._process_filter not in proc:
                return False

        return True


class LogTableView(QTableView):
    """日志表格视图。

    特性:
    - 列排序（点击表头）
    - 自适应列宽
    - 整行选择
    - 右键复制菜单
    - Ctrl/Cmd+C 复制选中内容

    Signals:
        row_selected(int): 选中行变化（源模型行号）。
    """

    row_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proxy = LogcatFilterProxy(self)
        self.setModel(self._proxy)
        self._setup_ui()

    @property
    def proxy_model(self) -> LogcatFilterProxy:
        return self._proxy

    def apply_filters(self, filters: dict) -> None:
        """应用过滤条件。"""
        self._proxy.apply_filters(filters)
        is_reset = (
            not filters.get("tag", "")
            and not filters.get("message", "")
            and not filters.get("pid", "")
            and not filters.get("tid", "")
            and not filters.get("application", "")
            and not filters.get("process", "")
        )
        if is_reset:
            self.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.scrollToTop()
        self.viewport().update()

    def reset_filter(self) -> None:
        """重置过滤器并刷新视图。"""
        self._proxy.reset_filter()
        self.scrollToTop()
        self.viewport().update()

    def set_source_model(self, model) -> None:
        """设置源数据模型。"""
        self._proxy.setSourceModel(model)

    def source_model(self):
        """获取源数据模型。"""
        return self._proxy.sourceModel()

    def selected_source_row(self) -> int:
        """返回选中行在源模型中的行号，未选中返回 -1。"""
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return -1
        proxy_idx = indexes[0]
        source_idx = self._proxy.mapToSource(proxy_idx)
        return source_idx.row()

    # ── UI 设置 ───────────────────────────────────────────────────────────
    def _setup_ui(self) -> None:
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # 表头交互
        header = self.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 行号列
        vheader = self.verticalHeader()
        vheader.setDefaultSectionSize(22)
        vheader.setVisible(False)

        # 选中变化信号
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # 默认列宽
        col_widths = {0: 50, 1: 180, 2: 70, 3: 60, 4: 60,
                      5: 180, 6: 180, 7: 130, 8: 400}
        for col, width in col_widths.items():
            self.setColumnWidth(col, width)

    # ── 交互 ──────────────────────────────────────────────────────────────
    def keyPressEvent(self, event) -> None:
        """Ctrl/Cmd+C 复制选中行文本。"""
        if event.matches(QKeySequence.StandardKey.Copy):
            self._copy_selected()
        else:
            super().keyPressEvent(event)

    def _copy_selected(self) -> None:
        """复制选中行内容到剪贴板。"""
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return
        model = self._proxy
        row = indexes[0].row()
        cols = model.columnCount()
        parts = []
        for c in range(cols):
            idx = model.index(row, c)
            parts.append(str(model.data(idx, Qt.ItemDataRole.DisplayRole) or ""))
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText("\t".join(parts))

    def _show_context_menu(self, pos) -> None:
        """右键菜单。"""
        menu = QMenu(self)
        copy_action = menu.addAction("复制整行")
        copy_action.triggered.connect(self._copy_selected)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        menu.exec_(self.viewport().mapToGlobal(pos))

    def _on_selection_changed(self) -> None:
        """选中行变化时发射信号。"""
        row = self.selected_source_row()
        self.row_selected.emit(row)
