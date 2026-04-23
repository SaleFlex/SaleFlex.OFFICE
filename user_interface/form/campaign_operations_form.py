"""
Read-only listing form for campaign operation statistics.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.campaign_management_service import CampaignManagementService
from settings.settings import Settings


class CampaignOperationsForm(QWidget):
    """Display campaign usage totals and last usage snapshots."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = CampaignManagementService(store_code=bootstrap_context.store_code)
        self.setWindowTitle(f"{Settings().app_name} - Campaign Operations")
        self.setMinimumSize(980, 620)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Campaign Operations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._campaign_filter = QComboBox()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Campaign"))
        filter_layout.addWidget(self._campaign_filter, stretch=1)
        filter_layout.addWidget(refresh_button)
        filter_layout.addWidget(close_button)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            [
                "Code",
                "Campaign Name",
                "Campaign Type",
                "Active",
                "Usage Count",
                "Total Discount",
                "Last Usage",
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(filter_layout)
        root.addWidget(self._table)
        self.setLayout(root)

    def refresh(self) -> None:
        self._reload_campaign_filter()
        selected_campaign_id = self._campaign_filter.currentData()
        rows = self.service.list_campaign_operations(campaign_id=selected_campaign_id)
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(row.campaign_code))
            self._table.setItem(row_index, 1, QTableWidgetItem(row.campaign_name))
            self._table.setItem(row_index, 2, QTableWidgetItem(row.campaign_type_name))
            self._table.setItem(row_index, 3, QTableWidgetItem("Yes" if row.is_active else "No"))
            self._table.setItem(row_index, 4, QTableWidgetItem(str(row.usage_count)))
            self._table.setItem(
                row_index,
                5,
                QTableWidgetItem(f"{row.total_discount_amount:.2f}"),
            )
            self._table.setItem(
                row_index,
                6,
                QTableWidgetItem(row.last_usage_at.isoformat(sep=" ") if row.last_usage_at else "-"),
            )
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _reload_campaign_filter(self) -> None:
        current_id = self._campaign_filter.currentData()
        self._campaign_filter.blockSignals(True)
        self._campaign_filter.clear()
        self._campaign_filter.addItem("All Campaigns", None)
        for item in self.service.list_campaign_lookups():
            self._campaign_filter.addItem(item.label, item.id)
        if current_id:
            index = self._campaign_filter.findData(current_id, role=Qt.UserRole)
            if index >= 0:
                self._campaign_filter.setCurrentIndex(index)
        self._campaign_filter.blockSignals(False)
