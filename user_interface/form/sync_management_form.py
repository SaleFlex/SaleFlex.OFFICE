"""
Data Sync and Backup management form.

Provides spreadsheet-style tabbed views for:
  - Pending Queue   : outbox items waiting to be dispatched.
  - Failed Items    : outbox items that exhausted all retries.
  - Sent History    : successfully delivered outbox items.
  - GATE Notifications : inbound notifications received from SaleFlex.GATE.

Operators can reset failed items to pending (manual retry), delete individual
records, clear the entire sent history, and mark GATE notifications as read.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.sync_management_service import (
    GateNotificationView,
    SyncManagementService,
    SyncQueueItemView,
    SyncSummaryView,
)
from settings.settings import Settings

# Column definitions for sync queue item grids
_QUEUE_COLUMNS = [
    "Connector",
    "Event Type",
    "Status",
    "Retries",
    "Max Retries",
    "Created At",
    "Updated At",
    "Sent At",
    "Error",
]

# Column definitions for notification grid
_NOTIF_COLUMNS = [
    "Type",
    "Title",
    "Body",
    "Read",
    "Received At",
]


def _make_table(columns: list[str]) -> QTableWidget:
    """Create a read-only QTableWidget with the given column headers."""
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    return table


def _fill_queue_table(table: QTableWidget, rows: list[SyncQueueItemView]) -> None:
    """Populate a sync queue grid from a list of SyncQueueItemView."""
    table.setRowCount(0)
    for view in rows:
        row = table.rowCount()
        table.insertRow(row)
        for col, value in enumerate([
            view.connector_type,
            view.event_type,
            view.status,
            str(view.retry_count),
            str(view.max_retries),
            view.created_at,
            view.updated_at,
            view.sent_at,
            view.error_message,
        ]):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, view.id)
            table.setItem(row, col, item)
    table.resizeColumnsToContents()


def _fill_notif_table(table: QTableWidget, rows: list[GateNotificationView]) -> None:
    """Populate the notification grid from a list of GateNotificationView."""
    table.setRowCount(0)
    for view in rows:
        row = table.rowCount()
        table.insertRow(row)
        for col, value in enumerate([
            view.notification_type,
            view.title,
            view.body,
            "Yes" if view.is_read else "No",
            view.received_at,
        ]):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, view.id)
            table.setItem(row, col, item)
        if not view.is_read:
            for col in range(table.columnCount()):
                cell = table.item(row, col)
                if cell:
                    cell.setForeground(Qt.darkBlue)
    table.resizeColumnsToContents()


def _selected_id(table: QTableWidget) -> str | None:
    """Return the UserRole UUID of the selected row, or None if no selection."""
    selected = table.selectedItems()
    if not selected:
        return None
    return selected[0].data(Qt.UserRole)


class SyncManagementForm(QWidget):
    """Monitor and manage the integration outbox and GATE notification inbox."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = SyncManagementService()
        self.setWindowTitle(f"{Settings().app_name} - Data Sync and Backup")
        self.setMinimumSize(1200, 780)

        self._pending_rows: list[SyncQueueItemView] = []
        self._failed_rows: list[SyncQueueItemView] = []
        self._sent_rows: list[SyncQueueItemView] = []
        self._notif_rows: list[GateNotificationView] = []

        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        header = QLabel("Data Sync and Backup")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))

        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}"
            f"  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; color: #1e3a5f;"
        )

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)

        refresh_all_button = QPushButton("Refresh All")
        refresh_all_button.clicked.connect(self.refresh_all)

        header_row = QHBoxLayout()
        header_row.addWidget(header)
        header_row.addStretch(1)
        header_row.addWidget(self._summary_label)
        header_row.addWidget(refresh_all_button)
        header_row.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_pending_tab(), "Pending Queue")
        self._tabs.addTab(self._build_failed_tab(), "Failed Items")
        self._tabs.addTab(self._build_sent_tab(), "Sent History")
        self._tabs.addTab(self._build_notifications_tab(), "GATE Notifications")

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)
        root.addLayout(header_row)
        root.addWidget(subtitle)
        root.addWidget(self._tabs)
        root.addWidget(self._status_label)
        self.setLayout(root)
        self._apply_styles()

    # ------------------------------------------------------------------
    # Pending Queue tab
    # ------------------------------------------------------------------

    def _build_pending_tab(self) -> QWidget:
        tab = QWidget()

        self._pending_table = _make_table(_QUEUE_COLUMNS)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_pending)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch(1)
        info = QLabel("Items waiting to be dispatched to an external system.")
        info.setStyleSheet("color: #64748b; font-size: 11px;")
        toolbar.addWidget(info)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self._pending_table)
        tab.setLayout(layout)
        return tab

    # ------------------------------------------------------------------
    # Failed Items tab
    # ------------------------------------------------------------------

    def _build_failed_tab(self) -> QWidget:
        tab = QWidget()

        self._failed_table = _make_table(_QUEUE_COLUMNS)
        self._failed_table.itemSelectionChanged.connect(
            self._on_failed_selection_changed
        )

        self._failed_detail = QTextEdit()
        self._failed_detail.setReadOnly(True)
        self._failed_detail.setMaximumHeight(90)
        self._failed_detail.setPlaceholderText("Select a row to see error details.")

        self._btn_reset_one = QPushButton("Reset Selected to Pending")
        self._btn_reset_one.setEnabled(False)
        self._btn_reset_one.clicked.connect(self._on_reset_selected)

        self._btn_delete_failed = QPushButton("Delete Selected")
        self._btn_delete_failed.setEnabled(False)
        self._btn_delete_failed.clicked.connect(self._on_delete_failed_selected)

        self._btn_reset_all = QPushButton("Reset All Failed to Pending")
        self._btn_reset_all.clicked.connect(self._on_reset_all_failed)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_failed)
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(self._btn_reset_one)
        toolbar.addWidget(self._btn_delete_failed)
        toolbar.addStretch(1)
        toolbar.addWidget(self._btn_reset_all)

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(self._failed_table)
        layout.addWidget(QLabel("Error details:"))
        layout.addWidget(self._failed_detail)
        tab.setLayout(layout)
        return tab

    # ------------------------------------------------------------------
    # Sent History tab
    # ------------------------------------------------------------------

    def _build_sent_tab(self) -> QWidget:
        tab = QWidget()

        self._sent_table = _make_table(_QUEUE_COLUMNS)
        self._sent_table.itemSelectionChanged.connect(
            self._on_sent_selection_changed
        )

        self._btn_delete_sent = QPushButton("Delete Selected")
        self._btn_delete_sent.setEnabled(False)
        self._btn_delete_sent.clicked.connect(self._on_delete_sent_selected)

        self._btn_clear_sent = QPushButton("Clear All Sent History")
        self._btn_clear_sent.clicked.connect(self._on_clear_sent_history)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_sent)
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(self._btn_delete_sent)
        toolbar.addStretch(1)
        toolbar.addWidget(self._btn_clear_sent)

        info = QLabel("Successfully delivered records. Safe to clear periodically.")
        info.setStyleSheet("color: #64748b; font-size: 11px;")

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(info)
        layout.addWidget(self._sent_table)
        tab.setLayout(layout)
        return tab

    # ------------------------------------------------------------------
    # GATE Notifications tab
    # ------------------------------------------------------------------

    def _build_notifications_tab(self) -> QWidget:
        tab = QWidget()

        self._notif_table = _make_table(_NOTIF_COLUMNS)
        self._notif_table.itemSelectionChanged.connect(
            self._on_notif_selection_changed
        )

        self._notif_body = QTextEdit()
        self._notif_body.setReadOnly(True)
        self._notif_body.setMaximumHeight(100)
        self._notif_body.setPlaceholderText("Select a notification to read its body.")

        self._btn_mark_read = QPushButton("Mark Selected as Read")
        self._btn_mark_read.setEnabled(False)
        self._btn_mark_read.clicked.connect(self._on_mark_notification_read)

        self._btn_mark_all_read = QPushButton("Mark All as Read")
        self._btn_mark_all_read.clicked.connect(self._on_mark_all_notifications_read)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._load_notifications)
        toolbar.addWidget(btn_refresh)
        toolbar.addWidget(self._btn_mark_read)
        toolbar.addStretch(1)
        toolbar.addWidget(self._btn_mark_all_read)

        info = QLabel("Inbound notifications received from SaleFlex.GATE. Unread items are shown in bold blue.")
        info.setStyleSheet("color: #64748b; font-size: 11px;")

        layout = QVBoxLayout()
        layout.addLayout(toolbar)
        layout.addWidget(info)
        layout.addWidget(self._notif_table)
        layout.addWidget(QLabel("Notification body:"))
        layout.addWidget(self._notif_body)
        tab.setLayout(layout)
        return tab

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        """Reload all tabs and update the summary header."""
        self._load_pending()
        self._load_failed()
        self._load_sent()
        self._load_notifications()
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        summary: SyncSummaryView = self.service.get_summary()
        self._summary_label.setText(
            f"Pending: {summary.pending_count}  |  "
            f"Failed: {summary.failed_count}  |  "
            f"Sent: {summary.sent_count}  |  "
            f"Unread Notifications: {summary.unread_notifications}"
        )

    def _load_pending(self) -> None:
        self._pending_rows = self.service.list_pending()
        _fill_queue_table(self._pending_table, self._pending_rows)
        self._refresh_summary()

    def _load_failed(self) -> None:
        self._failed_rows = self.service.list_failed()
        _fill_queue_table(self._failed_table, self._failed_rows)
        self._btn_reset_one.setEnabled(False)
        self._btn_delete_failed.setEnabled(False)
        self._failed_detail.clear()
        self._refresh_summary()

    def _load_sent(self) -> None:
        self._sent_rows = self.service.list_sent()
        _fill_queue_table(self._sent_table, self._sent_rows)
        self._btn_delete_sent.setEnabled(False)
        self._refresh_summary()

    def _load_notifications(self) -> None:
        self._notif_rows = self.service.list_notifications()
        _fill_notif_table(self._notif_table, self._notif_rows)
        self._btn_mark_read.setEnabled(False)
        self._notif_body.clear()
        self._refresh_summary()

    # ------------------------------------------------------------------
    # Selection handlers
    # ------------------------------------------------------------------

    def _on_failed_selection_changed(self) -> None:
        selected_id = _selected_id(self._failed_table)
        enabled = selected_id is not None
        self._btn_reset_one.setEnabled(enabled)
        self._btn_delete_failed.setEnabled(enabled)
        if enabled:
            for view in self._failed_rows:
                if view.id == selected_id:
                    self._failed_detail.setPlainText(view.error_message or "(no error message)")
                    break
        else:
            self._failed_detail.clear()

    def _on_sent_selection_changed(self) -> None:
        self._btn_delete_sent.setEnabled(
            _selected_id(self._sent_table) is not None
        )

    def _on_notif_selection_changed(self) -> None:
        selected_id = _selected_id(self._notif_table)
        self._btn_mark_read.setEnabled(selected_id is not None)
        if selected_id:
            for view in self._notif_rows:
                if view.id == selected_id:
                    self._notif_body.setPlainText(view.body or "(no body)")
                    break
        else:
            self._notif_body.clear()

    # ------------------------------------------------------------------
    # Action handlers – Failed Items
    # ------------------------------------------------------------------

    def _on_reset_selected(self) -> None:
        item_id = _selected_id(self._failed_table)
        if not item_id:
            return
        result = self.service.reset_to_pending(item_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_failed()
            self._load_pending()

    def _on_delete_failed_selected(self) -> None:
        item_id = _selected_id(self._failed_table)
        if not item_id:
            return
        answer = QMessageBox.question(
            self,
            "Delete Sync Item",
            "Permanently delete this failed sync item?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_item(item_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_failed()

    def _on_reset_all_failed(self) -> None:
        answer = QMessageBox.question(
            self,
            "Reset All Failed",
            "Reset ALL failed sync items back to pending?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.reset_all_failed()
        self._show_status(result.success, result.message)
        if result.success:
            self._load_failed()
            self._load_pending()

    # ------------------------------------------------------------------
    # Action handlers – Sent History
    # ------------------------------------------------------------------

    def _on_delete_sent_selected(self) -> None:
        item_id = _selected_id(self._sent_table)
        if not item_id:
            return
        result = self.service.delete_item(item_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_sent()

    def _on_clear_sent_history(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear Sent History",
            "Delete ALL sent sync records? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.clear_sent_history()
        self._show_status(result.success, result.message)
        if result.success:
            self._load_sent()

    # ------------------------------------------------------------------
    # Action handlers – GATE Notifications
    # ------------------------------------------------------------------

    def _on_mark_notification_read(self) -> None:
        notif_id = _selected_id(self._notif_table)
        if not notif_id:
            return
        result = self.service.mark_notification_read(notif_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_notifications()

    def _on_mark_all_notifications_read(self) -> None:
        result = self.service.mark_all_notifications_read()
        self._show_status(result.success, result.message)
        if result.success:
            self._load_notifications()

    # ------------------------------------------------------------------
    # Status label helper
    # ------------------------------------------------------------------

    def _show_status(self, success: bool, message: str) -> None:
        colour = "#166534" if success else "#991b1b"
        self._status_label.setStyleSheet(
            f"color: {colour}; font-weight: 600; font-size: 12px;"
        )
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Fullscreen
    # ------------------------------------------------------------------

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.showFullScreen()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f8fafc;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                padding: 6px 18px;
                margin-right: 2px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1d4ed8;
            }
            QTableWidget {
                border: 1px solid #e2e8f0;
                gridline-color: #e2e8f0;
                selection-background-color: #dbeafe;
                selection-color: #1e3a8a;
            }
            QTableWidget::item:alternate {
                background-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #1d4ed8;
                color: #ffffff;
                font-weight: 700;
                padding: 4px 8px;
                border: none;
            }
            QPushButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: 1px solid #1e40af;
                border-radius: 6px;
                padding: 5px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #1e3a8a;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                border-color: #94a3b8;
            }
            QTextEdit {
                border: 1px solid #e2e8f0;
                background-color: #f8fafc;
                font-family: monospace;
                font-size: 12px;
            }
            """
        )
