"""
Read-only listing form for customer operation statistics.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.customer_management_service import CustomerManagementService
from settings.settings import Settings


class CustomerOperationsForm(QWidget):
    """Display customer-focused operation summary rows."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = CustomerManagementService(store_code=bootstrap_context.store_id)
        self.setWindowTitle(f"{Settings().app_name} - Customer Operations")
        self.setMinimumSize(1180, 680)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Customer Operations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_id}  |  Office: {self.bootstrap_context.office_id}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._segment_filter = QComboBox()
        self._active_filter = QComboBox()
        self._active_filter.addItem("All", None)
        self._active_filter.addItem("Active Only", True)
        self._active_filter.addItem("Inactive Only", False)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Segment"))
        filter_layout.addWidget(self._segment_filter)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._active_filter)
        filter_layout.addStretch(1)
        filter_layout.addWidget(refresh_button)
        filter_layout.addWidget(close_button)

        self._table = QTableWidget(0, 10)
        self._table.setHorizontalHeaderLabels(
            [
                "Customer",
                "Phone",
                "Email",
                "Segments",
                "Loyalty Program",
                "Tier",
                "Available Points",
                "Lifetime Points",
                "Point Transactions",
                "Last Point Transaction",
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
        self._reload_segment_filter()
        active_filter_value = self._active_filter.currentData()
        operations = self.service.list_customer_operations(
            segment_id=self._segment_filter.currentData(),
            active_only=active_filter_value is True,
        )
        if active_filter_value is False:
            operations = [row for row in operations if not row.is_active]

        self._table.setRowCount(len(operations))
        for row_index, row in enumerate(operations):
            values = [
                row.customer_name,
                row.phone_number,
                row.email_address,
                row.segment_labels,
                row.loyalty_program_name,
                row.loyalty_tier_name,
                str(row.available_points),
                str(row.lifetime_points),
                str(row.point_transaction_count),
                row.last_point_transaction_at.isoformat(sep=" ")
                if row.last_point_transaction_at
                else "-",
            ]
            for col, value in enumerate(values):
                self._table.setItem(row_index, col, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _reload_segment_filter(self) -> None:
        current_id = self._segment_filter.currentData()
        self._segment_filter.blockSignals(True)
        self._segment_filter.clear()
        self._segment_filter.addItem("All Segments", None)
        for item in self.service.list_customer_segment_lookups():
            self._segment_filter.addItem(item.label, item.id)
        if current_id:
            index = self._segment_filter.findData(current_id, role=Qt.UserRole)
            if index >= 0:
                self._segment_filter.setCurrentIndex(index)
        self._segment_filter.blockSignals(False)
