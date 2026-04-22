"""
Campaign management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from datetime import datetime, time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.campaign_management_service import (
    CampaignManagementService,
    CampaignProductView,
    CampaignRuleView,
    CampaignTypeView,
    CampaignUsageView,
    CampaignView,
)
from settings.settings import Settings
from user_interface.form.campaign_operations_form import CampaignOperationsForm


class CampaignManagementForm(QWidget):
    """Manage campaign master data and campaign-related tables."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = CampaignManagementService(store_code=bootstrap_context.store_id)
        self.setWindowTitle(f"{Settings().app_name} - Campaign Management")
        self.setMinimumSize(1420, 960)

        self._campaigns: list[CampaignView] = []
        self._campaign_types: list[CampaignTypeView] = []
        self._campaign_rules: list[CampaignRuleView] = []
        self._campaign_products: list[CampaignProductView] = []
        self._campaign_usages: list[CampaignUsageView] = []

        self._selected_campaign_id: str | None = None
        self._selected_campaign_type_id: str | None = None
        self._selected_rule_id: str | None = None
        self._selected_campaign_product_id: str | None = None
        self._selected_usage_id: str | None = None

        self._campaign_operations_form: CampaignOperationsForm | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Campaign Operations Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_id}  |  Office: {self.bootstrap_context.office_id}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #0f172a;")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)

        header_layout = QHBoxLayout()
        header_layout.addStretch(1)
        header_layout.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_campaigns_tab(), "Campaigns")
        self._tabs.addTab(self._build_campaign_types_tab(), "Campaign Types")
        self._tabs.addTab(self._build_campaign_rules_tab(), "Campaign Rules")
        self._tabs.addTab(self._build_campaign_products_tab(), "Campaign Products")
        self._tabs.addTab(self._build_campaign_usages_tab(), "Campaign Usage")
        self._tabs.addTab(self._build_campaign_operations_tab(), "Campaign Operations")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_campaigns_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self._campaign_search_input = QLineEdit()
        self._campaign_search_input.setPlaceholderText("Search campaign code, name, or description")
        self._campaign_search_input.returnPressed.connect(self.refresh_campaigns)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_campaigns)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_campaigns)
        filter_layout.addWidget(self._campaign_search_input)
        filter_layout.addWidget(search_button)
        filter_layout.addWidget(refresh_button)
        left_layout.addLayout(filter_layout)

        self._campaign_table = QTableWidget(0, 8)
        self._campaign_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Name",
                "Type",
                "Store",
                "Discount Type",
                "Discount %",
                "Active",
                "Usage",
            ]
        )
        self._campaign_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_table.verticalHeader().setVisible(False)
        self._campaign_table.setAlternatingRowColors(True)
        self._campaign_table.itemSelectionChanged.connect(self._on_campaign_selected)
        left_layout.addWidget(self._campaign_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Campaign Editor")
        editor_grid = QGridLayout()

        self._campaign_code_input = QLineEdit()
        self._campaign_name_input = QLineEdit()
        self._campaign_description_input = QPlainTextEdit()
        self._campaign_description_input.setMinimumHeight(70)
        self._campaign_type_combo = QComboBox()
        self._campaign_store_combo = QComboBox()
        self._campaign_discount_type_combo = QComboBox()
        self._campaign_discount_type_combo.addItems(
            [
                "",
                "PERCENTAGE",
                "FIXED_AMOUNT",
                "FREE_PRODUCT",
                "BUY_X_GET_Y",
                "CHEAPEST_FREE",
            ]
        )

        self._campaign_discount_value_input = QDoubleSpinBox()
        self._campaign_discount_value_input.setMaximum(10_000_000_000)
        self._campaign_discount_value_input.setDecimals(4)
        self._campaign_discount_percentage_input = QDoubleSpinBox()
        self._campaign_discount_percentage_input.setMaximum(100)
        self._campaign_discount_percentage_input.setDecimals(4)
        self._campaign_max_discount_amount_input = QDoubleSpinBox()
        self._campaign_max_discount_amount_input.setMaximum(10_000_000_000)
        self._campaign_max_discount_amount_input.setDecimals(4)
        self._campaign_min_purchase_amount_input = QDoubleSpinBox()
        self._campaign_min_purchase_amount_input.setMaximum(10_000_000_000)
        self._campaign_min_purchase_amount_input.setDecimals(4)
        self._campaign_max_purchase_amount_input = QDoubleSpinBox()
        self._campaign_max_purchase_amount_input.setMaximum(10_000_000_000)
        self._campaign_max_purchase_amount_input.setDecimals(4)
        self._campaign_buy_quantity_input = QSpinBox()
        self._campaign_buy_quantity_input.setRange(0, 100_000)
        self._campaign_get_quantity_input = QSpinBox()
        self._campaign_get_quantity_input.setRange(0, 100_000)

        self._campaign_start_date_input = QLineEdit()
        self._campaign_start_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._campaign_end_date_input = QLineEdit()
        self._campaign_end_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._campaign_start_time_input = QLineEdit()
        self._campaign_start_time_input.setPlaceholderText("HH:MM")
        self._campaign_end_time_input = QLineEdit()
        self._campaign_end_time_input.setPlaceholderText("HH:MM")
        self._campaign_days_of_week_input = QLineEdit()
        self._campaign_days_of_week_input.setPlaceholderText("Comma-separated weekdays: 1,2,3,4,5")

        self._campaign_priority_input = QSpinBox()
        self._campaign_priority_input.setRange(1, 1000)
        self._campaign_usage_limit_customer_input = QLineEdit()
        self._campaign_usage_limit_customer_input.setPlaceholderText("Leave empty for unlimited")
        self._campaign_total_usage_limit_input = QLineEdit()
        self._campaign_total_usage_limit_input.setPlaceholderText("Leave empty for unlimited")
        self._campaign_total_usage_count_input = QSpinBox()
        self._campaign_total_usage_count_input.setRange(0, 10_000_000)

        self._campaign_is_combinable_checkbox = QCheckBox("Combinable")
        self._campaign_is_active_checkbox = QCheckBox("Active")
        self._campaign_is_active_checkbox.setChecked(True)
        self._campaign_is_auto_apply_checkbox = QCheckBox("Auto Apply")
        self._campaign_requires_coupon_checkbox = QCheckBox("Requires Coupon")

        self._campaign_customer_segment_combo = QComboBox()
        self._campaign_image_url_input = QLineEdit()
        self._campaign_terms_input = QPlainTextEdit()
        self._campaign_terms_input.setMinimumHeight(50)
        self._campaign_notification_input = QPlainTextEdit()
        self._campaign_notification_input.setMinimumHeight(50)
        self._campaign_settings_input = QPlainTextEdit()
        self._campaign_settings_input.setMinimumHeight(60)

        editor_grid.addWidget(QLabel("Campaign Code"), 0, 0)
        editor_grid.addWidget(self._campaign_code_input, 0, 1)
        editor_grid.addWidget(QLabel("Campaign Name"), 1, 0)
        editor_grid.addWidget(self._campaign_name_input, 1, 1)
        editor_grid.addWidget(QLabel("Campaign Type"), 2, 0)
        editor_grid.addWidget(self._campaign_type_combo, 2, 1)
        editor_grid.addWidget(QLabel("Store"), 3, 0)
        editor_grid.addWidget(self._campaign_store_combo, 3, 1)
        editor_grid.addWidget(QLabel("Discount Type"), 4, 0)
        editor_grid.addWidget(self._campaign_discount_type_combo, 4, 1)
        editor_grid.addWidget(QLabel("Discount Value"), 5, 0)
        editor_grid.addWidget(self._campaign_discount_value_input, 5, 1)
        editor_grid.addWidget(QLabel("Discount Percentage"), 6, 0)
        editor_grid.addWidget(self._campaign_discount_percentage_input, 6, 1)
        editor_grid.addWidget(QLabel("Max Discount Amount"), 7, 0)
        editor_grid.addWidget(self._campaign_max_discount_amount_input, 7, 1)
        editor_grid.addWidget(QLabel("Min Purchase Amount"), 8, 0)
        editor_grid.addWidget(self._campaign_min_purchase_amount_input, 8, 1)
        editor_grid.addWidget(QLabel("Max Purchase Amount"), 9, 0)
        editor_grid.addWidget(self._campaign_max_purchase_amount_input, 9, 1)
        editor_grid.addWidget(QLabel("Buy Quantity"), 10, 0)
        editor_grid.addWidget(self._campaign_buy_quantity_input, 10, 1)
        editor_grid.addWidget(QLabel("Get Quantity"), 11, 0)
        editor_grid.addWidget(self._campaign_get_quantity_input, 11, 1)
        editor_grid.addWidget(QLabel("Start Date"), 12, 0)
        editor_grid.addWidget(self._campaign_start_date_input, 12, 1)
        editor_grid.addWidget(QLabel("End Date"), 13, 0)
        editor_grid.addWidget(self._campaign_end_date_input, 13, 1)
        editor_grid.addWidget(QLabel("Start Time"), 14, 0)
        editor_grid.addWidget(self._campaign_start_time_input, 14, 1)
        editor_grid.addWidget(QLabel("End Time"), 15, 0)
        editor_grid.addWidget(self._campaign_end_time_input, 15, 1)
        editor_grid.addWidget(QLabel("Days of Week"), 16, 0)
        editor_grid.addWidget(self._campaign_days_of_week_input, 16, 1)
        editor_grid.addWidget(QLabel("Priority"), 17, 0)
        editor_grid.addWidget(self._campaign_priority_input, 17, 1)
        editor_grid.addWidget(QLabel("Usage Limit / Customer"), 18, 0)
        editor_grid.addWidget(self._campaign_usage_limit_customer_input, 18, 1)
        editor_grid.addWidget(QLabel("Total Usage Limit"), 19, 0)
        editor_grid.addWidget(self._campaign_total_usage_limit_input, 19, 1)
        editor_grid.addWidget(QLabel("Total Usage Count"), 20, 0)
        editor_grid.addWidget(self._campaign_total_usage_count_input, 20, 1)
        editor_grid.addWidget(self._campaign_is_combinable_checkbox, 21, 1)
        editor_grid.addWidget(self._campaign_is_active_checkbox, 22, 1)
        editor_grid.addWidget(self._campaign_is_auto_apply_checkbox, 23, 1)
        editor_grid.addWidget(self._campaign_requires_coupon_checkbox, 24, 1)
        editor_grid.addWidget(QLabel("Customer Segment"), 25, 0)
        editor_grid.addWidget(self._campaign_customer_segment_combo, 25, 1)
        editor_grid.addWidget(QLabel("Image URL"), 26, 0)
        editor_grid.addWidget(self._campaign_image_url_input, 26, 1)
        editor_grid.addWidget(QLabel("Description"), 27, 0)
        editor_grid.addWidget(self._campaign_description_input, 27, 1)
        editor_grid.addWidget(QLabel("Terms and Conditions"), 28, 0)
        editor_grid.addWidget(self._campaign_terms_input, 28, 1)
        editor_grid.addWidget(QLabel("Notification Message"), 29, 0)
        editor_grid.addWidget(self._campaign_notification_input, 29, 1)
        editor_grid.addWidget(QLabel("Settings JSON"), 30, 0)
        editor_grid.addWidget(self._campaign_settings_input, 30, 1)

        button_layout = QHBoxLayout()
        campaign_new_button = QPushButton("New")
        campaign_save_button = QPushButton("Save")
        campaign_delete_button = QPushButton("Delete")
        campaign_refresh_button = QPushButton("Refresh")
        operations_window_button = QPushButton("Open Operations Window")
        campaign_new_button.clicked.connect(self._new_campaign)
        campaign_save_button.clicked.connect(self._save_campaign)
        campaign_delete_button.clicked.connect(self._delete_campaign)
        campaign_refresh_button.clicked.connect(self.refresh_campaigns)
        operations_window_button.clicked.connect(self._open_campaign_operations_window)
        button_layout.addWidget(campaign_new_button)
        button_layout.addWidget(campaign_save_button)
        button_layout.addWidget(campaign_delete_button)
        button_layout.addWidget(campaign_refresh_button)
        button_layout.addWidget(operations_window_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(editor_grid)
        editor_layout.addLayout(button_layout)
        editor_layout.addStretch(1)

        editor_container = QWidget()
        editor_container.setLayout(editor_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(editor_container)

        editor_box_layout = QVBoxLayout()
        editor_box_layout.addWidget(scroll)
        editor_box.setLayout(editor_box_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 4)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(splitter)
        tab.setLayout(tab_layout)
        return tab

    def _build_campaign_types_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._campaign_type_table = QTableWidget(0, 5)
        self._campaign_type_table.setHorizontalHeaderLabels(
            ["Code", "Name", "Active", "Display Order", "Icon"]
        )
        self._campaign_type_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_type_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_type_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_type_table.verticalHeader().setVisible(False)
        self._campaign_type_table.setAlternatingRowColors(True)
        self._campaign_type_table.itemSelectionChanged.connect(self._on_campaign_type_selected)

        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self._campaign_type_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Campaign Type Editor")
        form = QFormLayout()

        self._campaign_type_code_input = QLineEdit()
        self._campaign_type_name_input = QLineEdit()
        self._campaign_type_description_input = QPlainTextEdit()
        self._campaign_type_description_input.setMinimumHeight(90)
        self._campaign_type_icon_input = QLineEdit()
        self._campaign_type_is_active_checkbox = QCheckBox("Active")
        self._campaign_type_is_active_checkbox.setChecked(True)
        self._campaign_type_display_order_input = QSpinBox()
        self._campaign_type_display_order_input.setRange(0, 10000)
        self._campaign_type_settings_input = QPlainTextEdit()
        self._campaign_type_settings_input.setMinimumHeight(90)

        form.addRow("Code", self._campaign_type_code_input)
        form.addRow("Name", self._campaign_type_name_input)
        form.addRow("Icon", self._campaign_type_icon_input)
        form.addRow("Display Order", self._campaign_type_display_order_input)
        form.addRow(self._campaign_type_is_active_checkbox)
        form.addRow("Description", self._campaign_type_description_input)
        form.addRow("Settings JSON", self._campaign_type_settings_input)

        buttons = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._new_campaign_type)
        save_button.clicked.connect(self._save_campaign_type)
        delete_button.clicked.connect(self._delete_campaign_type)
        refresh_button.clicked.connect(self.refresh_campaign_types)
        buttons.addWidget(new_button)
        buttons.addWidget(save_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(refresh_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addLayout(buttons)
        editor_layout.addStretch(1)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_campaign_rules_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._campaign_rule_table = QTableWidget(0, 7)
        self._campaign_rule_table.setHorizontalHeaderLabels(
            [
                "Campaign",
                "Rule Type",
                "Rule Value",
                "Product",
                "Department",
                "Payment Type",
                "Include",
            ]
        )
        self._campaign_rule_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_rule_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_rule_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_rule_table.verticalHeader().setVisible(False)
        self._campaign_rule_table.setAlternatingRowColors(True)
        self._campaign_rule_table.itemSelectionChanged.connect(self._on_campaign_rule_selected)

        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self._campaign_rule_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Campaign Rule Editor")
        form = QFormLayout()

        self._campaign_rule_campaign_combo = QComboBox()
        self._campaign_rule_type_combo = QComboBox()
        self._campaign_rule_type_combo.addItems(
            [
                "PRODUCT",
                "DEPARTMENT",
                "CATEGORY",
                "BRAND",
                "PAYMENT_TYPE",
                "BARCODE_PATTERN",
            ]
        )
        self._campaign_rule_value_input = QLineEdit()
        self._campaign_rule_product_combo = QComboBox()
        self._campaign_rule_department_combo = QComboBox()
        self._campaign_rule_payment_type_combo = QComboBox()
        self._campaign_rule_manufacturer_combo = QComboBox()
        self._campaign_rule_is_include_checkbox = QCheckBox("Include Rule")
        self._campaign_rule_is_include_checkbox.setChecked(True)
        self._campaign_rule_description_input = QPlainTextEdit()
        self._campaign_rule_description_input.setMinimumHeight(70)
        self._campaign_rule_settings_input = QPlainTextEdit()
        self._campaign_rule_settings_input.setMinimumHeight(70)

        form.addRow("Campaign", self._campaign_rule_campaign_combo)
        form.addRow("Rule Type", self._campaign_rule_type_combo)
        form.addRow("Rule Value", self._campaign_rule_value_input)
        form.addRow("Product", self._campaign_rule_product_combo)
        form.addRow("Department", self._campaign_rule_department_combo)
        form.addRow("Payment Type", self._campaign_rule_payment_type_combo)
        form.addRow("Manufacturer", self._campaign_rule_manufacturer_combo)
        form.addRow(self._campaign_rule_is_include_checkbox)
        form.addRow("Description", self._campaign_rule_description_input)
        form.addRow("Settings JSON", self._campaign_rule_settings_input)

        buttons = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._new_campaign_rule)
        save_button.clicked.connect(self._save_campaign_rule)
        delete_button.clicked.connect(self._delete_campaign_rule)
        refresh_button.clicked.connect(self.refresh_campaign_rules)
        buttons.addWidget(new_button)
        buttons.addWidget(save_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(refresh_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addLayout(buttons)
        editor_layout.addStretch(1)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_campaign_products_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._campaign_product_table = QTableWidget(0, 7)
        self._campaign_product_table.setHorizontalHeaderLabels(
            [
                "Campaign",
                "Product",
                "Gift Product",
                "Min Qty",
                "Max Qty",
                "Discount %",
                "Active",
            ]
        )
        self._campaign_product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_product_table.verticalHeader().setVisible(False)
        self._campaign_product_table.setAlternatingRowColors(True)
        self._campaign_product_table.itemSelectionChanged.connect(self._on_campaign_product_selected)

        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self._campaign_product_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Campaign Product Editor")
        form = QFormLayout()

        self._campaign_product_campaign_combo = QComboBox()
        self._campaign_product_product_combo = QComboBox()
        self._campaign_product_is_gift_checkbox = QCheckBox("Gift Product")
        self._campaign_product_min_quantity_input = QSpinBox()
        self._campaign_product_min_quantity_input.setRange(0, 100_000)
        self._campaign_product_max_quantity_input = QSpinBox()
        self._campaign_product_max_quantity_input.setRange(0, 100_000)
        self._campaign_product_discount_value_input = QDoubleSpinBox()
        self._campaign_product_discount_value_input.setMaximum(10_000_000_000)
        self._campaign_product_discount_value_input.setDecimals(4)
        self._campaign_product_discount_percentage_input = QDoubleSpinBox()
        self._campaign_product_discount_percentage_input.setMaximum(100)
        self._campaign_product_discount_percentage_input.setDecimals(4)
        self._campaign_product_is_active_checkbox = QCheckBox("Active")
        self._campaign_product_is_active_checkbox.setChecked(True)
        self._campaign_product_display_order_input = QSpinBox()
        self._campaign_product_display_order_input.setRange(0, 10000)

        form.addRow("Campaign", self._campaign_product_campaign_combo)
        form.addRow("Product", self._campaign_product_product_combo)
        form.addRow(self._campaign_product_is_gift_checkbox)
        form.addRow("Min Quantity", self._campaign_product_min_quantity_input)
        form.addRow("Max Quantity", self._campaign_product_max_quantity_input)
        form.addRow("Discount Value", self._campaign_product_discount_value_input)
        form.addRow("Discount Percentage", self._campaign_product_discount_percentage_input)
        form.addRow("Display Order", self._campaign_product_display_order_input)
        form.addRow(self._campaign_product_is_active_checkbox)

        buttons = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._new_campaign_product)
        save_button.clicked.connect(self._save_campaign_product)
        delete_button.clicked.connect(self._delete_campaign_product)
        refresh_button.clicked.connect(self.refresh_campaign_products)
        buttons.addWidget(new_button)
        buttons.addWidget(save_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(refresh_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addLayout(buttons)
        editor_layout.addStretch(1)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_campaign_usages_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._campaign_usage_table = QTableWidget(0, 8)
        self._campaign_usage_table.setHorizontalHeaderLabels(
            [
                "Campaign",
                "Customer",
                "Transaction",
                "Store",
                "Cashier",
                "Discount",
                "Usage Date",
                "Coupon",
            ]
        )
        self._campaign_usage_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_usage_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_usage_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_usage_table.verticalHeader().setVisible(False)
        self._campaign_usage_table.setAlternatingRowColors(True)
        self._campaign_usage_table.itemSelectionChanged.connect(self._on_campaign_usage_selected)

        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self._campaign_usage_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Campaign Usage Editor")
        form = QFormLayout()

        self._campaign_usage_campaign_combo = QComboBox()
        self._campaign_usage_customer_combo = QComboBox()
        self._campaign_usage_transaction_id_input = QLineEdit()
        self._campaign_usage_transaction_id_input.setPlaceholderText("Transaction UUID")
        self._campaign_usage_store_combo = QComboBox()
        self._campaign_usage_cashier_combo = QComboBox()
        self._campaign_usage_discount_amount_input = QDoubleSpinBox()
        self._campaign_usage_discount_amount_input.setMaximum(10_000_000_000)
        self._campaign_usage_discount_amount_input.setDecimals(4)
        self._campaign_usage_date_input = QLineEdit()
        self._campaign_usage_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._campaign_usage_coupon_code_input = QLineEdit()
        self._campaign_usage_notes_input = QPlainTextEdit()
        self._campaign_usage_notes_input.setMinimumHeight(90)

        form.addRow("Campaign", self._campaign_usage_campaign_combo)
        form.addRow("Customer", self._campaign_usage_customer_combo)
        form.addRow("Transaction ID", self._campaign_usage_transaction_id_input)
        form.addRow("Store", self._campaign_usage_store_combo)
        form.addRow("Cashier", self._campaign_usage_cashier_combo)
        form.addRow("Discount Amount", self._campaign_usage_discount_amount_input)
        form.addRow("Usage Date", self._campaign_usage_date_input)
        form.addRow("Coupon Code", self._campaign_usage_coupon_code_input)
        form.addRow("Notes", self._campaign_usage_notes_input)

        buttons = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._new_campaign_usage)
        save_button.clicked.connect(self._save_campaign_usage)
        delete_button.clicked.connect(self._delete_campaign_usage)
        refresh_button.clicked.connect(self.refresh_campaign_usages)
        buttons.addWidget(new_button)
        buttons.addWidget(save_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(refresh_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addLayout(buttons)
        editor_layout.addStretch(1)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 3)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_campaign_operations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        top_actions = QHBoxLayout()
        self._campaign_operations_filter_combo = QComboBox()
        operations_refresh_button = QPushButton("Refresh")
        operations_refresh_button.clicked.connect(self.refresh_campaign_operations)
        open_window_button = QPushButton("Open Detailed Operations Window")
        open_window_button.clicked.connect(self._open_campaign_operations_window)
        top_actions.addWidget(QLabel("Campaign"))
        top_actions.addWidget(self._campaign_operations_filter_combo, stretch=1)
        top_actions.addWidget(operations_refresh_button)
        top_actions.addWidget(open_window_button)

        self._campaign_operations_table = QTableWidget(0, 7)
        self._campaign_operations_table.setHorizontalHeaderLabels(
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
        self._campaign_operations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._campaign_operations_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._campaign_operations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._campaign_operations_table.verticalHeader().setVisible(False)
        self._campaign_operations_table.setAlternatingRowColors(True)

        layout.addLayout(top_actions)
        layout.addWidget(self._campaign_operations_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self._reload_lookup_combos()
        self.refresh_campaign_types()
        self.refresh_campaigns()
        self.refresh_campaign_rules()
        self.refresh_campaign_products()
        self.refresh_campaign_usages()
        self.refresh_campaign_operations()
        self._set_status("Campaign module loaded successfully.", True)

    def refresh_campaigns(self) -> None:
        search_text = self._campaign_search_input.text().strip()
        self._campaigns = self.service.list_campaigns(search_text=search_text)
        self._campaign_table.setRowCount(len(self._campaigns))
        for row_index, row in enumerate(self._campaigns):
            self._campaign_table.setItem(row_index, 0, QTableWidgetItem(row.code))
            self._campaign_table.setItem(row_index, 1, QTableWidgetItem(row.name))
            self._campaign_table.setItem(row_index, 2, QTableWidgetItem(row.campaign_type_name))
            self._campaign_table.setItem(row_index, 3, QTableWidgetItem(row.store_label))
            self._campaign_table.setItem(row_index, 4, QTableWidgetItem(row.discount_type or "-"))
            self._campaign_table.setItem(row_index, 5, QTableWidgetItem(f"{row.discount_percentage:.2f}"))
            self._campaign_table.setItem(row_index, 6, QTableWidgetItem("Yes" if row.is_active else "No"))
            self._campaign_table.setItem(row_index, 7, QTableWidgetItem(str(row.total_usage_count)))
        self._campaign_table.resizeColumnsToContents()
        self._campaign_table.horizontalHeader().setStretchLastSection(True)

    def refresh_campaign_types(self) -> None:
        self._campaign_types = self.service.list_campaign_types()
        self._campaign_type_table.setRowCount(len(self._campaign_types))
        for row_index, row in enumerate(self._campaign_types):
            self._campaign_type_table.setItem(row_index, 0, QTableWidgetItem(row.code))
            self._campaign_type_table.setItem(row_index, 1, QTableWidgetItem(row.name))
            self._campaign_type_table.setItem(row_index, 2, QTableWidgetItem("Yes" if row.is_active else "No"))
            self._campaign_type_table.setItem(row_index, 3, QTableWidgetItem(str(row.display_order)))
            self._campaign_type_table.setItem(row_index, 4, QTableWidgetItem(row.icon))
        self._campaign_type_table.resizeColumnsToContents()
        self._campaign_type_table.horizontalHeader().setStretchLastSection(True)
        self._reload_lookup_combos()

    def refresh_campaign_rules(self) -> None:
        self._campaign_rules = self.service.list_campaign_rules()
        self._campaign_rule_table.setRowCount(len(self._campaign_rules))
        for row_index, row in enumerate(self._campaign_rules):
            self._campaign_rule_table.setItem(row_index, 0, QTableWidgetItem(row.campaign_label))
            self._campaign_rule_table.setItem(row_index, 1, QTableWidgetItem(row.rule_type))
            self._campaign_rule_table.setItem(row_index, 2, QTableWidgetItem(row.rule_value))
            self._campaign_rule_table.setItem(row_index, 3, QTableWidgetItem(row.product_label))
            self._campaign_rule_table.setItem(row_index, 4, QTableWidgetItem(row.department_label))
            self._campaign_rule_table.setItem(row_index, 5, QTableWidgetItem(row.payment_type_label))
            self._campaign_rule_table.setItem(
                row_index, 6, QTableWidgetItem("Yes" if row.is_include else "No")
            )
        self._campaign_rule_table.resizeColumnsToContents()
        self._campaign_rule_table.horizontalHeader().setStretchLastSection(True)

    def refresh_campaign_products(self) -> None:
        self._campaign_products = self.service.list_campaign_products()
        self._campaign_product_table.setRowCount(len(self._campaign_products))
        for row_index, row in enumerate(self._campaign_products):
            self._campaign_product_table.setItem(row_index, 0, QTableWidgetItem(row.campaign_label))
            self._campaign_product_table.setItem(row_index, 1, QTableWidgetItem(row.product_label))
            self._campaign_product_table.setItem(
                row_index, 2, QTableWidgetItem("Yes" if row.is_gift_product else "No")
            )
            self._campaign_product_table.setItem(
                row_index, 3, QTableWidgetItem("" if row.min_quantity is None else str(row.min_quantity))
            )
            self._campaign_product_table.setItem(
                row_index, 4, QTableWidgetItem("" if row.max_quantity is None else str(row.max_quantity))
            )
            self._campaign_product_table.setItem(
                row_index, 5, QTableWidgetItem(f"{row.discount_percentage:.2f}")
            )
            self._campaign_product_table.setItem(
                row_index, 6, QTableWidgetItem("Yes" if row.is_active else "No")
            )
        self._campaign_product_table.resizeColumnsToContents()
        self._campaign_product_table.horizontalHeader().setStretchLastSection(True)

    def refresh_campaign_usages(self) -> None:
        self._campaign_usages = self.service.list_campaign_usages()
        self._campaign_usage_table.setRowCount(len(self._campaign_usages))
        for row_index, row in enumerate(self._campaign_usages):
            self._campaign_usage_table.setItem(row_index, 0, QTableWidgetItem(row.campaign_label))
            self._campaign_usage_table.setItem(row_index, 1, QTableWidgetItem(row.customer_label))
            self._campaign_usage_table.setItem(row_index, 2, QTableWidgetItem(row.transaction_label))
            self._campaign_usage_table.setItem(row_index, 3, QTableWidgetItem(row.store_label))
            self._campaign_usage_table.setItem(row_index, 4, QTableWidgetItem(row.cashier_label))
            self._campaign_usage_table.setItem(
                row_index, 5, QTableWidgetItem(f"{row.discount_amount:.2f}")
            )
            self._campaign_usage_table.setItem(
                row_index,
                6,
                QTableWidgetItem(row.usage_date.isoformat(sep=" ") if row.usage_date else "-"),
            )
            self._campaign_usage_table.setItem(row_index, 7, QTableWidgetItem(row.coupon_code))
        self._campaign_usage_table.resizeColumnsToContents()
        self._campaign_usage_table.horizontalHeader().setStretchLastSection(True)

    def refresh_campaign_operations(self) -> None:
        selected_campaign_id = self._campaign_operations_filter_combo.currentData()
        rows = self.service.list_campaign_operations(campaign_id=selected_campaign_id)
        self._campaign_operations_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self._campaign_operations_table.setItem(row_index, 0, QTableWidgetItem(row.campaign_code))
            self._campaign_operations_table.setItem(row_index, 1, QTableWidgetItem(row.campaign_name))
            self._campaign_operations_table.setItem(
                row_index, 2, QTableWidgetItem(row.campaign_type_name)
            )
            self._campaign_operations_table.setItem(
                row_index, 3, QTableWidgetItem("Yes" if row.is_active else "No")
            )
            self._campaign_operations_table.setItem(
                row_index, 4, QTableWidgetItem(str(row.usage_count))
            )
            self._campaign_operations_table.setItem(
                row_index, 5, QTableWidgetItem(f"{row.total_discount_amount:.2f}")
            )
            self._campaign_operations_table.setItem(
                row_index,
                6,
                QTableWidgetItem(row.last_usage_at.isoformat(sep=" ") if row.last_usage_at else "-"),
            )
        self._campaign_operations_table.resizeColumnsToContents()
        self._campaign_operations_table.horizontalHeader().setStretchLastSection(True)

    def _reload_lookup_combos(self) -> None:
        self._set_combo_items(self._campaign_type_combo, self.service.list_campaign_type_lookups())
        self._set_combo_items(
            self._campaign_store_combo,
            self.service.list_store_lookups(),
            first_label="Default Store",
        )
        self._set_combo_items(
            self._campaign_customer_segment_combo,
            self.service.list_customer_segment_lookups(),
            first_label="All Customers",
        )

        campaign_lookups = self.service.list_campaign_lookups()
        self._set_combo_items(self._campaign_rule_campaign_combo, campaign_lookups)
        self._set_combo_items(self._campaign_product_campaign_combo, campaign_lookups)
        self._set_combo_items(self._campaign_usage_campaign_combo, campaign_lookups)
        self._set_combo_items(
            self._campaign_operations_filter_combo,
            campaign_lookups,
            first_label="All Campaigns",
        )

        self._set_combo_items(
            self._campaign_rule_product_combo,
            self.service.list_product_lookups(),
            first_label="Not Selected",
        )
        self._set_combo_items(
            self._campaign_rule_department_combo,
            self.service.list_department_lookups(),
            first_label="Not Selected",
        )
        self._set_combo_items(
            self._campaign_rule_payment_type_combo,
            self.service.list_payment_type_lookups(),
            first_label="Not Selected",
        )
        self._set_combo_items(
            self._campaign_rule_manufacturer_combo,
            self.service.list_manufacturer_lookups(),
            first_label="Not Selected",
        )

        self._set_combo_items(self._campaign_product_product_combo, self.service.list_product_lookups())
        self._set_combo_items(
            self._campaign_usage_customer_combo,
            self.service.list_customer_lookups(),
            first_label="Not Selected",
        )
        self._set_combo_items(
            self._campaign_usage_store_combo,
            self.service.list_store_lookups(),
            first_label="Default Store",
        )
        self._set_combo_items(
            self._campaign_usage_cashier_combo,
            self.service.list_cashier_lookups(),
            first_label="Not Selected",
        )

    def _on_campaign_selected(self) -> None:
        index = self._campaign_table.currentRow()
        if index < 0 or index >= len(self._campaigns):
            return
        item = self._campaigns[index]
        self._selected_campaign_id = item.id
        self._campaign_code_input.setText(item.code)
        self._campaign_name_input.setText(item.name)
        self._campaign_description_input.setPlainText(item.description)
        self._select_combo_value(self._campaign_type_combo, item.fk_campaign_type_id)
        self._select_combo_value(self._campaign_store_combo, item.fk_store_id)
        self._campaign_discount_type_combo.setCurrentText(item.discount_type)
        self._campaign_discount_value_input.setValue(float(item.discount_value))
        self._campaign_discount_percentage_input.setValue(float(item.discount_percentage))
        self._campaign_max_discount_amount_input.setValue(float(item.max_discount_amount))
        self._campaign_min_purchase_amount_input.setValue(float(item.min_purchase_amount))
        self._campaign_max_purchase_amount_input.setValue(float(item.max_purchase_amount))
        self._campaign_buy_quantity_input.setValue(item.buy_quantity)
        self._campaign_get_quantity_input.setValue(item.get_quantity)
        self._campaign_start_date_input.setText(self._format_datetime(item.start_date))
        self._campaign_end_date_input.setText(self._format_datetime(item.end_date))
        self._campaign_start_time_input.setText(self._format_time(item.start_time))
        self._campaign_end_time_input.setText(self._format_time(item.end_time))
        self._campaign_days_of_week_input.setText(item.days_of_week)
        self._campaign_priority_input.setValue(item.priority)
        self._campaign_usage_limit_customer_input.setText(
            "" if item.usage_limit_per_customer is None else str(item.usage_limit_per_customer)
        )
        self._campaign_total_usage_limit_input.setText(
            "" if item.total_usage_limit is None else str(item.total_usage_limit)
        )
        self._campaign_total_usage_count_input.setValue(item.total_usage_count)
        self._campaign_is_combinable_checkbox.setChecked(item.is_combinable)
        self._campaign_is_active_checkbox.setChecked(item.is_active)
        self._campaign_is_auto_apply_checkbox.setChecked(item.is_auto_apply)
        self._campaign_requires_coupon_checkbox.setChecked(item.requires_coupon)
        self._select_combo_value(self._campaign_customer_segment_combo, item.fk_customer_segment_id)
        self._campaign_image_url_input.setText(item.image_url)
        self._campaign_terms_input.setPlainText(item.terms_conditions)
        self._campaign_notification_input.setPlainText(item.notification_message)
        self._campaign_settings_input.setPlainText(item.settings_json)

    def _on_campaign_type_selected(self) -> None:
        index = self._campaign_type_table.currentRow()
        if index < 0 or index >= len(self._campaign_types):
            return
        item = self._campaign_types[index]
        self._selected_campaign_type_id = item.id
        self._campaign_type_code_input.setText(item.code)
        self._campaign_type_name_input.setText(item.name)
        self._campaign_type_description_input.setPlainText(item.description)
        self._campaign_type_icon_input.setText(item.icon)
        self._campaign_type_is_active_checkbox.setChecked(item.is_active)
        self._campaign_type_display_order_input.setValue(item.display_order)
        self._campaign_type_settings_input.setPlainText(item.settings_json)

    def _on_campaign_rule_selected(self) -> None:
        index = self._campaign_rule_table.currentRow()
        if index < 0 or index >= len(self._campaign_rules):
            return
        item = self._campaign_rules[index]
        self._selected_rule_id = item.id
        self._select_combo_value(self._campaign_rule_campaign_combo, item.campaign_id)
        self._campaign_rule_type_combo.setCurrentText(item.rule_type)
        self._campaign_rule_value_input.setText(item.rule_value)
        self._select_combo_value(self._campaign_rule_product_combo, item.fk_product_id)
        self._select_combo_value(self._campaign_rule_department_combo, item.fk_department_id)
        self._select_combo_value(self._campaign_rule_payment_type_combo, item.fk_payment_type_id)
        self._select_combo_value(
            self._campaign_rule_manufacturer_combo,
            item.fk_product_manufacturer_id,
        )
        self._campaign_rule_is_include_checkbox.setChecked(item.is_include)
        self._campaign_rule_description_input.setPlainText(item.description)
        self._campaign_rule_settings_input.setPlainText(item.settings_json)

    def _on_campaign_product_selected(self) -> None:
        index = self._campaign_product_table.currentRow()
        if index < 0 or index >= len(self._campaign_products):
            return
        item = self._campaign_products[index]
        self._selected_campaign_product_id = item.id
        self._select_combo_value(self._campaign_product_campaign_combo, item.campaign_id)
        self._select_combo_value(self._campaign_product_product_combo, item.product_id)
        self._campaign_product_is_gift_checkbox.setChecked(item.is_gift_product)
        self._campaign_product_min_quantity_input.setValue(item.min_quantity or 0)
        self._campaign_product_max_quantity_input.setValue(item.max_quantity or 0)
        self._campaign_product_discount_value_input.setValue(float(item.discount_value))
        self._campaign_product_discount_percentage_input.setValue(float(item.discount_percentage))
        self._campaign_product_is_active_checkbox.setChecked(item.is_active)
        self._campaign_product_display_order_input.setValue(item.display_order)

    def _on_campaign_usage_selected(self) -> None:
        index = self._campaign_usage_table.currentRow()
        if index < 0 or index >= len(self._campaign_usages):
            return
        item = self._campaign_usages[index]
        self._selected_usage_id = item.id
        self._select_combo_value(self._campaign_usage_campaign_combo, item.campaign_id)
        self._select_combo_value(self._campaign_usage_customer_combo, item.customer_id)
        self._campaign_usage_transaction_id_input.setText(item.transaction_id or "")
        self._select_combo_value(self._campaign_usage_store_combo, item.store_id)
        self._select_combo_value(self._campaign_usage_cashier_combo, item.cashier_id)
        self._campaign_usage_discount_amount_input.setValue(float(item.discount_amount))
        self._campaign_usage_date_input.setText(self._format_datetime(item.usage_date))
        self._campaign_usage_coupon_code_input.setText(item.coupon_code)
        self._campaign_usage_notes_input.setPlainText(item.notes)

    def _new_campaign(self) -> None:
        self._selected_campaign_id = None
        self._campaign_code_input.clear()
        self._campaign_name_input.clear()
        self._campaign_description_input.clear()
        self._campaign_type_combo.setCurrentIndex(0)
        self._campaign_store_combo.setCurrentIndex(0)
        self._campaign_discount_type_combo.setCurrentIndex(0)
        self._campaign_discount_value_input.setValue(0)
        self._campaign_discount_percentage_input.setValue(0)
        self._campaign_max_discount_amount_input.setValue(0)
        self._campaign_min_purchase_amount_input.setValue(0)
        self._campaign_max_purchase_amount_input.setValue(0)
        self._campaign_buy_quantity_input.setValue(0)
        self._campaign_get_quantity_input.setValue(0)
        self._campaign_start_date_input.clear()
        self._campaign_end_date_input.clear()
        self._campaign_start_time_input.clear()
        self._campaign_end_time_input.clear()
        self._campaign_days_of_week_input.clear()
        self._campaign_priority_input.setValue(1)
        self._campaign_usage_limit_customer_input.clear()
        self._campaign_total_usage_limit_input.clear()
        self._campaign_total_usage_count_input.setValue(0)
        self._campaign_is_combinable_checkbox.setChecked(False)
        self._campaign_is_active_checkbox.setChecked(True)
        self._campaign_is_auto_apply_checkbox.setChecked(False)
        self._campaign_requires_coupon_checkbox.setChecked(False)
        self._campaign_customer_segment_combo.setCurrentIndex(0)
        self._campaign_image_url_input.clear()
        self._campaign_terms_input.clear()
        self._campaign_notification_input.clear()
        self._campaign_settings_input.clear()

    def _save_campaign(self) -> None:
        try:
            payload = {
                "code": self._campaign_code_input.text().strip(),
                "name": self._campaign_name_input.text().strip(),
                "description": self._campaign_description_input.toPlainText().strip(),
                "fk_campaign_type_id": self._campaign_type_combo.currentData(),
                "fk_store_id": self._campaign_store_combo.currentData(),
                "discount_type": self._campaign_discount_type_combo.currentText().strip(),
                "discount_value": self._campaign_discount_value_input.value(),
                "discount_percentage": self._campaign_discount_percentage_input.value(),
                "max_discount_amount": self._campaign_max_discount_amount_input.value(),
                "min_purchase_amount": self._campaign_min_purchase_amount_input.value(),
                "max_purchase_amount": self._campaign_max_purchase_amount_input.value(),
                "buy_quantity": self._campaign_buy_quantity_input.value(),
                "get_quantity": self._campaign_get_quantity_input.value(),
                "start_date": self._parse_datetime(self._campaign_start_date_input.text()),
                "end_date": self._parse_datetime(self._campaign_end_date_input.text()),
                "start_time": self._parse_time(self._campaign_start_time_input.text()),
                "end_time": self._parse_time(self._campaign_end_time_input.text()),
                "days_of_week": self._campaign_days_of_week_input.text().strip(),
                "priority": self._campaign_priority_input.value(),
                "usage_limit_per_customer": self._campaign_usage_limit_customer_input.text().strip(),
                "total_usage_limit": self._campaign_total_usage_limit_input.text().strip(),
                "total_usage_count": self._campaign_total_usage_count_input.value(),
                "is_combinable": self._campaign_is_combinable_checkbox.isChecked(),
                "is_active": self._campaign_is_active_checkbox.isChecked(),
                "is_auto_apply": self._campaign_is_auto_apply_checkbox.isChecked(),
                "requires_coupon": self._campaign_requires_coupon_checkbox.isChecked(),
                "fk_customer_segment_id": self._campaign_customer_segment_combo.currentData(),
                "image_url": self._campaign_image_url_input.text().strip(),
                "terms_conditions": self._campaign_terms_input.toPlainText().strip(),
                "notification_message": self._campaign_notification_input.toPlainText().strip(),
                "settings_json": self._campaign_settings_input.toPlainText().strip(),
            }
        except ValueError as error:
            self._set_status(str(error), False)
            return

        result = self.service.save_campaign(payload=payload, campaign_id=self._selected_campaign_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._reload_lookup_combos()
            self.refresh_campaigns()
            self.refresh_campaign_rules()
            self.refresh_campaign_products()
            self.refresh_campaign_usages()
            self.refresh_campaign_operations()

    def _delete_campaign(self) -> None:
        if not self._selected_campaign_id:
            self._set_status("Select a campaign row before delete operation.", False)
            return
        answer = QMessageBox.question(
            self,
            "Delete Campaign",
            "Do you want to soft delete selected campaign?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_campaign(self._selected_campaign_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign()
            self._reload_lookup_combos()
            self.refresh_campaigns()
            self.refresh_campaign_rules()
            self.refresh_campaign_products()
            self.refresh_campaign_usages()
            self.refresh_campaign_operations()

    def _new_campaign_type(self) -> None:
        self._selected_campaign_type_id = None
        self._campaign_type_code_input.clear()
        self._campaign_type_name_input.clear()
        self._campaign_type_description_input.clear()
        self._campaign_type_icon_input.clear()
        self._campaign_type_is_active_checkbox.setChecked(True)
        self._campaign_type_display_order_input.setValue(0)
        self._campaign_type_settings_input.clear()

    def _save_campaign_type(self) -> None:
        payload = {
            "code": self._campaign_type_code_input.text().strip(),
            "name": self._campaign_type_name_input.text().strip(),
            "description": self._campaign_type_description_input.toPlainText().strip(),
            "icon": self._campaign_type_icon_input.text().strip(),
            "is_active": self._campaign_type_is_active_checkbox.isChecked(),
            "display_order": self._campaign_type_display_order_input.value(),
            "settings_json": self._campaign_type_settings_input.toPlainText().strip(),
        }
        result = self.service.save_campaign_type(
            payload=payload,
            campaign_type_id=self._selected_campaign_type_id,
        )
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_type()
            self.refresh_campaign_types()
            self.refresh_campaigns()
            self.refresh_campaign_operations()

    def _delete_campaign_type(self) -> None:
        if not self._selected_campaign_type_id:
            self._set_status("Select a campaign type row before delete operation.", False)
            return
        answer = QMessageBox.question(
            self,
            "Delete Campaign Type",
            "Do you want to soft delete selected campaign type?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_campaign_type(self._selected_campaign_type_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_type()
            self.refresh_campaign_types()
            self.refresh_campaigns()
            self.refresh_campaign_operations()

    def _new_campaign_rule(self) -> None:
        self._selected_rule_id = None
        self._campaign_rule_campaign_combo.setCurrentIndex(0)
        self._campaign_rule_type_combo.setCurrentIndex(0)
        self._campaign_rule_value_input.clear()
        self._campaign_rule_product_combo.setCurrentIndex(0)
        self._campaign_rule_department_combo.setCurrentIndex(0)
        self._campaign_rule_payment_type_combo.setCurrentIndex(0)
        self._campaign_rule_manufacturer_combo.setCurrentIndex(0)
        self._campaign_rule_is_include_checkbox.setChecked(True)
        self._campaign_rule_description_input.clear()
        self._campaign_rule_settings_input.clear()

    def _save_campaign_rule(self) -> None:
        payload = {
            "campaign_id": self._campaign_rule_campaign_combo.currentData(),
            "rule_type": self._campaign_rule_type_combo.currentText().strip(),
            "rule_value": self._campaign_rule_value_input.text().strip(),
            "fk_product_id": self._campaign_rule_product_combo.currentData(),
            "fk_department_id": self._campaign_rule_department_combo.currentData(),
            "fk_payment_type_id": self._campaign_rule_payment_type_combo.currentData(),
            "fk_product_manufacturer_id": self._campaign_rule_manufacturer_combo.currentData(),
            "is_include": self._campaign_rule_is_include_checkbox.isChecked(),
            "description": self._campaign_rule_description_input.toPlainText().strip(),
            "settings_json": self._campaign_rule_settings_input.toPlainText().strip(),
        }
        result = self.service.save_campaign_rule(payload=payload, rule_id=self._selected_rule_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_rule()
            self.refresh_campaign_rules()

    def _delete_campaign_rule(self) -> None:
        if not self._selected_rule_id:
            self._set_status("Select a campaign rule row before delete operation.", False)
            return
        answer = QMessageBox.question(
            self,
            "Delete Campaign Rule",
            "Do you want to soft delete selected campaign rule?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_campaign_rule(self._selected_rule_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_rule()
            self.refresh_campaign_rules()

    def _new_campaign_product(self) -> None:
        self._selected_campaign_product_id = None
        self._campaign_product_campaign_combo.setCurrentIndex(0)
        self._campaign_product_product_combo.setCurrentIndex(0)
        self._campaign_product_is_gift_checkbox.setChecked(False)
        self._campaign_product_min_quantity_input.setValue(0)
        self._campaign_product_max_quantity_input.setValue(0)
        self._campaign_product_discount_value_input.setValue(0)
        self._campaign_product_discount_percentage_input.setValue(0)
        self._campaign_product_is_active_checkbox.setChecked(True)
        self._campaign_product_display_order_input.setValue(0)

    def _save_campaign_product(self) -> None:
        payload = {
            "campaign_id": self._campaign_product_campaign_combo.currentData(),
            "product_id": self._campaign_product_product_combo.currentData(),
            "is_gift_product": self._campaign_product_is_gift_checkbox.isChecked(),
            "min_quantity": self._campaign_product_min_quantity_input.value(),
            "max_quantity": self._campaign_product_max_quantity_input.value(),
            "discount_value": self._campaign_product_discount_value_input.value(),
            "discount_percentage": self._campaign_product_discount_percentage_input.value(),
            "is_active": self._campaign_product_is_active_checkbox.isChecked(),
            "display_order": self._campaign_product_display_order_input.value(),
        }
        result = self.service.save_campaign_product(
            payload=payload,
            campaign_product_id=self._selected_campaign_product_id,
        )
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_product()
            self.refresh_campaign_products()

    def _delete_campaign_product(self) -> None:
        if not self._selected_campaign_product_id:
            self._set_status("Select a campaign product row before delete operation.", False)
            return
        answer = QMessageBox.question(
            self,
            "Delete Campaign Product",
            "Do you want to soft delete selected campaign product row?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_campaign_product(self._selected_campaign_product_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_product()
            self.refresh_campaign_products()

    def _new_campaign_usage(self) -> None:
        self._selected_usage_id = None
        self._campaign_usage_campaign_combo.setCurrentIndex(0)
        self._campaign_usage_customer_combo.setCurrentIndex(0)
        self._campaign_usage_transaction_id_input.clear()
        self._campaign_usage_store_combo.setCurrentIndex(0)
        self._campaign_usage_cashier_combo.setCurrentIndex(0)
        self._campaign_usage_discount_amount_input.setValue(0)
        self._campaign_usage_date_input.clear()
        self._campaign_usage_coupon_code_input.clear()
        self._campaign_usage_notes_input.clear()

    def _save_campaign_usage(self) -> None:
        try:
            payload = {
                "campaign_id": self._campaign_usage_campaign_combo.currentData(),
                "fk_customer_id": self._campaign_usage_customer_combo.currentData(),
                "fk_transaction_head_id": self._campaign_usage_transaction_id_input.text().strip(),
                "fk_store_id": self._campaign_usage_store_combo.currentData(),
                "fk_cashier_id": self._campaign_usage_cashier_combo.currentData(),
                "discount_amount": self._campaign_usage_discount_amount_input.value(),
                "usage_date": self._parse_datetime(self._campaign_usage_date_input.text()),
                "coupon_code": self._campaign_usage_coupon_code_input.text().strip(),
                "notes": self._campaign_usage_notes_input.toPlainText().strip(),
            }
        except ValueError as error:
            self._set_status(str(error), False)
            return

        result = self.service.save_campaign_usage(payload=payload, usage_id=self._selected_usage_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_usage()
            self.refresh_campaign_usages()
            self.refresh_campaign_operations()

    def _delete_campaign_usage(self) -> None:
        if not self._selected_usage_id:
            self._set_status("Select a campaign usage row before delete operation.", False)
            return
        answer = QMessageBox.question(
            self,
            "Delete Campaign Usage",
            "Do you want to soft delete selected campaign usage row?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_campaign_usage(self._selected_usage_id)
        self._set_status(result.message, result.success)
        if result.success:
            self._new_campaign_usage()
            self.refresh_campaign_usages()
            self.refresh_campaign_operations()

    def _open_campaign_operations_window(self) -> None:
        if self._campaign_operations_form is None:
            self._campaign_operations_form = CampaignOperationsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._campaign_operations_form.refresh()
        self._campaign_operations_form.show()
        self._campaign_operations_form.raise_()
        self._campaign_operations_form.activateWindow()

    def _set_status(self, message: str, success: bool) -> None:
        color = "#166534" if success else "#b91c1c"
        self._status_label.setStyleSheet(f"color: {color};")
        self._status_label.setText(message)

    @staticmethod
    def _set_combo_items(combo: QComboBox, items, first_label: str | None = None) -> None:
        current_value = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        if first_label is not None:
            combo.addItem(first_label, None)
        for item in items:
            combo.addItem(item.label, item.id)
        if current_value:
            index = combo.findData(current_value, role=Qt.UserRole)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    @staticmethod
    def _select_combo_value(combo: QComboBox, value: str | None) -> None:
        index = combo.findData(value, role=Qt.UserRole)
        if index >= 0:
            combo.setCurrentIndex(index)
            return
        if combo.count() > 0:
            combo.setCurrentIndex(0)

    @staticmethod
    def _format_datetime(value: datetime | None) -> str:
        if value is None:
            return ""
        return value.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return datetime.strptime(normalized, "%Y-%m-%d %H:%M")
        except ValueError as error:
            raise ValueError("Datetime fields must use format YYYY-MM-DD HH:MM.") from error

    @staticmethod
    def _format_time(value: time | None) -> str:
        if value is None:
            return ""
        return value.strftime("%H:%M")

    @staticmethod
    def _parse_time(value: str) -> time | None:
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return datetime.strptime(normalized, "%H:%M").time()
        except ValueError as error:
            raise ValueError("Time fields must use format HH:MM.") from error
