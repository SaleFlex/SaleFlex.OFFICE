"""
Transaction Management form – read-only, spreadsheet-style view.

Structure
---------
Top-level tabs: "All POS"  +  one tab per POS terminal (POS 1, POS 2, …)

Each POS tab contains a vertical splitter:
  • Upper panel  – QTableWidget listing TransactionHead rows (read-only)
  • Lower panel  – QTabWidget with detail sub-tabs:
      Products | Payments | Discounts

All data is fetched on demand and is strictly read-only; no edit, add, or
delete operations are exposed.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.transaction_management_service import (
    PosTerminalSummary,
    TransactionDiscountView,
    TransactionHeadView,
    TransactionManagementService,
    TransactionPaymentView,
    TransactionProductView,
)
from settings.settings import Settings


class TransactionManagementForm(QWidget):
    """Read-only Excel-style viewer for POS transaction data."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = TransactionManagementService()
        self.setWindowTitle(f"{Settings().app_name} - Transaction Management")
        self.setMinimumSize(1400, 900)

        self._selected_transaction_id: str | None = None

        self._build_ui()
        self._load_all_data()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        header = QLabel("Transaction Management Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}"
            f"  |  Office: {self.bootstrap_context.office_code}"
            "  |  Read-Only"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)
        refresh_button = QPushButton("Refresh All")
        refresh_button.clicked.connect(self._load_all_data)

        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch(1)
        header_layout.addWidget(refresh_button)
        header_layout.addWidget(close_button)

        self._pos_tabs = QTabWidget()

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)
        root.addLayout(header_layout)
        root.addWidget(subtitle)
        root.addWidget(self._pos_tabs, stretch=1)
        root.addWidget(self._status_label)
        self.setLayout(root)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_all_data(self) -> None:
        """Rebuild POS tabs and populate all transaction grids."""
        self._pos_tabs.clear()
        self._selected_transaction_id = None

        terminals = self.service.list_pos_terminals()
        pos_ids = self.service.list_distinct_pos_ids()

        # "All POS" tab shows every transaction
        all_tab = self._build_pos_tab(pos_id=None, label="All POS")
        self._pos_tabs.addTab(all_tab, "All POS")

        # One tab per POS terminal that has at least one transaction
        for pos_id in pos_ids:
            # Try to find a matching terminal record by pos_id integer
            matching = next(
                (t for t in terminals if t.terminal_code == str(pos_id)),
                None,
            )
            label = (
                f"{matching.terminal_name} (POS {pos_id})"
                if matching
                else f"POS {pos_id}"
            )
            tab = self._build_pos_tab(pos_id=pos_id, label=label)
            self._pos_tabs.addTab(tab, label)

        total = len(self.service.list_transactions())
        self._show_status(True, f"Loaded {total} transaction(s) across {len(pos_ids)} POS terminal(s).")

    # ------------------------------------------------------------------
    # Per-POS tab construction
    # ------------------------------------------------------------------

    def _build_pos_tab(self, pos_id: int | None, label: str) -> QWidget:
        """Build a complete vertical-splitter workspace for a single POS."""
        splitter = QSplitter(Qt.Vertical)

        # ---- upper: transaction header grid ----
        tx_group = QGroupBox("Transactions")
        tx_table = self._make_transaction_table()
        self._populate_transaction_table(tx_table, pos_id)

        detail_tabs = self._build_detail_panel()
        product_table: QTableWidget = detail_tabs.findChild(QTableWidget, "productTable")
        payment_table: QTableWidget = detail_tabs.findChild(QTableWidget, "paymentTable")
        discount_table: QTableWidget = detail_tabs.findChild(QTableWidget, "discountTable")

        def on_tx_selected() -> None:
            items = tx_table.selectedItems()
            if not items:
                return
            row_idx = tx_table.currentRow()
            tx_id_item = tx_table.item(row_idx, 0)
            if tx_id_item is None:
                return
            tx_id = tx_id_item.text()
            self._selected_transaction_id = tx_id
            self._load_products(product_table, tx_id)
            self._load_payments(payment_table, tx_id)
            self._load_discounts(discount_table, tx_id)

        tx_table.itemSelectionChanged.connect(on_tx_selected)

        tx_layout = QVBoxLayout()
        tx_layout.setContentsMargins(4, 4, 4, 4)
        tx_layout.addWidget(tx_table)
        tx_group.setLayout(tx_layout)
        splitter.addWidget(tx_group)
        splitter.addWidget(detail_tabs)
        splitter.setSizes([500, 320])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Transaction header table helpers
    # ------------------------------------------------------------------

    def _make_transaction_table(self) -> QTableWidget:
        """Create and style the transaction header QTableWidget."""
        table = QTableWidget(0, 16)
        table.setHorizontalHeaderLabels([
            "ID",
            "Receipt No",
            "Closure No",
            "Date / Time",
            "POS",
            "Document Type",
            "Tx Type",
            "Status",
            "Total",
            "VAT",
            "Discount",
            "Payment",
            "Change",
            "Currency",
            "Order Source",
            "Cancelled",
        ])
        table.setColumnHidden(0, True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _populate_transaction_table(
        self, table: QTableWidget, pos_id: int | None
    ) -> None:
        """Fill *table* with transaction header rows for *pos_id* (or all)."""
        rows = self.service.list_transactions(pos_id=pos_id)
        table.setRowCount(len(rows))
        table.setSortingEnabled(False)
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r.id))
            table.setItem(i, 1, QTableWidgetItem(str(r.receipt_number)))
            table.setItem(i, 2, QTableWidgetItem(str(r.closure_number)))
            table.setItem(i, 3, QTableWidgetItem(r.transaction_date_time))
            table.setItem(i, 4, QTableWidgetItem(str(r.pos_id)))
            table.setItem(i, 5, QTableWidgetItem(r.document_type))
            table.setItem(i, 6, QTableWidgetItem(r.transaction_type))
            status_item = QTableWidgetItem(r.transaction_status)
            if r.transaction_status == "completed":
                status_item.setForeground(Qt.darkGreen)
            elif r.transaction_status in ("cancelled", "refunded"):
                status_item.setForeground(Qt.darkRed)
            table.setItem(i, 7, status_item)
            table.setItem(i, 8, self._right_aligned(r.total_amount))
            table.setItem(i, 9, self._right_aligned(r.total_vat_amount))
            table.setItem(i, 10, self._right_aligned(r.total_discount_amount))
            table.setItem(i, 11, self._right_aligned(r.total_payment_amount))
            table.setItem(i, 12, self._right_aligned(r.total_change_amount))
            table.setItem(i, 13, QTableWidgetItem(r.base_currency))
            table.setItem(i, 14, QTableWidgetItem(r.order_source))
            table.setItem(i, 15, QTableWidgetItem("Yes" if r.is_cancel else "No"))
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Detail panel (Products / Payments / Discounts)
    # ------------------------------------------------------------------

    def _build_detail_panel(self) -> QTabWidget:
        """Build the three read-only detail sub-tabs."""
        detail_tabs = QTabWidget()

        # Products tab
        product_table = QTableWidget(0, 12)
        product_table.setObjectName("productTable")
        product_table.setHorizontalHeaderLabels([
            "ID", "Line", "Code", "Product Name", "Qty", "Unit Price",
            "Discount", "Total", "VAT", "VAT %", "UOM", "Voided",
        ])
        product_table.setColumnHidden(0, True)
        self._configure_readonly_table(product_table)
        product_tab = QWidget()
        pl = QVBoxLayout()
        pl.setContentsMargins(4, 4, 4, 4)
        pl.addWidget(product_table)
        product_tab.setLayout(pl)
        detail_tabs.addTab(product_tab, "Products")

        # Payments tab
        payment_table = QTableWidget(0, 11)
        payment_table.setObjectName("paymentTable")
        payment_table.setHorizontalHeaderLabels([
            "ID", "Line", "Payment Type", "Amount", "Currency", "Curr. Total",
            "Status", "Provider", "Card Type", "Card (masked)", "Auth Code",
        ])
        payment_table.setColumnHidden(0, True)
        self._configure_readonly_table(payment_table)
        payment_tab = QWidget()
        pl2 = QVBoxLayout()
        pl2.setContentsMargins(4, 4, 4, 4)
        pl2.addWidget(payment_table)
        payment_tab.setLayout(pl2)
        detail_tabs.addTab(payment_tab, "Payments")

        # Discounts tab
        discount_table = QTableWidget(0, 6)
        discount_table.setObjectName("discountTable")
        discount_table.setHorizontalHeaderLabels([
            "ID", "Line", "Discount Type", "Amount", "Rate (%)", "Code",
        ])
        discount_table.setColumnHidden(0, True)
        self._configure_readonly_table(discount_table)
        discount_tab = QWidget()
        pl3 = QVBoxLayout()
        pl3.setContentsMargins(4, 4, 4, 4)
        pl3.addWidget(discount_table)
        discount_tab.setLayout(pl3)
        detail_tabs.addTab(discount_tab, "Discounts")

        return detail_tabs

    @staticmethod
    def _configure_readonly_table(table: QTableWidget) -> None:
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Detail table loaders
    # ------------------------------------------------------------------

    def _load_products(self, table: QTableWidget, tx_id: str) -> None:
        rows = self.service.list_transaction_products(tx_id)
        table.setRowCount(len(rows))
        table.setSortingEnabled(False)
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r.id))
            table.setItem(i, 1, QTableWidgetItem(str(r.line_no)))
            table.setItem(i, 2, QTableWidgetItem(r.product_code))
            table.setItem(i, 3, QTableWidgetItem(r.product_name))
            table.setItem(i, 4, self._right_aligned(r.quantity))
            table.setItem(i, 5, self._right_aligned(r.unit_price))
            table.setItem(i, 6, self._right_aligned(r.unit_discount))
            table.setItem(i, 7, self._right_aligned(r.total_price))
            table.setItem(i, 8, self._right_aligned(r.total_vat))
            table.setItem(i, 9, self._right_aligned(r.vat_rate))
            table.setItem(i, 10, QTableWidgetItem(r.unit_of_measure))
            table.setItem(i, 11, QTableWidgetItem("Yes" if r.is_voided else "No"))
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _load_payments(self, table: QTableWidget, tx_id: str) -> None:
        rows = self.service.list_transaction_payments(tx_id)
        table.setRowCount(len(rows))
        table.setSortingEnabled(False)
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r.id))
            table.setItem(i, 1, QTableWidgetItem(str(r.line_no)))
            table.setItem(i, 2, QTableWidgetItem(r.payment_type))
            table.setItem(i, 3, self._right_aligned(r.payment_total))
            table.setItem(i, 4, QTableWidgetItem(r.currency_code))
            table.setItem(i, 5, self._right_aligned(r.currency_total))
            status_item = QTableWidgetItem(r.payment_status)
            if r.payment_status == "approved":
                status_item.setForeground(Qt.darkGreen)
            elif r.payment_status in ("declined", "failed"):
                status_item.setForeground(Qt.darkRed)
            table.setItem(i, 6, status_item)
            table.setItem(i, 7, QTableWidgetItem(r.payment_provider))
            table.setItem(i, 8, QTableWidgetItem(r.card_type))
            table.setItem(i, 9, QTableWidgetItem(r.card_number_masked))
            table.setItem(i, 10, QTableWidgetItem(r.authorization_code))
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _load_discounts(self, table: QTableWidget, tx_id: str) -> None:
        rows = self.service.list_transaction_discounts(tx_id)
        table.setRowCount(len(rows))
        table.setSortingEnabled(False)
        for i, r in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(r.id))
            table.setItem(i, 1, QTableWidgetItem(str(r.line_no)))
            table.setItem(i, 2, QTableWidgetItem(r.discount_type_name))
            table.setItem(i, 3, self._right_aligned(r.discount_amount))
            table.setItem(i, 4, self._right_aligned(r.discount_rate))
            table.setItem(i, 5, QTableWidgetItem(r.discount_code))
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _right_aligned(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item

    def _show_status(self, success: bool, message: str) -> None:
        color = "#166534" if success else "#991b1b"
        self._status_label.setStyleSheet(f"color: {color};")
        self._status_label.setText(message)
