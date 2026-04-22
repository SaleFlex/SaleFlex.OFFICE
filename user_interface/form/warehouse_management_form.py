"""
Warehouse management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.warehouse_management_service import (
    WarehouseAdjustmentView,
    WarehouseLocationView,
    WarehouseManagementService,
    WarehouseMovementView,
    WarehouseStockView,
    WarehouseView,
)
from settings.settings import Settings
from user_interface.form.warehouse_operations_form import WarehouseOperationsForm


class WarehouseManagementForm(QWidget):
    """Manage warehouse definition and operation tables."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.warehouse_service = WarehouseManagementService(store_code=bootstrap_context.store_id)
        self.setWindowTitle(f"{Settings().app_name} - Warehouse Management")
        self.setMinimumSize(1520, 960)

        self._warehouses: list[WarehouseView] = []
        self._locations: list[WarehouseLocationView] = []
        self._stocks: list[WarehouseStockView] = []
        self._movements: list[WarehouseMovementView] = []
        self._adjustments: list[WarehouseAdjustmentView] = []

        self._selected_warehouse_id: str | None = None
        self._selected_location_id: str | None = None
        self._selected_stock_id: str | None = None
        self._selected_movement_id: str | None = None
        self._selected_adjustment_id: str | None = None

        self._operations_form: WarehouseOperationsForm | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Warehouse Management Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_id}  |  Office: {self.bootstrap_context.office_id}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)
        open_operations_button = QPushButton("Open Warehouse Operations Window")
        open_operations_button.clicked.connect(self._open_operations_window)
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        action_row.addWidget(open_operations_button)
        action_row.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_warehouses_tab(), "Warehouses")
        self._tabs.addTab(self._build_locations_tab(), "Warehouse Locations")
        self._tabs.addTab(self._build_stock_tab(), "Warehouse Product Stock")
        self._tabs.addTab(self._build_movement_tab(), "Stock Movements")
        self._tabs.addTab(self._build_adjustment_tab(), "Stock Adjustments")
        self._tabs.addTab(self._build_operations_tab(), "Warehouse Operations")

        root = QVBoxLayout()
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)
        root.addWidget(header)
        root.addWidget(subtitle)
        root.addLayout(action_row)
        root.addWidget(self._status_label)
        root.addWidget(self._tabs)
        self.setLayout(root)

    def _build_warehouses_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        self._warehouse_table = QTableWidget(0, 8)
        self._warehouse_table.setHorizontalHeaderLabels(
            ["Code", "Name", "Type", "Store", "Active", "Receiving", "Shipping", "Manager"]
        )
        self._init_table(self._warehouse_table, self._on_warehouse_selected)

        editor = QGroupBox("Warehouse Editor")
        form = QFormLayout()
        self._warehouse_store_combo = QComboBox()
        self._warehouse_name_input = QLineEdit()
        self._warehouse_code_input = QLineEdit()
        self._warehouse_type_combo = QComboBox()
        self._warehouse_type_combo.addItems(
            ["MAIN", "BACKROOM", "SALES_FLOOR", "COLD_STORAGE", "SECURITY", "TEMPORARY"]
        )
        self._warehouse_description_input = QPlainTextEdit()
        self._warehouse_description_input.setMinimumHeight(60)
        self._warehouse_address_input = QLineEdit()
        self._warehouse_manager_name_input = QLineEdit()
        self._warehouse_contact_phone_input = QLineEdit()
        self._warehouse_contact_email_input = QLineEdit()
        self._warehouse_security_level_combo = QComboBox()
        self._warehouse_security_level_combo.addItems(["", "LOW", "MEDIUM", "HIGH"])
        self._warehouse_min_temperature_input = QLineEdit()
        self._warehouse_max_temperature_input = QLineEdit()
        self._warehouse_active_checkbox = QCheckBox("Active")
        self._warehouse_active_checkbox.setChecked(True)
        self._warehouse_receiving_checkbox = QCheckBox("Receiving Enabled")
        self._warehouse_receiving_checkbox.setChecked(True)
        self._warehouse_shipping_checkbox = QCheckBox("Shipping Enabled")
        self._warehouse_shipping_checkbox.setChecked(True)
        self._warehouse_cycle_count_checkbox = QCheckBox("Cycle Count Enabled")
        self._warehouse_cycle_count_checkbox.setChecked(True)
        self._warehouse_temperature_checkbox = QCheckBox("Temperature Controlled")
        self._warehouse_security_checkbox = QCheckBox("Requires Security Access")
        form.addRow("Store", self._warehouse_store_combo)
        form.addRow("Name", self._warehouse_name_input)
        form.addRow("Code", self._warehouse_code_input)
        form.addRow("Warehouse Type", self._warehouse_type_combo)
        form.addRow("Description", self._warehouse_description_input)
        form.addRow("Address", self._warehouse_address_input)
        form.addRow("Manager Name", self._warehouse_manager_name_input)
        form.addRow("Contact Phone", self._warehouse_contact_phone_input)
        form.addRow("Contact Email", self._warehouse_contact_email_input)
        form.addRow("Security Level", self._warehouse_security_level_combo)
        form.addRow("Min Temperature", self._warehouse_min_temperature_input)
        form.addRow("Max Temperature", self._warehouse_max_temperature_input)
        form.addRow(self._warehouse_active_checkbox)
        form.addRow(self._warehouse_receiving_checkbox)
        form.addRow(self._warehouse_shipping_checkbox)
        form.addRow(self._warehouse_cycle_count_checkbox)
        form.addRow(self._warehouse_temperature_checkbox)
        form.addRow(self._warehouse_security_checkbox)
        editor.setLayout(
            self._editor_layout(
                form, self._save_warehouse, self._delete_warehouse, self._clear_warehouse_editor, self.refresh_warehouses
            )
        )

        splitter.addWidget(self._wrap(self._warehouse_table))
        splitter.addWidget(editor)
        splitter.setSizes([980, 470])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_locations_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._location_warehouse_filter_combo = QComboBox()
        self._location_warehouse_filter_combo.currentIndexChanged.connect(self.refresh_locations)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_locations)
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._location_warehouse_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._location_table = QTableWidget(0, 10)
        self._location_table.setHorizontalHeaderLabels(
            ["Warehouse", "Code", "Name", "Type", "Level", "Parent", "Active", "Blocked", "Pick", "Replenish"]
        )
        self._init_table(self._location_table, self._on_location_selected)
        left_layout.addWidget(self._location_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Warehouse Location Editor")
        form = QFormLayout()
        self._location_warehouse_combo = QComboBox()
        self._location_warehouse_combo.currentIndexChanged.connect(self._reload_parent_location_combo)
        self._location_parent_combo = QComboBox()
        self._location_name_input = QLineEdit()
        self._location_code_input = QLineEdit()
        self._location_type_combo = QComboBox()
        self._location_type_combo.addItems(
            ["AISLE", "SHELF", "RACK", "ZONE", "BAY", "LEVEL", "DISPLAY", "COUNTER", "GONDOLA"]
        )
        self._location_level_input = QSpinBox()
        self._location_level_input.setRange(1, 10)
        self._location_description_input = QPlainTextEdit()
        self._location_description_input.setMinimumHeight(60)
        self._location_pick_sequence_input = QSpinBox()
        self._location_pick_sequence_input.setRange(0, 100000)
        self._location_replenishment_priority_input = QSpinBox()
        self._location_replenishment_priority_input.setRange(0, 100000)
        self._location_block_reason_input = QLineEdit()
        self._location_active_checkbox = QCheckBox("Active")
        self._location_active_checkbox.setChecked(True)
        self._location_blocked_checkbox = QCheckBox("Blocked")
        self._location_pick_checkbox = QCheckBox("Pick Location")
        self._location_pick_checkbox.setChecked(True)
        self._location_replenishment_checkbox = QCheckBox("Replenishment Location")
        self._location_replenishment_checkbox.setChecked(True)
        form.addRow("Warehouse", self._location_warehouse_combo)
        form.addRow("Parent Location", self._location_parent_combo)
        form.addRow("Name", self._location_name_input)
        form.addRow("Code", self._location_code_input)
        form.addRow("Location Type", self._location_type_combo)
        form.addRow("Level", self._location_level_input)
        form.addRow("Description", self._location_description_input)
        form.addRow("Pick Sequence", self._location_pick_sequence_input)
        form.addRow("Replenishment Priority", self._location_replenishment_priority_input)
        form.addRow("Block Reason", self._location_block_reason_input)
        form.addRow(self._location_active_checkbox)
        form.addRow(self._location_blocked_checkbox)
        form.addRow(self._location_pick_checkbox)
        form.addRow(self._location_replenishment_checkbox)
        editor.setLayout(
            self._editor_layout(
                form, self._save_location, self._delete_location, self._clear_location_editor, self.refresh_locations
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 470])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_stock_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._stock_warehouse_filter_combo = QComboBox()
        self._stock_warehouse_filter_combo.currentIndexChanged.connect(self._on_stock_filter_warehouse_changed)
        self._stock_location_filter_combo = QComboBox()
        self._stock_location_filter_combo.currentIndexChanged.connect(self.refresh_stocks)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_stocks)
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._stock_warehouse_filter_combo)
        filter_layout.addWidget(QLabel("Location"))
        filter_layout.addWidget(self._stock_location_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._stock_table = QTableWidget(0, 13)
        self._stock_table.setHorizontalHeaderLabels(
            ["Product", "Location", "Qty", "Available", "Reserved", "Min", "Max", "Reorder", "Lot", "Expiry", "Low", "Active", "Blocked"]
        )
        self._init_table(self._stock_table, self._on_stock_selected)
        left_layout.addWidget(self._stock_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Warehouse Product Stock Editor")
        form = QFormLayout()
        self._stock_product_combo = QComboBox()
        self._stock_location_combo = QComboBox()
        self._stock_quantity_input = QSpinBox()
        self._stock_quantity_input.setRange(-1_000_000, 1_000_000)
        self._stock_available_quantity_input = QSpinBox()
        self._stock_available_quantity_input.setRange(-1_000_000, 1_000_000)
        self._stock_reserved_quantity_input = QSpinBox()
        self._stock_reserved_quantity_input.setRange(0, 1_000_000)
        self._stock_min_level_input = QSpinBox()
        self._stock_min_level_input.setRange(0, 1_000_000)
        self._stock_max_level_input = QSpinBox()
        self._stock_max_level_input.setRange(0, 1_000_000)
        self._stock_reorder_point_input = QSpinBox()
        self._stock_reorder_point_input.setRange(0, 1_000_000)
        self._stock_reorder_quantity_input = QSpinBox()
        self._stock_reorder_quantity_input.setRange(0, 1_000_000)
        self._stock_lot_number_input = QLineEdit()
        self._stock_expiration_date_input = QLineEdit()
        self._stock_expiration_date_input.setPlaceholderText("YYYY-MM-DD")
        self._stock_block_reason_input = QLineEdit()
        self._stock_low_stock_checkbox = QCheckBox("Low Stock Alert")
        self._stock_overstock_checkbox = QCheckBox("Overstock Alert")
        self._stock_expiry_checkbox = QCheckBox("Expiry Alert")
        self._stock_active_checkbox = QCheckBox("Active")
        self._stock_active_checkbox.setChecked(True)
        self._stock_discontinued_checkbox = QCheckBox("Discontinued")
        self._stock_blocked_checkbox = QCheckBox("Blocked")
        form.addRow("Product", self._stock_product_combo)
        form.addRow("Warehouse Location", self._stock_location_combo)
        form.addRow("Quantity", self._stock_quantity_input)
        form.addRow("Available Quantity", self._stock_available_quantity_input)
        form.addRow("Reserved Quantity", self._stock_reserved_quantity_input)
        form.addRow("Min Stock Level", self._stock_min_level_input)
        form.addRow("Max Stock Level", self._stock_max_level_input)
        form.addRow("Reorder Point", self._stock_reorder_point_input)
        form.addRow("Reorder Quantity", self._stock_reorder_quantity_input)
        form.addRow("Lot Number", self._stock_lot_number_input)
        form.addRow("Expiration Date", self._stock_expiration_date_input)
        form.addRow("Block Reason", self._stock_block_reason_input)
        form.addRow(self._stock_low_stock_checkbox)
        form.addRow(self._stock_overstock_checkbox)
        form.addRow(self._stock_expiry_checkbox)
        form.addRow(self._stock_active_checkbox)
        form.addRow(self._stock_discontinued_checkbox)
        form.addRow(self._stock_blocked_checkbox)
        editor.setLayout(
            self._editor_layout(
                form, self._save_stock, self._delete_stock, self._clear_stock_editor, self.refresh_stocks
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 470])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_movement_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._movement_warehouse_filter_combo = QComboBox()
        self._movement_warehouse_filter_combo.currentIndexChanged.connect(self.refresh_movements)
        self._movement_status_filter_combo = QComboBox()
        self._movement_status_filter_combo.addItem("All", None)
        for status in ("PENDING", "COMPLETED", "CANCELLED", "REVERSED"):
            self._movement_status_filter_combo.addItem(status, status)
        self._movement_status_filter_combo.currentIndexChanged.connect(self.refresh_movements)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_movements)
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._movement_warehouse_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._movement_status_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._movement_table = QTableWidget(0, 11)
        self._movement_table.setHorizontalHeaderLabels(
            ["No", "Type", "Subtype", "Status", "Warehouse", "Product", "From", "To", "Qty", "Date", "Approved"]
        )
        self._init_table(self._movement_table, self._on_movement_selected)
        left_layout.addWidget(self._movement_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Stock Movement Editor")
        form = QFormLayout()
        self._movement_number_input = QLineEdit()
        self._movement_type_combo = QComboBox()
        self._movement_type_combo.addItems(["RECEIPT", "SALE", "TRANSFER", "ADJUSTMENT", "RETURN", "LOSS", "DAMAGE"])
        self._movement_subtype_input = QLineEdit()
        self._movement_status_combo = QComboBox()
        self._movement_status_combo.addItems(["PENDING", "COMPLETED", "CANCELLED", "REVERSED"])
        self._movement_product_combo = QComboBox()
        self._movement_from_location_combo = QComboBox()
        self._movement_to_location_combo = QComboBox()
        self._movement_quantity_input = QSpinBox()
        self._movement_quantity_input.setRange(-1_000_000, 1_000_000)
        self._movement_date_input = QLineEdit()
        self._movement_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._movement_reference_input = QLineEdit()
        self._movement_reason_input = QLineEdit()
        self._movement_description_input = QPlainTextEdit()
        self._movement_description_input.setMinimumHeight(60)
        self._movement_approved_by_combo = QComboBox()
        self._movement_approved_checkbox = QCheckBox("Approved")
        form.addRow("Movement Number", self._movement_number_input)
        form.addRow("Movement Type", self._movement_type_combo)
        form.addRow("Movement Subtype", self._movement_subtype_input)
        form.addRow("Status", self._movement_status_combo)
        form.addRow("Product", self._movement_product_combo)
        form.addRow("From Location", self._movement_from_location_combo)
        form.addRow("To Location", self._movement_to_location_combo)
        form.addRow("Quantity", self._movement_quantity_input)
        form.addRow("Movement Date", self._movement_date_input)
        form.addRow("Reference Document", self._movement_reference_input)
        form.addRow("Reason", self._movement_reason_input)
        form.addRow("Description", self._movement_description_input)
        form.addRow("Approved By", self._movement_approved_by_combo)
        form.addRow(self._movement_approved_checkbox)
        editor.setLayout(
            self._editor_layout(
                form, self._save_movement, self._delete_movement, self._clear_movement_editor, self.refresh_movements
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 470])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_adjustment_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._adjustment_warehouse_filter_combo = QComboBox()
        self._adjustment_warehouse_filter_combo.currentIndexChanged.connect(self.refresh_adjustments)
        self._adjustment_status_filter_combo = QComboBox()
        self._adjustment_status_filter_combo.addItem("All", None)
        for status in ("PENDING", "APPROVED", "REJECTED", "PROCESSED"):
            self._adjustment_status_filter_combo.addItem(status, status)
        self._adjustment_status_filter_combo.currentIndexChanged.connect(self.refresh_adjustments)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_adjustments)
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._adjustment_warehouse_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._adjustment_status_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._adjustment_table = QTableWidget(0, 11)
        self._adjustment_table.setHorizontalHeaderLabels(
            ["No", "Type", "Reason", "Status", "Warehouse", "Product", "Location", "System", "Counted", "Diff", "Date"]
        )
        self._init_table(self._adjustment_table, self._on_adjustment_selected)
        left_layout.addWidget(self._adjustment_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Stock Adjustment Editor")
        form = QFormLayout()
        self._adjustment_number_input = QLineEdit()
        self._adjustment_type_combo = QComboBox()
        self._adjustment_type_combo.addItems(
            ["CYCLE_COUNT", "PHYSICAL_COUNT", "LOSS", "DAMAGE", "FOUND", "WRITE_OFF"]
        )
        self._adjustment_reason_input = QLineEdit()
        self._adjustment_status_combo = QComboBox()
        self._adjustment_status_combo.addItems(["PENDING", "APPROVED", "REJECTED", "PROCESSED"])
        self._adjustment_product_combo = QComboBox()
        self._adjustment_location_combo = QComboBox()
        self._adjustment_system_quantity_input = QSpinBox()
        self._adjustment_system_quantity_input.setRange(-1_000_000, 1_000_000)
        self._adjustment_counted_quantity_input = QSpinBox()
        self._adjustment_counted_quantity_input.setRange(-1_000_000, 1_000_000)
        self._adjustment_difference_input = QSpinBox()
        self._adjustment_difference_input.setRange(-1_000_000, 1_000_000)
        self._adjustment_date_input = QLineEdit()
        self._adjustment_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._adjustment_approved_by_combo = QComboBox()
        self._adjustment_counter_notes_input = QPlainTextEdit()
        self._adjustment_counter_notes_input.setMinimumHeight(60)
        self._adjustment_supervisor_notes_input = QPlainTextEdit()
        self._adjustment_supervisor_notes_input.setMinimumHeight(60)
        self._adjustment_approved_checkbox = QCheckBox("Approved")
        form.addRow("Adjustment Number", self._adjustment_number_input)
        form.addRow("Adjustment Type", self._adjustment_type_combo)
        form.addRow("Adjustment Reason", self._adjustment_reason_input)
        form.addRow("Status", self._adjustment_status_combo)
        form.addRow("Product", self._adjustment_product_combo)
        form.addRow("Warehouse Location", self._adjustment_location_combo)
        form.addRow("System Quantity", self._adjustment_system_quantity_input)
        form.addRow("Counted Quantity", self._adjustment_counted_quantity_input)
        form.addRow("Quantity Difference", self._adjustment_difference_input)
        form.addRow("Count Date", self._adjustment_date_input)
        form.addRow("Approved By", self._adjustment_approved_by_combo)
        form.addRow("Counter Notes", self._adjustment_counter_notes_input)
        form.addRow("Supervisor Notes", self._adjustment_supervisor_notes_input)
        form.addRow(self._adjustment_approved_checkbox)
        editor.setLayout(
            self._editor_layout(
                form,
                self._save_adjustment,
                self._delete_adjustment,
                self._clear_adjustment_editor,
                self.refresh_adjustments,
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 470])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_operations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._operations_warehouse_filter_combo = QComboBox()
        self._operations_warehouse_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        self._operations_active_filter_combo = QComboBox()
        self._operations_active_filter_combo.addItem("All", None)
        self._operations_active_filter_combo.addItem("Active Only", True)
        self._operations_active_filter_combo.addItem("Inactive Only", False)
        self._operations_active_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_operations)
        open_window_button = QPushButton("Open Operations Window")
        open_window_button.clicked.connect(self._open_operations_window)
        filter_layout.addWidget(QLabel("Warehouse"))
        filter_layout.addWidget(self._operations_warehouse_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._operations_active_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        filter_layout.addWidget(open_window_button)
        layout.addLayout(filter_layout)
        self._operations_table = QTableWidget(0, 11)
        self._operations_table.setHorizontalHeaderLabels(
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
        self._init_table(self._operations_table, None)
        layout.addWidget(self._operations_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self._reload_lookup_combos()
        self.refresh_warehouses()
        self.refresh_locations()
        self.refresh_stocks()
        self.refresh_movements()
        self.refresh_adjustments()
        self.refresh_operations()

    def refresh_warehouses(self) -> None:
        self._warehouses = self.warehouse_service.list_warehouses()
        self._warehouse_table.setRowCount(len(self._warehouses))
        for row_index, row in enumerate(self._warehouses):
            values = [
                row.code,
                row.name,
                row.warehouse_type,
                row.store_label,
                "Yes" if row.is_active else "No",
                "Yes" if row.is_receiving_enabled else "No",
                "Yes" if row.is_shipping_enabled else "No",
                row.manager_name,
            ]
            self._set_row(self._warehouse_table, row_index, values, row.id)
        self._warehouse_table.resizeColumnsToContents()
        self._reload_warehouse_combos()

    def refresh_locations(self) -> None:
        self._locations = self.warehouse_service.list_warehouse_locations(
            warehouse_id=self._location_warehouse_filter_combo.currentData()
        )
        self._location_table.setRowCount(len(self._locations))
        for row_index, row in enumerate(self._locations):
            values = [
                row.warehouse_label,
                row.code,
                row.name,
                row.location_type,
                str(row.level),
                row.parent_location_label,
                "Yes" if row.is_active else "No",
                "Yes" if row.is_blocked else "No",
                "Yes" if row.is_pick_location else "No",
                "Yes" if row.is_replenishment_location else "No",
            ]
            self._set_row(self._location_table, row_index, values, row.id)
        self._location_table.resizeColumnsToContents()
        self._reload_parent_location_combo()
        self._reload_location_combos()

    def refresh_stocks(self) -> None:
        self._stocks = self.warehouse_service.list_warehouse_product_stocks(
            warehouse_id=self._stock_warehouse_filter_combo.currentData(),
            location_id=self._stock_location_filter_combo.currentData(),
        )
        self._stock_table.setRowCount(len(self._stocks))
        for row_index, row in enumerate(self._stocks):
            values = [
                row.product_label,
                row.location_label,
                str(row.quantity),
                str(row.available_quantity),
                str(row.reserved_quantity),
                str(row.min_stock_level),
                str(row.max_stock_level),
                str(row.reorder_point),
                row.lot_number,
                row.expiration_date.isoformat() if row.expiration_date else "",
                "Yes" if row.low_stock_alert else "No",
                "Yes" if row.is_active else "No",
                "Yes" if row.is_blocked else "No",
            ]
            self._set_row(self._stock_table, row_index, values, row.id)
        self._stock_table.resizeColumnsToContents()

    def refresh_movements(self) -> None:
        self._movements = self.warehouse_service.list_warehouse_stock_movements(
            warehouse_id=self._movement_warehouse_filter_combo.currentData(),
            status=self._movement_status_filter_combo.currentData(),
        )
        self._movement_table.setRowCount(len(self._movements))
        for row_index, row in enumerate(self._movements):
            values = [
                row.movement_number,
                row.movement_type,
                row.movement_subtype,
                row.status,
                row.warehouse_label,
                row.product_label,
                row.from_location_label,
                row.to_location_label,
                str(row.quantity),
                row.movement_date.isoformat(sep=" ") if row.movement_date else "",
                "Yes" if row.is_approved else "No",
            ]
            self._set_row(self._movement_table, row_index, values, row.id)
        self._movement_table.resizeColumnsToContents()

    def refresh_adjustments(self) -> None:
        self._adjustments = self.warehouse_service.list_warehouse_stock_adjustments(
            warehouse_id=self._adjustment_warehouse_filter_combo.currentData(),
            status=self._adjustment_status_filter_combo.currentData(),
        )
        self._adjustment_table.setRowCount(len(self._adjustments))
        for row_index, row in enumerate(self._adjustments):
            values = [
                row.adjustment_number,
                row.adjustment_type,
                row.adjustment_reason,
                row.status,
                row.warehouse_label,
                row.product_label,
                row.location_label,
                str(row.system_quantity),
                str(row.counted_quantity),
                str(row.quantity_difference),
                row.count_date.isoformat(sep=" ") if row.count_date else "",
            ]
            self._set_row(self._adjustment_table, row_index, values, row.id)
        self._adjustment_table.resizeColumnsToContents()

    def refresh_operations(self) -> None:
        rows = self.warehouse_service.list_warehouse_operations(
            warehouse_id=self._operations_warehouse_filter_combo.currentData(),
            active_only=self._operations_active_filter_combo.currentData(),
        )
        self._operations_table.setRowCount(len(rows))
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
                row.last_movement_date.isoformat(sep=" ") if row.last_movement_date else "",
            ]
            self._set_row(self._operations_table, row_index, values, row.warehouse_id)
        self._operations_table.resizeColumnsToContents()

    def _save_warehouse(self) -> None:
        payload = {
            "store_id": self._warehouse_store_combo.currentData(),
            "name": self._warehouse_name_input.text(),
            "code": self._warehouse_code_input.text(),
            "warehouse_type": self._warehouse_type_combo.currentText(),
            "description": self._warehouse_description_input.toPlainText(),
            "address": self._warehouse_address_input.text(),
            "manager_name": self._warehouse_manager_name_input.text(),
            "contact_phone": self._warehouse_contact_phone_input.text(),
            "contact_email": self._warehouse_contact_email_input.text(),
            "security_level": self._warehouse_security_level_combo.currentText(),
            "min_temperature": self._warehouse_min_temperature_input.text(),
            "max_temperature": self._warehouse_max_temperature_input.text(),
            "is_active": self._warehouse_active_checkbox.isChecked(),
            "is_receiving_enabled": self._warehouse_receiving_checkbox.isChecked(),
            "is_shipping_enabled": self._warehouse_shipping_checkbox.isChecked(),
            "is_cycle_count_enabled": self._warehouse_cycle_count_checkbox.isChecked(),
            "temperature_controlled": self._warehouse_temperature_checkbox.isChecked(),
            "requires_security_access": self._warehouse_security_checkbox.isChecked(),
        }
        result = self.warehouse_service.save_warehouse(payload=payload, warehouse_id=self._selected_warehouse_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_warehouse_editor()

    def _save_location(self) -> None:
        payload = {
            "warehouse_id": self._location_warehouse_combo.currentData(),
            "parent_location_id": self._location_parent_combo.currentData(),
            "name": self._location_name_input.text(),
            "code": self._location_code_input.text(),
            "location_type": self._location_type_combo.currentText(),
            "level": self._location_level_input.value(),
            "description": self._location_description_input.toPlainText(),
            "pick_sequence": self._location_pick_sequence_input.value(),
            "replenishment_priority": self._location_replenishment_priority_input.value(),
            "block_reason": self._location_block_reason_input.text(),
            "is_active": self._location_active_checkbox.isChecked(),
            "is_blocked": self._location_blocked_checkbox.isChecked(),
            "is_pick_location": self._location_pick_checkbox.isChecked(),
            "is_replenishment_location": self._location_replenishment_checkbox.isChecked(),
        }
        result = self.warehouse_service.save_warehouse_location(payload=payload, location_id=self._selected_location_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_location_editor()

    def _save_stock(self) -> None:
        payload = {
            "product_id": self._stock_product_combo.currentData(),
            "warehouse_location_id": self._stock_location_combo.currentData(),
            "quantity": self._stock_quantity_input.value(),
            "available_quantity": self._stock_available_quantity_input.value(),
            "reserved_quantity": self._stock_reserved_quantity_input.value(),
            "min_stock_level": self._stock_min_level_input.value(),
            "max_stock_level": self._stock_max_level_input.value(),
            "reorder_point": self._stock_reorder_point_input.value(),
            "reorder_quantity": self._stock_reorder_quantity_input.value(),
            "lot_number": self._stock_lot_number_input.text(),
            "expiration_date": self._stock_expiration_date_input.text(),
            "block_reason": self._stock_block_reason_input.text(),
            "low_stock_alert": self._stock_low_stock_checkbox.isChecked(),
            "overstock_alert": self._stock_overstock_checkbox.isChecked(),
            "expiry_alert": self._stock_expiry_checkbox.isChecked(),
            "is_active": self._stock_active_checkbox.isChecked(),
            "is_discontinued": self._stock_discontinued_checkbox.isChecked(),
            "is_blocked": self._stock_blocked_checkbox.isChecked(),
        }
        result = self.warehouse_service.save_warehouse_product_stock(payload=payload, stock_id=self._selected_stock_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_stocks()
            self._clear_stock_editor()

    def _save_movement(self) -> None:
        payload = {
            "movement_number": self._movement_number_input.text(),
            "movement_type": self._movement_type_combo.currentText(),
            "movement_subtype": self._movement_subtype_input.text(),
            "status": self._movement_status_combo.currentText(),
            "product_id": self._movement_product_combo.currentData(),
            "warehouse_location_from": self._movement_from_location_combo.currentData(),
            "warehouse_location_to": self._movement_to_location_combo.currentData(),
            "quantity": self._movement_quantity_input.value(),
            "movement_date": self._movement_date_input.text(),
            "reference_document": self._movement_reference_input.text(),
            "reason": self._movement_reason_input.text(),
            "description": self._movement_description_input.toPlainText(),
            "approved_by": self._movement_approved_by_combo.currentData(),
            "is_approved": self._movement_approved_checkbox.isChecked(),
        }
        result = self.warehouse_service.save_warehouse_stock_movement(
            payload=payload,
            movement_id=self._selected_movement_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_movements()
            self._clear_movement_editor()

    def _save_adjustment(self) -> None:
        payload = {
            "adjustment_number": self._adjustment_number_input.text(),
            "adjustment_type": self._adjustment_type_combo.currentText(),
            "adjustment_reason": self._adjustment_reason_input.text(),
            "status": self._adjustment_status_combo.currentText(),
            "product_id": self._adjustment_product_combo.currentData(),
            "warehouse_location_id": self._adjustment_location_combo.currentData(),
            "system_quantity": self._adjustment_system_quantity_input.value(),
            "counted_quantity": self._adjustment_counted_quantity_input.value(),
            "quantity_difference": self._adjustment_difference_input.value(),
            "count_date": self._adjustment_date_input.text(),
            "approved_by": self._adjustment_approved_by_combo.currentData(),
            "is_approved": self._adjustment_approved_checkbox.isChecked(),
            "counter_notes": self._adjustment_counter_notes_input.toPlainText(),
            "supervisor_notes": self._adjustment_supervisor_notes_input.toPlainText(),
        }
        result = self.warehouse_service.save_warehouse_stock_adjustment(
            payload=payload,
            adjustment_id=self._selected_adjustment_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_adjustments()
            self._clear_adjustment_editor()

    def _delete_warehouse(self) -> None:
        self._delete_record(
            selected_id=self._selected_warehouse_id,
            title="Delete Warehouse",
            question="Selected warehouse will be soft deleted. Continue?",
            deleter=self.warehouse_service.delete_warehouse,
            refresh=self.refresh_warehouses,
            clear=self._clear_warehouse_editor,
        )

    def _delete_location(self) -> None:
        self._delete_record(
            selected_id=self._selected_location_id,
            title="Delete Warehouse Location",
            question="Selected warehouse location will be soft deleted. Continue?",
            deleter=self.warehouse_service.delete_warehouse_location,
            refresh=self.refresh_locations,
            clear=self._clear_location_editor,
        )

    def _delete_stock(self) -> None:
        self._delete_record(
            selected_id=self._selected_stock_id,
            title="Delete Warehouse Stock",
            question="Selected warehouse stock will be soft deleted. Continue?",
            deleter=self.warehouse_service.delete_warehouse_product_stock,
            refresh=self.refresh_stocks,
            clear=self._clear_stock_editor,
        )

    def _delete_movement(self) -> None:
        self._delete_record(
            selected_id=self._selected_movement_id,
            title="Delete Stock Movement",
            question="Selected stock movement will be soft deleted. Continue?",
            deleter=self.warehouse_service.delete_warehouse_stock_movement,
            refresh=self.refresh_movements,
            clear=self._clear_movement_editor,
        )

    def _delete_adjustment(self) -> None:
        self._delete_record(
            selected_id=self._selected_adjustment_id,
            title="Delete Stock Adjustment",
            question="Selected stock adjustment will be soft deleted. Continue?",
            deleter=self.warehouse_service.delete_warehouse_stock_adjustment,
            refresh=self.refresh_adjustments,
            clear=self._clear_adjustment_editor,
        )

    def _on_warehouse_selected(self) -> None:
        selected = self._selected_row(self._warehouse_table, self._warehouses)
        if selected is None:
            return
        self._selected_warehouse_id = selected.id
        self._warehouse_store_combo.setCurrentIndex(self._warehouse_store_combo.findData(selected.store_id))
        self._warehouse_name_input.setText(selected.name)
        self._warehouse_code_input.setText(selected.code)
        self._warehouse_type_combo.setCurrentText(selected.warehouse_type)
        self._warehouse_description_input.setPlainText(selected.description)
        self._warehouse_address_input.setText(selected.address)
        self._warehouse_manager_name_input.setText(selected.manager_name)
        self._warehouse_contact_phone_input.setText(selected.contact_phone)
        self._warehouse_contact_email_input.setText(selected.contact_email)
        self._warehouse_security_level_combo.setCurrentText(selected.security_level)
        self._warehouse_min_temperature_input.setText(
            "" if selected.min_temperature is None else str(selected.min_temperature)
        )
        self._warehouse_max_temperature_input.setText(
            "" if selected.max_temperature is None else str(selected.max_temperature)
        )
        self._warehouse_active_checkbox.setChecked(selected.is_active)
        self._warehouse_receiving_checkbox.setChecked(selected.is_receiving_enabled)
        self._warehouse_shipping_checkbox.setChecked(selected.is_shipping_enabled)
        self._warehouse_cycle_count_checkbox.setChecked(selected.is_cycle_count_enabled)
        self._warehouse_temperature_checkbox.setChecked(selected.temperature_controlled)
        self._warehouse_security_checkbox.setChecked(selected.requires_security_access)

    def _on_location_selected(self) -> None:
        selected = self._selected_row(self._location_table, self._locations)
        if selected is None:
            return
        self._selected_location_id = selected.id
        self._location_warehouse_combo.setCurrentIndex(self._location_warehouse_combo.findData(selected.warehouse_id))
        self._reload_parent_location_combo()
        self._location_parent_combo.setCurrentIndex(
            self._location_parent_combo.findData(selected.parent_location_id)
        )
        self._location_name_input.setText(selected.name)
        self._location_code_input.setText(selected.code)
        self._location_type_combo.setCurrentText(selected.location_type)
        self._location_level_input.setValue(selected.level)
        self._location_block_reason_input.setText(selected.block_reason)
        self._location_pick_sequence_input.setValue(selected.pick_sequence or 0)
        self._location_replenishment_priority_input.setValue(selected.replenishment_priority or 0)
        self._location_active_checkbox.setChecked(selected.is_active)
        self._location_blocked_checkbox.setChecked(selected.is_blocked)
        self._location_pick_checkbox.setChecked(selected.is_pick_location)
        self._location_replenishment_checkbox.setChecked(selected.is_replenishment_location)

    def _on_stock_selected(self) -> None:
        selected = self._selected_row(self._stock_table, self._stocks)
        if selected is None:
            return
        self._selected_stock_id = selected.id
        self._stock_product_combo.setCurrentIndex(self._stock_product_combo.findData(selected.product_id))
        self._stock_location_combo.setCurrentIndex(self._stock_location_combo.findData(selected.location_id))
        self._stock_quantity_input.setValue(selected.quantity)
        self._stock_available_quantity_input.setValue(selected.available_quantity)
        self._stock_reserved_quantity_input.setValue(selected.reserved_quantity)
        self._stock_min_level_input.setValue(selected.min_stock_level)
        self._stock_max_level_input.setValue(selected.max_stock_level)
        self._stock_reorder_point_input.setValue(selected.reorder_point)
        self._stock_reorder_quantity_input.setValue(selected.reorder_quantity)
        self._stock_lot_number_input.setText(selected.lot_number)
        self._stock_expiration_date_input.setText(selected.expiration_date.isoformat() if selected.expiration_date else "")
        self._stock_low_stock_checkbox.setChecked(selected.low_stock_alert)
        self._stock_overstock_checkbox.setChecked(selected.overstock_alert)
        self._stock_expiry_checkbox.setChecked(selected.expiry_alert)
        self._stock_active_checkbox.setChecked(selected.is_active)
        self._stock_discontinued_checkbox.setChecked(selected.is_discontinued)
        self._stock_blocked_checkbox.setChecked(selected.is_blocked)
        self._stock_block_reason_input.setText(selected.block_reason)

    def _on_movement_selected(self) -> None:
        selected = self._selected_row(self._movement_table, self._movements)
        if selected is None:
            return
        self._selected_movement_id = selected.id
        self._movement_number_input.setText(selected.movement_number)
        self._movement_type_combo.setCurrentText(selected.movement_type)
        self._movement_subtype_input.setText(selected.movement_subtype)
        self._movement_status_combo.setCurrentText(selected.status)
        self._movement_product_combo.setCurrentIndex(self._movement_product_combo.findData(selected.product_id))
        self._movement_from_location_combo.setCurrentIndex(
            self._movement_from_location_combo.findData(selected.from_location_id)
        )
        self._movement_to_location_combo.setCurrentIndex(self._movement_to_location_combo.findData(selected.to_location_id))
        self._movement_quantity_input.setValue(selected.quantity)
        self._movement_date_input.setText(
            selected.movement_date.strftime("%Y-%m-%d %H:%M") if selected.movement_date else ""
        )
        self._movement_reference_input.setText(selected.reference_document)
        self._movement_reason_input.setText(selected.reason)
        self._movement_approved_checkbox.setChecked(selected.is_approved)
        self._movement_approved_by_combo.setCurrentIndex(
            self._movement_approved_by_combo.findData(selected.approved_by_id)
        )

    def _on_adjustment_selected(self) -> None:
        selected = self._selected_row(self._adjustment_table, self._adjustments)
        if selected is None:
            return
        self._selected_adjustment_id = selected.id
        self._adjustment_number_input.setText(selected.adjustment_number)
        self._adjustment_type_combo.setCurrentText(selected.adjustment_type)
        self._adjustment_reason_input.setText(selected.adjustment_reason)
        self._adjustment_status_combo.setCurrentText(selected.status)
        self._adjustment_product_combo.setCurrentIndex(self._adjustment_product_combo.findData(selected.product_id))
        self._adjustment_location_combo.setCurrentIndex(self._adjustment_location_combo.findData(selected.location_id))
        self._adjustment_system_quantity_input.setValue(selected.system_quantity)
        self._adjustment_counted_quantity_input.setValue(selected.counted_quantity)
        self._adjustment_difference_input.setValue(selected.quantity_difference)
        self._adjustment_date_input.setText(selected.count_date.strftime("%Y-%m-%d %H:%M") if selected.count_date else "")
        self._adjustment_approved_checkbox.setChecked(selected.is_approved)
        self._adjustment_approved_by_combo.setCurrentIndex(
            self._adjustment_approved_by_combo.findData(selected.approved_by_id)
        )

    def _reload_lookup_combos(self) -> None:
        store_items = [(item.id, item.label) for item in self.warehouse_service.list_store_lookups()]
        warehouse_items = [(item.id, item.label) for item in self.warehouse_service.list_warehouse_lookups()]
        product_items = [(item.id, item.label) for item in self.warehouse_service.list_product_lookups()]
        location_items = [(item.id, item.label) for item in self.warehouse_service.list_warehouse_location_lookups()]
        cashier_items = [(item.id, item.label) for item in self.warehouse_service.list_cashier_lookups()]

        self._reload_combo(self._warehouse_store_combo, store_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._location_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._location_warehouse_combo, warehouse_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._stock_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._movement_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._adjustment_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._operations_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._stock_product_combo, product_items, include_empty=False, empty_label="")
        self._reload_combo(self._movement_product_combo, product_items, include_empty=False, empty_label="")
        self._reload_combo(self._adjustment_product_combo, product_items, include_empty=False, empty_label="")
        self._reload_combo(self._stock_location_combo, location_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._stock_location_filter_combo, location_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._movement_from_location_combo, location_items, include_empty=True, empty_label="None")
        self._reload_combo(self._movement_to_location_combo, location_items, include_empty=True, empty_label="None")
        self._reload_combo(self._adjustment_location_combo, location_items, include_empty=False, empty_label="")
        self._reload_combo(self._movement_approved_by_combo, cashier_items, include_empty=True, empty_label="None")
        self._reload_combo(self._adjustment_approved_by_combo, cashier_items, include_empty=True, empty_label="None")
        self._reload_parent_location_combo()

    def _reload_warehouse_combos(self) -> None:
        warehouse_items = [(item.id, item.label) for item in self.warehouse_service.list_warehouse_lookups()]
        self._reload_combo(
            self._location_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._location_warehouse_combo, warehouse_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._stock_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._movement_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._adjustment_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._operations_warehouse_filter_combo, warehouse_items, include_empty=True, empty_label="All"
        )

    def _reload_location_combos(self) -> None:
        location_items = [(item.id, item.label) for item in self.warehouse_service.list_warehouse_location_lookups()]
        self._reload_combo(self._stock_location_combo, location_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._stock_location_filter_combo, location_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._movement_from_location_combo, location_items, include_empty=True, empty_label="None")
        self._reload_combo(self._movement_to_location_combo, location_items, include_empty=True, empty_label="None")
        self._reload_combo(self._adjustment_location_combo, location_items, include_empty=False, empty_label="")

    def _reload_parent_location_combo(self) -> None:
        selected_warehouse_id = self._location_warehouse_combo.currentData()
        location_items = [
            (item.id, item.label)
            for item in self.warehouse_service.list_warehouse_location_lookups(
                warehouse_id=selected_warehouse_id
            )
        ]
        self._reload_combo(self._location_parent_combo, location_items, include_empty=True, empty_label="None")

    def _on_stock_filter_warehouse_changed(self) -> None:
        selected_warehouse_id = self._stock_warehouse_filter_combo.currentData()
        location_items = [
            (item.id, item.label)
            for item in self.warehouse_service.list_warehouse_location_lookups(
                warehouse_id=selected_warehouse_id
            )
        ]
        self._reload_combo(
            self._stock_location_filter_combo,
            location_items,
            include_empty=True,
            empty_label="All",
        )
        self.refresh_stocks()

    def _clear_warehouse_editor(self) -> None:
        self._selected_warehouse_id = None
        self._warehouse_table.clearSelection()
        self._warehouse_name_input.clear()
        self._warehouse_code_input.clear()
        self._warehouse_type_combo.setCurrentIndex(0)
        self._warehouse_description_input.clear()
        self._warehouse_address_input.clear()
        self._warehouse_manager_name_input.clear()
        self._warehouse_contact_phone_input.clear()
        self._warehouse_contact_email_input.clear()
        self._warehouse_security_level_combo.setCurrentIndex(0)
        self._warehouse_min_temperature_input.clear()
        self._warehouse_max_temperature_input.clear()
        self._warehouse_active_checkbox.setChecked(True)
        self._warehouse_receiving_checkbox.setChecked(True)
        self._warehouse_shipping_checkbox.setChecked(True)
        self._warehouse_cycle_count_checkbox.setChecked(True)
        self._warehouse_temperature_checkbox.setChecked(False)
        self._warehouse_security_checkbox.setChecked(False)

    def _clear_location_editor(self) -> None:
        self._selected_location_id = None
        self._location_table.clearSelection()
        self._location_parent_combo.setCurrentIndex(0)
        self._location_name_input.clear()
        self._location_code_input.clear()
        self._location_type_combo.setCurrentIndex(0)
        self._location_level_input.setValue(1)
        self._location_description_input.clear()
        self._location_pick_sequence_input.setValue(0)
        self._location_replenishment_priority_input.setValue(0)
        self._location_block_reason_input.clear()
        self._location_active_checkbox.setChecked(True)
        self._location_blocked_checkbox.setChecked(False)
        self._location_pick_checkbox.setChecked(True)
        self._location_replenishment_checkbox.setChecked(True)

    def _clear_stock_editor(self) -> None:
        self._selected_stock_id = None
        self._stock_table.clearSelection()
        self._stock_quantity_input.setValue(0)
        self._stock_available_quantity_input.setValue(0)
        self._stock_reserved_quantity_input.setValue(0)
        self._stock_min_level_input.setValue(0)
        self._stock_max_level_input.setValue(0)
        self._stock_reorder_point_input.setValue(0)
        self._stock_reorder_quantity_input.setValue(0)
        self._stock_lot_number_input.clear()
        self._stock_expiration_date_input.clear()
        self._stock_block_reason_input.clear()
        self._stock_low_stock_checkbox.setChecked(False)
        self._stock_overstock_checkbox.setChecked(False)
        self._stock_expiry_checkbox.setChecked(False)
        self._stock_active_checkbox.setChecked(True)
        self._stock_discontinued_checkbox.setChecked(False)
        self._stock_blocked_checkbox.setChecked(False)

    def _clear_movement_editor(self) -> None:
        self._selected_movement_id = None
        self._movement_table.clearSelection()
        self._movement_number_input.clear()
        self._movement_type_combo.setCurrentIndex(0)
        self._movement_subtype_input.clear()
        self._movement_status_combo.setCurrentIndex(0)
        self._movement_quantity_input.setValue(0)
        self._movement_date_input.clear()
        self._movement_reference_input.clear()
        self._movement_reason_input.clear()
        self._movement_description_input.clear()
        self._movement_approved_by_combo.setCurrentIndex(0)
        self._movement_approved_checkbox.setChecked(False)

    def _clear_adjustment_editor(self) -> None:
        self._selected_adjustment_id = None
        self._adjustment_table.clearSelection()
        self._adjustment_number_input.clear()
        self._adjustment_type_combo.setCurrentIndex(0)
        self._adjustment_reason_input.clear()
        self._adjustment_status_combo.setCurrentIndex(0)
        self._adjustment_system_quantity_input.setValue(0)
        self._adjustment_counted_quantity_input.setValue(0)
        self._adjustment_difference_input.setValue(0)
        self._adjustment_date_input.clear()
        self._adjustment_approved_by_combo.setCurrentIndex(0)
        self._adjustment_counter_notes_input.clear()
        self._adjustment_supervisor_notes_input.clear()
        self._adjustment_approved_checkbox.setChecked(False)

    def _open_operations_window(self) -> None:
        if self._operations_form is None:
            self._operations_form = WarehouseOperationsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._operations_form.show()
        self._operations_form.raise_()
        self._operations_form.activateWindow()

    def _set_status(self, success: bool, message: str) -> None:
        self._status_label.setStyleSheet("color: #166534;" if success else "color: #b91c1c;")
        self._status_label.setText(message)

    @staticmethod
    def _wrap(widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        wrapper.setLayout(layout)
        return wrapper

    @staticmethod
    def _init_table(table: QTableWidget, selection_callback) -> None:
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        if selection_callback:
            table.itemSelectionChanged.connect(selection_callback)

    @staticmethod
    def _editor_layout(form_layout: QFormLayout, save_cb, delete_cb, new_cb, refresh_cb) -> QVBoxLayout:
        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(new_cb)
        save_button.clicked.connect(save_cb)
        delete_button.clicked.connect(delete_cb)
        refresh_button.clicked.connect(refresh_cb)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_button)
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addStretch(1)
        layout.addLayout(action_layout)
        return layout

    @staticmethod
    def _set_row(table: QTableWidget, row_index: int, values: list[str], row_id: str) -> None:
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, row_id)
            table.setItem(row_index, col, item)

    @staticmethod
    def _selected_row(table: QTableWidget, rows: list[Any]) -> Any | None:
        selected_items = table.selectedItems()
        if not selected_items:
            return None
        selected_id = selected_items[0].data(Qt.UserRole)
        return next((x for x in rows if x.id == selected_id), None)

    def _delete_record(
        self,
        selected_id: str | None,
        title: str,
        question: str,
        deleter,
        refresh,
        clear,
    ) -> None:
        if not selected_id:
            self._set_status(False, "Please select a record to delete.")
            return
        answer = QMessageBox.question(
            self,
            title,
            question,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = deleter(selected_id)
        self._set_status(result.success, result.message)
        if result.success:
            refresh()
            clear()

    @staticmethod
    def _reload_combo(
        combo: QComboBox,
        rows: list[tuple[str, str]],
        include_empty: bool,
        empty_label: str,
    ) -> None:
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        if include_empty:
            combo.addItem(empty_label, None)
        for item_id, label in rows:
            combo.addItem(label, item_id)
        if selected is not None:
            index = combo.findData(selected)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)
