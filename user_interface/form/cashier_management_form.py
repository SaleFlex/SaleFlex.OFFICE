"""
Cashier management module form with grid-based workflows.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.cashier_management_service import (
    CashierManagementService,
    CashierPerformanceTargetView,
    CashierTransactionMetricView,
    CashierView,
)
from settings.settings import Settings


class CashierManagementForm(QWidget):
    """Manage cashier records, performance targets, and transaction metric views."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = CashierManagementService(store_code=bootstrap_context.store_id)
        self.setWindowTitle(f"{Settings().app_name} - Cashier Management")
        self.setMinimumSize(1280, 760)

        self._cashiers: list[CashierView] = []
        self._targets: list[CashierPerformanceTargetView] = []
        self._transactions: list[CashierTransactionMetricView] = []
        self._selected_cashier_id: str | None = None
        self._selected_target_id: str | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Cashier Operations Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_id}  |  Office: {self.bootstrap_context.office_id}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("color: #0f172a;")

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)

        header_layout = QHBoxLayout()
        header_layout.addStretch(1)
        header_layout.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_cashier_tab(), "Cashier List")
        self._tabs.addTab(self._build_target_tab(), "Performance Targets")
        self._tabs.addTab(self._build_transaction_tab(), "Transaction Metrics")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_cashier_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._cashier_table = QTableWidget(0, 8)
        self._cashier_table.setHorizontalHeaderLabels(
            [
                "No",
                "Username",
                "Name",
                "Last Name",
                "Role",
                "Active",
                "Identity",
                "Last Login",
            ]
        )
        self._cashier_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._cashier_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._cashier_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._cashier_table.itemSelectionChanged.connect(self._on_cashier_row_selected)
        self._cashier_table.verticalHeader().setVisible(False)
        self._cashier_table.setAlternatingRowColors(True)

        table_container = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._cashier_table)
        table_container.setLayout(table_layout)

        editor_box = QGroupBox("Cashier Editor")
        editor_layout = QFormLayout()

        self._cashier_no_input = QSpinBox()
        self._cashier_no_input.setRange(1, 999999)
        self._cashier_username_input = QLineEdit()
        self._cashier_name_input = QLineEdit()
        self._cashier_last_name_input = QLineEdit()
        self._cashier_password_input = QLineEdit()
        self._cashier_identity_input = QLineEdit()
        self._cashier_description_input = QLineEdit()
        self._cashier_admin_checkbox = QCheckBox("Administrator")
        self._cashier_manager_checkbox = QCheckBox("Manager")
        self._cashier_active_checkbox = QCheckBox("Active")

        editor_layout.addRow("No", self._cashier_no_input)
        editor_layout.addRow("Username", self._cashier_username_input)
        editor_layout.addRow("Name", self._cashier_name_input)
        editor_layout.addRow("Last Name", self._cashier_last_name_input)
        editor_layout.addRow("Password", self._cashier_password_input)
        editor_layout.addRow("Identity Number", self._cashier_identity_input)
        editor_layout.addRow("Description", self._cashier_description_input)
        editor_layout.addRow(self._cashier_admin_checkbox)
        editor_layout.addRow(self._cashier_manager_checkbox)
        editor_layout.addRow(self._cashier_active_checkbox)

        cash_actions = QHBoxLayout()
        new_cashier_button = QPushButton("New")
        save_cashier_button = QPushButton("Save")
        delete_cashier_button = QPushButton("Delete")
        refresh_cashier_button = QPushButton("Refresh")

        new_cashier_button.clicked.connect(self._clear_cashier_editor)
        save_cashier_button.clicked.connect(self._save_cashier)
        delete_cashier_button.clicked.connect(self._delete_cashier)
        refresh_cashier_button.clicked.connect(self.refresh_cashiers)

        cash_actions.addWidget(new_cashier_button)
        cash_actions.addWidget(save_cashier_button)
        cash_actions.addWidget(delete_cashier_button)
        cash_actions.addWidget(refresh_cashier_button)

        editor_wrapper = QVBoxLayout()
        editor_wrapper.addLayout(editor_layout)
        editor_wrapper.addStretch(1)
        editor_wrapper.addLayout(cash_actions)
        editor_box.setLayout(editor_wrapper)

        splitter.addWidget(table_container)
        splitter.addWidget(editor_box)
        splitter.setSizes([900, 360])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_target_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left_container = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._target_cashier_filter_combo = QComboBox()
        self._target_cashier_filter_combo.currentIndexChanged.connect(self.refresh_targets)
        filter_layout.addWidget(QLabel("Cashier"))
        filter_layout.addWidget(self._target_cashier_filter_combo)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._target_table = QTableWidget(0, 8)
        self._target_table.setHorizontalHeaderLabels(
            [
                "Cashier",
                "Period",
                "Start",
                "End",
                "Target Sales",
                "Target Txn",
                "Achievement %",
                "Status",
            ]
        )
        self._target_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._target_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._target_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._target_table.itemSelectionChanged.connect(self._on_target_row_selected)
        self._target_table.verticalHeader().setVisible(False)
        self._target_table.setAlternatingRowColors(True)
        left_layout.addWidget(self._target_table)
        left_container.setLayout(left_layout)

        editor_box = QGroupBox("Performance Target Editor")
        editor_grid = QGridLayout()

        self._target_cashier_combo = QComboBox()
        self._target_period_combo = QComboBox()
        self._target_period_combo.addItems(["DAILY", "WEEKLY", "MONTHLY"])
        self._target_start_date_input = QDateEdit()
        self._target_start_date_input.setCalendarPopup(True)
        self._target_end_date_input = QDateEdit()
        self._target_end_date_input.setCalendarPopup(True)
        self._target_start_date_input.setDate(QDate.currentDate())
        self._target_end_date_input.setDate(QDate.currentDate())
        self._target_total_sales_input = QDoubleSpinBox()
        self._target_total_sales_input.setDecimals(2)
        self._target_total_sales_input.setMaximum(10_000_000_000)
        self._target_transactions_count_input = QSpinBox()
        self._target_transactions_count_input.setRange(0, 1_000_000)
        self._target_achievement_input = QDoubleSpinBox()
        self._target_achievement_input.setDecimals(2)
        self._target_achievement_input.setRange(0, 100)
        self._target_status_combo = QComboBox()
        self._target_status_combo.addItems(["ACTIVE", "COMPLETED", "SUSPENDED", "CANCELLED"])
        self._target_on_track_checkbox = QCheckBox("On Track")
        self._target_on_track_checkbox.setChecked(True)
        self._target_description_input = QPlainTextEdit()
        self._target_description_input.setPlaceholderText("Target notes...")
        self._target_description_input.setMaximumHeight(120)

        editor_grid.addWidget(QLabel("Cashier"), 0, 0)
        editor_grid.addWidget(self._target_cashier_combo, 0, 1)
        editor_grid.addWidget(QLabel("Period"), 1, 0)
        editor_grid.addWidget(self._target_period_combo, 1, 1)
        editor_grid.addWidget(QLabel("Start Date"), 2, 0)
        editor_grid.addWidget(self._target_start_date_input, 2, 1)
        editor_grid.addWidget(QLabel("End Date"), 3, 0)
        editor_grid.addWidget(self._target_end_date_input, 3, 1)
        editor_grid.addWidget(QLabel("Target Sales"), 4, 0)
        editor_grid.addWidget(self._target_total_sales_input, 4, 1)
        editor_grid.addWidget(QLabel("Target Transactions"), 5, 0)
        editor_grid.addWidget(self._target_transactions_count_input, 5, 1)
        editor_grid.addWidget(QLabel("Achievement %"), 6, 0)
        editor_grid.addWidget(self._target_achievement_input, 6, 1)
        editor_grid.addWidget(QLabel("Status"), 7, 0)
        editor_grid.addWidget(self._target_status_combo, 7, 1)
        editor_grid.addWidget(self._target_on_track_checkbox, 8, 1)
        editor_grid.addWidget(QLabel("Description"), 9, 0)
        editor_grid.addWidget(self._target_description_input, 9, 1)

        target_actions = QHBoxLayout()
        new_target_button = QPushButton("New")
        save_target_button = QPushButton("Save")
        delete_target_button = QPushButton("Delete")
        refresh_target_button = QPushButton("Refresh")

        new_target_button.clicked.connect(self._clear_target_editor)
        save_target_button.clicked.connect(self._save_target)
        delete_target_button.clicked.connect(self._delete_target)
        refresh_target_button.clicked.connect(self.refresh_targets)

        target_actions.addWidget(new_target_button)
        target_actions.addWidget(save_target_button)
        target_actions.addWidget(delete_target_button)
        target_actions.addWidget(refresh_target_button)

        editor_wrapper = QVBoxLayout()
        editor_wrapper.addLayout(editor_grid)
        editor_wrapper.addStretch(1)
        editor_wrapper.addLayout(target_actions)
        editor_box.setLayout(editor_wrapper)

        splitter.addWidget(left_container)
        splitter.addWidget(editor_box)
        splitter.setSizes([900, 360])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_transaction_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self._transaction_cashier_filter_combo = QComboBox()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_transactions)
        self._transaction_cashier_filter_combo.currentIndexChanged.connect(
            self.refresh_transactions
        )

        filter_layout.addWidget(QLabel("Cashier"))
        filter_layout.addWidget(self._transaction_cashier_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)

        self._transaction_table = QTableWidget(0, 10)
        self._transaction_table.setHorizontalHeaderLabels(
            [
                "Cashier",
                "Start",
                "End",
                "Total Time (sec)",
                "Total Amount",
                "Items",
                "Payment",
                "Efficiency",
                "Complexity",
                "Cancelled",
            ]
        )
        self._transaction_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._transaction_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._transaction_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._transaction_table.verticalHeader().setVisible(False)
        self._transaction_table.setAlternatingRowColors(True)
        self._transaction_table.itemSelectionChanged.connect(self._on_transaction_row_selected)

        self._transaction_detail_label = QLabel("Select a transaction to view notes.")
        self._transaction_detail_label.setWordWrap(True)
        self._transaction_detail_label.setStyleSheet("color: #334155;")

        layout.addLayout(filter_layout)
        layout.addWidget(self._transaction_table)
        layout.addWidget(self._transaction_detail_label)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        """Refresh all tabs and dependent combo data."""
        self.refresh_cashiers()
        self.refresh_targets()
        self.refresh_transactions()

    def refresh_cashiers(self) -> None:
        """Reload cashier grid and all cashier selector combos."""
        self._cashiers = self.service.list_cashiers()
        self._cashier_table.setRowCount(len(self._cashiers))
        for row_index, cashier in enumerate(self._cashiers):
            role = self._format_role(cashier)
            last_login = (
                cashier.login_at.strftime("%Y-%m-%d %H:%M") if cashier.login_at else "-"
            )
            values = [
                str(cashier.no),
                cashier.user_name,
                cashier.name,
                cashier.last_name,
                role,
                "Yes" if cashier.is_active else "No",
                cashier.identity_number,
                last_login,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, cashier.id)
                self._cashier_table.setItem(row_index, col, item)
        self._cashier_table.resizeColumnsToContents()
        self._reload_cashier_combos()

    def refresh_targets(self) -> None:
        """Reload target grid with selected cashier filter."""
        cashier_filter_id = self._target_cashier_filter_combo.currentData()
        self._targets = self.service.list_performance_targets(cashier_id=cashier_filter_id)
        self._target_table.setRowCount(len(self._targets))
        for row_index, target in enumerate(self._targets):
            values = [
                target.cashier_name,
                target.target_period,
                target.target_start_date.isoformat(),
                target.target_end_date.isoformat(),
                self._format_amount(target.target_total_sales),
                str(target.target_transactions_count or 0),
                f"{target.current_achievement_percentage:.2f}",
                target.target_status,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, target.id)
                self._target_table.setItem(row_index, col, item)
        self._target_table.resizeColumnsToContents()

    def refresh_transactions(self) -> None:
        """Reload transaction metrics grid by selected cashier filter."""
        cashier_filter_id = self._transaction_cashier_filter_combo.currentData()
        self._transactions = self.service.list_transaction_metrics(
            cashier_id=cashier_filter_id,
            limit=1000,
        )
        self._transaction_table.setRowCount(len(self._transactions))
        for row_index, metric in enumerate(self._transactions):
            values = [
                metric.cashier_name,
                metric.transaction_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                metric.transaction_end_time.strftime("%Y-%m-%d %H:%M:%S")
                if metric.transaction_end_time
                else "-",
                f"{metric.total_transaction_time:.2f}"
                if metric.total_transaction_time is not None
                else "-",
                self._format_amount(metric.transaction_total_amount),
                str(metric.number_of_items),
                metric.payment_method_used or "-",
                f"{metric.transaction_efficiency_score:.2f}"
                if metric.transaction_efficiency_score is not None
                else "-",
                metric.transaction_complexity_level,
                "Yes" if metric.transaction_cancelled else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, metric.id)
                self._transaction_table.setItem(row_index, col, item)
        self._transaction_table.resizeColumnsToContents()
        self._transaction_detail_label.setText("Select a transaction to view notes.")

    def _reload_cashier_combos(self) -> None:
        """Sync cashier selectors used by target and transaction tabs."""
        combo_specs = [
            (self._target_cashier_filter_combo, True),
            (self._target_cashier_combo, False),
            (self._transaction_cashier_filter_combo, True),
        ]
        for combo, include_all in combo_specs:
            selected = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if include_all:
                combo.addItem("All", None)
            for cashier in self._cashiers:
                combo.addItem(
                    f"{cashier.no} - {cashier.name} {cashier.last_name}",
                    cashier.id,
                )
            index = combo.findData(selected)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _on_cashier_row_selected(self) -> None:
        selected_items = self._cashier_table.selectedItems()
        if not selected_items:
            return
        cashier_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._cashiers if x.id == cashier_id), None)
        if selected is None:
            return
        self._selected_cashier_id = selected.id
        self._cashier_no_input.setValue(int(selected.no))
        self._cashier_username_input.setText(selected.user_name)
        self._cashier_name_input.setText(selected.name)
        self._cashier_last_name_input.setText(selected.last_name)
        self._cashier_password_input.setText(selected.password)
        self._cashier_identity_input.setText(selected.identity_number)
        self._cashier_description_input.setText(selected.description)
        self._cashier_admin_checkbox.setChecked(selected.is_administrator)
        self._cashier_manager_checkbox.setChecked(selected.is_manager)
        self._cashier_active_checkbox.setChecked(selected.is_active)

    def _on_target_row_selected(self) -> None:
        selected_items = self._target_table.selectedItems()
        if not selected_items:
            return
        target_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._targets if x.id == target_id), None)
        if selected is None:
            return
        self._selected_target_id = selected.id
        self._target_cashier_combo.setCurrentIndex(
            self._target_cashier_combo.findData(selected.cashier_id)
        )
        self._target_period_combo.setCurrentText(selected.target_period)
        self._target_start_date_input.setDate(
            QDate(
                selected.target_start_date.year,
                selected.target_start_date.month,
                selected.target_start_date.day,
            )
        )
        self._target_end_date_input.setDate(
            QDate(
                selected.target_end_date.year,
                selected.target_end_date.month,
                selected.target_end_date.day,
            )
        )
        self._target_total_sales_input.setValue(float(selected.target_total_sales or 0))
        self._target_transactions_count_input.setValue(selected.target_transactions_count or 0)
        self._target_achievement_input.setValue(selected.current_achievement_percentage)
        self._target_status_combo.setCurrentText(selected.target_status)
        self._target_on_track_checkbox.setChecked(selected.is_on_track)
        self._target_description_input.setPlainText(selected.target_description)

    def _on_transaction_row_selected(self) -> None:
        selected_items = self._transaction_table.selectedItems()
        if not selected_items:
            self._transaction_detail_label.setText("Select a transaction to view notes.")
            return
        metric_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._transactions if x.id == metric_id), None)
        if selected is None:
            return
        note_text = selected.transaction_notes or "No notes provided."
        self._transaction_detail_label.setText(f"Transaction Notes: {note_text}")

    def _clear_cashier_editor(self) -> None:
        self._selected_cashier_id = None
        self._cashier_no_input.setValue(1)
        self._cashier_username_input.clear()
        self._cashier_name_input.clear()
        self._cashier_last_name_input.clear()
        self._cashier_password_input.clear()
        self._cashier_identity_input.clear()
        self._cashier_description_input.clear()
        self._cashier_admin_checkbox.setChecked(False)
        self._cashier_manager_checkbox.setChecked(False)
        self._cashier_active_checkbox.setChecked(True)
        self._cashier_table.clearSelection()

    def _save_cashier(self) -> None:
        payload = {
            "no": self._cashier_no_input.value(),
            "user_name": self._cashier_username_input.text(),
            "name": self._cashier_name_input.text(),
            "last_name": self._cashier_last_name_input.text(),
            "password": self._cashier_password_input.text(),
            "identity_number": self._cashier_identity_input.text(),
            "description": self._cashier_description_input.text(),
            "is_administrator": self._cashier_admin_checkbox.isChecked(),
            "is_manager": self._cashier_manager_checkbox.isChecked(),
            "is_active": self._cashier_active_checkbox.isChecked(),
        }
        result = self.service.save_cashier(
            payload=payload,
            cashier_id=self._selected_cashier_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_cashiers()
            self._clear_cashier_editor()

    def _delete_cashier(self) -> None:
        if not self._selected_cashier_id:
            self._set_status(False, "Please select a cashier record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Cashier",
            "Selected cashier will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_cashier(self._selected_cashier_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_cashier_editor()

    def _clear_target_editor(self) -> None:
        self._selected_target_id = None
        self._target_table.clearSelection()
        if self._target_cashier_combo.count() > 0:
            self._target_cashier_combo.setCurrentIndex(0)
        self._target_period_combo.setCurrentText("MONTHLY")
        self._target_start_date_input.setDate(QDate.currentDate())
        self._target_end_date_input.setDate(QDate.currentDate())
        self._target_total_sales_input.setValue(0)
        self._target_transactions_count_input.setValue(0)
        self._target_achievement_input.setValue(0)
        self._target_status_combo.setCurrentText("ACTIVE")
        self._target_on_track_checkbox.setChecked(True)
        self._target_description_input.clear()

    def _save_target(self) -> None:
        start_date = self._target_start_date_input.date().toPython()
        end_date = self._target_end_date_input.date().toPython()
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            self._set_status(False, "Start and end dates are required.")
            return

        payload = {
            "cashier_id": self._target_cashier_combo.currentData(),
            "target_period": self._target_period_combo.currentText(),
            "target_start_date": start_date,
            "target_end_date": end_date,
            "target_total_sales": self._target_total_sales_input.value(),
            "target_transactions_count": self._target_transactions_count_input.value(),
            "current_achievement_percentage": self._target_achievement_input.value(),
            "target_status": self._target_status_combo.currentText(),
            "is_on_track": self._target_on_track_checkbox.isChecked(),
            "target_description": self._target_description_input.toPlainText(),
        }
        result = self.service.save_performance_target(
            payload=payload,
            target_id=self._selected_target_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_targets()
            self._clear_target_editor()

    def _delete_target(self) -> None:
        if not self._selected_target_id:
            self._set_status(False, "Please select a performance target to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Performance Target",
            "Selected performance target will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_performance_target(self._selected_target_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_targets()
            self._clear_target_editor()

    def _set_status(self, success: bool, message: str) -> None:
        self._status_label.setStyleSheet("color: #166534;" if success else "color: #b91c1c;")
        self._status_label.setText(message)

    @staticmethod
    def _format_role(cashier: CashierView) -> str:
        roles: list[str] = []
        if cashier.is_administrator:
            roles.append("Admin")
        if cashier.is_manager:
            roles.append("Manager")
        return ", ".join(roles) if roles else "Cashier"

    @staticmethod
    def _format_amount(value: Decimal | None) -> str:
        amount = Decimal("0") if value is None else Decimal(str(value))
        return f"{amount:.2f}"
