"""
Read-only listing form for warehouse operation statistics.
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
from office.service.warehouse_management_service import WarehouseManagementService
from settings.settings import Settings


class WarehouseOperationsForm(QWidget):
    """Display warehouse-focused operation summary rows."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.warehouse_service = WarehouseManagementService(store_code=bootstrap_context.store_code)
        self.setWindowTitle(f"{Settings().app_name} - Warehouse Operations")
        self.setMinimumSize(1280, 720)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Warehouse Operations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._warehouse_filter = QComboBox()
        self._status_filter = QComboBox()
        self._status_filter.addItem("All", None)
        self._status_filter.addItem("Active Only", True)
        self._status_filter.addItem("Inactive Only", False)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._warehouse_filter)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._status_filter)
        filter_layout.addStretch(1)
        filter_layout.addWidget(refresh_button)
        filter_layout.addWidget(close_button)

        self._table = QTableWidget(0, 11)
        self._table.setHorizontalHeaderLabels(
            [
                "Warehouse",
                "Code",
                "Type",
                "Active",
                "Locations",
                "Stock Rows",
                "Total Quantity",
                "Low Stock Rows",
                "Pending Movements",
                "Pending Adjustments",
                "Last Movement",
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
        self._reload_filters()
        rows = self.warehouse_service.list_warehouse_operations(
            warehouse_id=self._warehouse_filter.currentData(),
            active_only=self._status_filter.currentData(),
        )
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.warehouse_name,
                row.warehouse_code,
                row.warehouse_type,
                "Yes" if row.is_active else "No",
                str(row.location_count),
                str(row.stock_row_count),
                str(row.total_quantity),
                str(row.low_stock_count),
                str(row.pending_movement_count),
                str(row.pending_adjustment_count),
                row.last_movement_date.isoformat(sep=" ") if row.last_movement_date else "-",
            ]
            for col, value in enumerate(values):
                self._table.setItem(row_index, col, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _reload_filters(self) -> None:
        selected_warehouse = self._warehouse_filter.currentData()
        self._warehouse_filter.blockSignals(True)
        self._warehouse_filter.clear()
        self._warehouse_filter.addItem("All Warehouses", None)
        for item in self.warehouse_service.list_warehouse_lookups():
            self._warehouse_filter.addItem(item.label, item.id)
        if selected_warehouse:
            index = self._warehouse_filter.findData(selected_warehouse, role=Qt.UserRole)
            if index >= 0:
                self._warehouse_filter.setCurrentIndex(index)
        self._warehouse_filter.blockSignals(False)
