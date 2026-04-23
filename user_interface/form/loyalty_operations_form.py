"""
Read-only listing form for loyalty operation statistics.
"""

from __future__ import annotations

from decimal import Decimal

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
from office.service.loyalty_management_service import LoyaltyManagementService
from settings.settings import Settings


class LoyaltyOperationsForm(QWidget):
    """Display loyalty-focused operation summary rows."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.loyalty_service = LoyaltyManagementService()
        self.customer_service = CustomerManagementService(store_code=bootstrap_context.store_code)
        self.setWindowTitle(f"{Settings().app_name} - Loyalty Operations")
        self.setMinimumSize(1280, 720)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Loyalty Operations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._customer_filter = QComboBox()
        self._program_filter = QComboBox()
        self._active_filter = QComboBox()
        self._active_filter.addItem("All", None)
        self._active_filter.addItem("Active Only", True)
        self._active_filter.addItem("Inactive Only", False)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._customer_filter)
        filter_layout.addWidget(QLabel("Program"))
        filter_layout.addWidget(self._program_filter)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._active_filter)
        filter_layout.addStretch(1)
        filter_layout.addWidget(refresh_button)
        filter_layout.addWidget(close_button)

        self._table = QTableWidget(0, 11)
        self._table.setHorizontalHeaderLabels(
            [
                "Customer",
                "Program",
                "Tier",
                "Card Number",
                "Available Points",
                "Lifetime Points",
                "Total Spent",
                "Transactions",
                "Earned Points",
                "Redeemed Points",
                "Last Transaction",
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
        rows = self.loyalty_service.list_loyalty_operations(
            program_id=self._program_filter.currentData(),
            customer_id=self._customer_filter.currentData(),
            active_only=self._active_filter.currentData(),
        )
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.customer_label,
                row.loyalty_program_name,
                row.loyalty_tier_name,
                row.loyalty_card_number,
                str(row.available_points),
                str(row.lifetime_points),
                self._format_amount(row.total_spent),
                str(row.transaction_count),
                str(row.earned_points),
                str(row.redeemed_points),
                row.last_transaction_at.isoformat(sep=" ") if row.last_transaction_at else "-",
            ]
            for col, value in enumerate(values):
                self._table.setItem(row_index, col, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _reload_filters(self) -> None:
        selected_customer = self._customer_filter.currentData()
        selected_program = self._program_filter.currentData()
        self._customer_filter.blockSignals(True)
        self._program_filter.blockSignals(True)
        self._customer_filter.clear()
        self._program_filter.clear()
        self._customer_filter.addItem("All Customers", None)
        self._program_filter.addItem("All Programs", None)
        for item in self.customer_service.list_customer_lookups():
            self._customer_filter.addItem(item.label, item.id)
        for item in self.loyalty_service.list_loyalty_program_lookups():
            self._program_filter.addItem(item.label, item.id)
        if selected_customer:
            index = self._customer_filter.findData(selected_customer, role=Qt.UserRole)
            if index >= 0:
                self._customer_filter.setCurrentIndex(index)
        if selected_program:
            index = self._program_filter.findData(selected_program, role=Qt.UserRole)
            if index >= 0:
                self._program_filter.setCurrentIndex(index)
        self._customer_filter.blockSignals(False)
        self._program_filter.blockSignals(False)

    @staticmethod
    def _format_amount(value: Decimal | None) -> str:
        amount = Decimal("0") if value is None else Decimal(str(value))
        return f"{amount:.2f}"
