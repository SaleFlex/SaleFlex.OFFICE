"""
Customer management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
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
from office.service.customer_management_service import (
    CustomerLoyaltyView,
    CustomerManagementService,
    CustomerOperationView,
    CustomerSegmentMemberView,
    CustomerSegmentView,
    CustomerView,
    LoyaltyPointTransactionView,
)
from settings.settings import Settings
from user_interface.form.customer_operations_form import CustomerOperationsForm
from user_interface.form.loyalty_management_form import LoyaltyManagementForm
from user_interface.form.loyalty_operations_form import LoyaltyOperationsForm


class CustomerManagementForm(QWidget):
    """Manage customer, segmentation, and loyalty-related workflows."""

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
        self.setWindowTitle(f"{Settings().app_name} - Customer Management")
        self.setMinimumSize(1440, 960)

        self._customers: list[CustomerView] = []
        self._segments: list[CustomerSegmentView] = []
        self._members: list[CustomerSegmentMemberView] = []
        self._loyalties: list[CustomerLoyaltyView] = []
        self._transactions: list[LoyaltyPointTransactionView] = []
        self._operations: list[CustomerOperationView] = []

        self._selected_customer_id: str | None = None
        self._selected_segment_id: str | None = None
        self._selected_member_id: str | None = None
        self._selected_loyalty_id: str | None = None
        self._selected_transaction_id: str | None = None

        self._customer_operations_form: CustomerOperationsForm | None = None
        self._loyalty_management_form: LoyaltyManagementForm | None = None
        self._loyalty_operations_form: LoyaltyOperationsForm | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Customer Operations Center")
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
        self._tabs.addTab(self._build_customers_tab(), "Customers")
        self._tabs.addTab(self._build_segments_tab(), "Customer Segments")
        self._tabs.addTab(self._build_segment_members_tab(), "Segment Members")
        self._tabs.addTab(self._build_loyalty_tab(), "Customer Loyalty")
        self._tabs.addTab(self._build_point_transactions_tab(), "Loyalty Point Transactions")
        self._tabs.addTab(self._build_operations_tab(), "Customer Operations")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_customers_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._customer_search_input = QLineEdit()
        self._customer_search_input.setPlaceholderText("Search customer name, phone, email, or national id")
        self._customer_search_input.returnPressed.connect(self.refresh_customers)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_customers)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_customers)
        filter_layout.addWidget(self._customer_search_input)
        filter_layout.addWidget(search_button)
        filter_layout.addWidget(refresh_button)
        left_layout.addLayout(filter_layout)

        self._customer_table = QTableWidget(0, 10)
        self._customer_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Last Name",
                "Phone",
                "Email",
                "Date of Birth",
                "Active",
                "Walk-in",
                "Segments",
                "Available Points",
                "Program",
            ]
        )
        self._customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._customer_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._customer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._customer_table.verticalHeader().setVisible(False)
        self._customer_table.setAlternatingRowColors(True)
        self._customer_table.itemSelectionChanged.connect(self._on_customer_row_selected)
        left_layout.addWidget(self._customer_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Customer Editor")
        editor_grid = QGridLayout()
        self._customer_name_input = QLineEdit()
        self._customer_last_name_input = QLineEdit()
        self._customer_phone_input = QLineEdit()
        self._customer_phone_normalized_input = QLineEdit()
        self._customer_email_input = QLineEdit()
        self._customer_dob_input = QLineEdit()
        self._customer_dob_input.setPlaceholderText("YYYY-MM-DD")
        self._customer_gender_combo = QComboBox()
        self._customer_gender_combo.addItems(["", "MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"])
        self._customer_national_id_input = QLineEdit()
        self._customer_tax_id_input = QLineEdit()
        self._customer_registration_source_input = QLineEdit()
        self._customer_zip_code_input = QLineEdit()
        self._customer_address_1_input = QLineEdit()
        self._customer_address_2_input = QLineEdit()
        self._customer_address_3_input = QLineEdit()
        self._customer_preferences_input = QPlainTextEdit()
        self._customer_preferences_input.setMinimumHeight(70)
        self._customer_description_input = QPlainTextEdit()
        self._customer_description_input.setMinimumHeight(70)
        self._customer_marketing_checkbox = QCheckBox("Marketing Consent")
        self._customer_sms_checkbox = QCheckBox("SMS Consent")
        self._customer_email_checkbox = QCheckBox("Email Consent")
        self._customer_walkin_checkbox = QCheckBox("Walk-in Customer")
        self._customer_active_checkbox = QCheckBox("Active")
        self._customer_active_checkbox.setChecked(True)

        editor_grid.addWidget(QLabel("Name"), 0, 0)
        editor_grid.addWidget(self._customer_name_input, 0, 1)
        editor_grid.addWidget(QLabel("Last Name"), 1, 0)
        editor_grid.addWidget(self._customer_last_name_input, 1, 1)
        editor_grid.addWidget(QLabel("Phone"), 2, 0)
        editor_grid.addWidget(self._customer_phone_input, 2, 1)
        editor_grid.addWidget(QLabel("Phone Normalized"), 3, 0)
        editor_grid.addWidget(self._customer_phone_normalized_input, 3, 1)
        editor_grid.addWidget(QLabel("Email"), 4, 0)
        editor_grid.addWidget(self._customer_email_input, 4, 1)
        editor_grid.addWidget(QLabel("Date of Birth"), 5, 0)
        editor_grid.addWidget(self._customer_dob_input, 5, 1)
        editor_grid.addWidget(QLabel("Gender"), 6, 0)
        editor_grid.addWidget(self._customer_gender_combo, 6, 1)
        editor_grid.addWidget(QLabel("National ID"), 7, 0)
        editor_grid.addWidget(self._customer_national_id_input, 7, 1)
        editor_grid.addWidget(QLabel("Tax ID"), 8, 0)
        editor_grid.addWidget(self._customer_tax_id_input, 8, 1)
        editor_grid.addWidget(QLabel("Registration Source"), 9, 0)
        editor_grid.addWidget(self._customer_registration_source_input, 9, 1)
        editor_grid.addWidget(QLabel("Zip Code"), 10, 0)
        editor_grid.addWidget(self._customer_zip_code_input, 10, 1)
        editor_grid.addWidget(QLabel("Address Line 1"), 11, 0)
        editor_grid.addWidget(self._customer_address_1_input, 11, 1)
        editor_grid.addWidget(QLabel("Address Line 2"), 12, 0)
        editor_grid.addWidget(self._customer_address_2_input, 12, 1)
        editor_grid.addWidget(QLabel("Address Line 3"), 13, 0)
        editor_grid.addWidget(self._customer_address_3_input, 13, 1)
        editor_grid.addWidget(QLabel("Preferences JSON"), 14, 0)
        editor_grid.addWidget(self._customer_preferences_input, 14, 1)
        editor_grid.addWidget(QLabel("Description"), 15, 0)
        editor_grid.addWidget(self._customer_description_input, 15, 1)
        editor_grid.addWidget(self._customer_marketing_checkbox, 16, 1)
        editor_grid.addWidget(self._customer_sms_checkbox, 17, 1)
        editor_grid.addWidget(self._customer_email_checkbox, 18, 1)
        editor_grid.addWidget(self._customer_walkin_checkbox, 19, 1)
        editor_grid.addWidget(self._customer_active_checkbox, 20, 1)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_customer_editor)
        save_button.clicked.connect(self._save_customer)
        delete_button.clicked.connect(self._delete_customer)
        refresh_editor_button.clicked.connect(self.refresh_customers)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_editor_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(editor_grid)
        editor_layout.addStretch(1)
        editor_layout.addLayout(action_layout)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([960, 420])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_segments_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._segment_table = QTableWidget(0, 6)
        self._segment_table.setHorizontalHeaderLabels(
            ["Code", "Name", "Type", "Active", "Members", "Display Order"]
        )
        self._segment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._segment_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._segment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._segment_table.verticalHeader().setVisible(False)
        self._segment_table.setAlternatingRowColors(True)
        self._segment_table.itemSelectionChanged.connect(self._on_segment_row_selected)

        table_wrap = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._segment_table)
        table_wrap.setLayout(table_layout)

        editor_box = QGroupBox("Customer Segment Editor")
        form_layout = QFormLayout()
        self._segment_code_input = QLineEdit()
        self._segment_name_input = QLineEdit()
        self._segment_type_input = QComboBox()
        self._segment_type_input.addItems(
            ["VIP", "NEW_CUSTOMER", "FREQUENT_BUYER", "HIGH_VALUE", "INACTIVE", "BIRTHDAY", "CUSTOM"]
        )
        self._segment_description_input = QPlainTextEdit()
        self._segment_description_input.setMinimumHeight(80)
        self._segment_criteria_input = QPlainTextEdit()
        self._segment_criteria_input.setMinimumHeight(80)
        self._segment_display_order_input = QSpinBox()
        self._segment_display_order_input.setRange(0, 100_000)
        self._segment_color_input = QLineEdit()
        self._segment_icon_input = QLineEdit()
        self._segment_active_checkbox = QCheckBox("Active")
        self._segment_active_checkbox.setChecked(True)
        form_layout.addRow("Code", self._segment_code_input)
        form_layout.addRow("Name", self._segment_name_input)
        form_layout.addRow("Segment Type", self._segment_type_input)
        form_layout.addRow("Description", self._segment_description_input)
        form_layout.addRow("Criteria JSON", self._segment_criteria_input)
        form_layout.addRow("Display Order", self._segment_display_order_input)
        form_layout.addRow("Color", self._segment_color_input)
        form_layout.addRow("Icon", self._segment_icon_input)
        form_layout.addRow(self._segment_active_checkbox)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_segment_editor)
        save_button.clicked.connect(self._save_segment)
        delete_button.clicked.connect(self._delete_segment)
        refresh_button.clicked.connect(self.refresh_segments)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form_layout)
        editor_layout.addStretch(1)
        editor_layout.addLayout(action_layout)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(table_wrap)
        splitter.addWidget(editor_box)
        splitter.setSizes([960, 420])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_segment_members_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._member_customer_filter_combo = QComboBox()
        self._member_customer_filter_combo.currentIndexChanged.connect(self.refresh_segment_members)
        self._member_segment_filter_combo = QComboBox()
        self._member_segment_filter_combo.currentIndexChanged.connect(self.refresh_segment_members)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_segment_members)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._member_customer_filter_combo)
        filter_layout.addWidget(QLabel("Segment"))
        filter_layout.addWidget(self._member_segment_filter_combo)
        filter_layout.addWidget(refresh_button)
        left_layout.addLayout(filter_layout)

        self._member_table = QTableWidget(0, 5)
        self._member_table.setHorizontalHeaderLabels(
            ["Customer", "Segment", "Assigned Date", "Assigned By", "Active"]
        )
        self._member_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._member_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._member_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._member_table.verticalHeader().setVisible(False)
        self._member_table.setAlternatingRowColors(True)
        self._member_table.itemSelectionChanged.connect(self._on_member_row_selected)
        left_layout.addWidget(self._member_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Segment Member Editor")
        form_layout = QFormLayout()
        self._member_customer_combo = QComboBox()
        self._member_segment_combo = QComboBox()
        self._member_assigned_date_input = QLineEdit()
        self._member_assigned_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._member_assigned_by_input = QLineEdit()
        self._member_reason_input = QPlainTextEdit()
        self._member_reason_input.setMinimumHeight(70)
        self._member_active_checkbox = QCheckBox("Active")
        self._member_active_checkbox.setChecked(True)
        form_layout.addRow("Customer", self._member_customer_combo)
        form_layout.addRow("Segment", self._member_segment_combo)
        form_layout.addRow("Assigned Date", self._member_assigned_date_input)
        form_layout.addRow("Assigned By", self._member_assigned_by_input)
        form_layout.addRow("Assignment Reason", self._member_reason_input)
        form_layout.addRow(self._member_active_checkbox)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_member_editor)
        save_button.clicked.connect(self._save_member)
        delete_button.clicked.connect(self._delete_member)
        refresh_editor_button.clicked.connect(self.refresh_segment_members)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_editor_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form_layout)
        editor_layout.addStretch(1)
        editor_layout.addLayout(action_layout)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([960, 420])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_loyalty_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._loyalty_customer_filter_combo = QComboBox()
        self._loyalty_customer_filter_combo.currentIndexChanged.connect(self.refresh_loyalties)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_loyalties)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._loyalty_customer_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._loyalty_table = QTableWidget(0, 8)
        self._loyalty_table.setHorizontalHeaderLabels(
            ["Customer", "Program", "Tier", "Card Number", "Available", "Lifetime", "Total Spent", "Active"]
        )
        self._loyalty_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._loyalty_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._loyalty_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._loyalty_table.verticalHeader().setVisible(False)
        self._loyalty_table.setAlternatingRowColors(True)
        self._loyalty_table.itemSelectionChanged.connect(self._on_loyalty_row_selected)
        left_layout.addWidget(self._loyalty_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Customer Loyalty Editor")
        form_layout = QFormLayout()
        self._loyalty_customer_combo = QComboBox()
        self._loyalty_program_combo = QComboBox()
        self._loyalty_program_combo.currentIndexChanged.connect(self._reload_loyalty_tier_combos)
        self._loyalty_tier_combo = QComboBox()
        self._loyalty_card_number_input = QLineEdit()
        self._loyalty_total_points_input = QSpinBox()
        self._loyalty_total_points_input.setRange(-10_000_000, 10_000_000)
        self._loyalty_available_points_input = QSpinBox()
        self._loyalty_available_points_input.setRange(-10_000_000, 10_000_000)
        self._loyalty_lifetime_points_input = QSpinBox()
        self._loyalty_lifetime_points_input.setRange(0, 10_000_000)
        self._loyalty_points_to_expire_input = QSpinBox()
        self._loyalty_points_to_expire_input.setRange(0, 10_000_000)
        self._loyalty_points_expiry_date_input = QLineEdit()
        self._loyalty_points_expiry_date_input.setPlaceholderText("YYYY-MM-DD")
        self._loyalty_enrollment_date_input = QLineEdit()
        self._loyalty_enrollment_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._loyalty_last_activity_date_input = QLineEdit()
        self._loyalty_last_activity_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._loyalty_total_purchases_input = QSpinBox()
        self._loyalty_total_purchases_input.setRange(0, 100_000_000)
        self._loyalty_total_spent_input = QLineEdit()
        self._loyalty_annual_spent_input = QLineEdit()
        self._loyalty_active_checkbox = QCheckBox("Active")
        self._loyalty_active_checkbox.setChecked(True)
        form_layout.addRow("Customer", self._loyalty_customer_combo)
        form_layout.addRow("Program", self._loyalty_program_combo)
        form_layout.addRow("Tier", self._loyalty_tier_combo)
        form_layout.addRow("Card Number", self._loyalty_card_number_input)
        form_layout.addRow("Total Points", self._loyalty_total_points_input)
        form_layout.addRow("Available Points", self._loyalty_available_points_input)
        form_layout.addRow("Lifetime Points", self._loyalty_lifetime_points_input)
        form_layout.addRow("Points to Expire", self._loyalty_points_to_expire_input)
        form_layout.addRow("Points Expiry Date", self._loyalty_points_expiry_date_input)
        form_layout.addRow("Enrollment Date", self._loyalty_enrollment_date_input)
        form_layout.addRow("Last Activity Date", self._loyalty_last_activity_date_input)
        form_layout.addRow("Total Purchases", self._loyalty_total_purchases_input)
        form_layout.addRow("Total Spent", self._loyalty_total_spent_input)
        form_layout.addRow("Annual Spent", self._loyalty_annual_spent_input)
        form_layout.addRow(self._loyalty_active_checkbox)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_loyalty_editor)
        save_button.clicked.connect(self._save_loyalty)
        delete_button.clicked.connect(self._delete_loyalty)
        refresh_editor_button.clicked.connect(self.refresh_loyalties)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_editor_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form_layout)
        editor_layout.addStretch(1)
        editor_layout.addLayout(action_layout)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([960, 420])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_point_transactions_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._transaction_customer_filter_combo = QComboBox()
        self._transaction_customer_filter_combo.currentIndexChanged.connect(self.refresh_point_transactions)
        self._transaction_loyalty_filter_combo = QComboBox()
        self._transaction_loyalty_filter_combo.currentIndexChanged.connect(self.refresh_point_transactions)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_point_transactions)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._transaction_customer_filter_combo)
        filter_layout.addWidget(QLabel("Loyalty"))
        filter_layout.addWidget(self._transaction_loyalty_filter_combo)
        filter_layout.addWidget(refresh_button)
        left_layout.addLayout(filter_layout)

        self._transaction_table = QTableWidget(0, 8)
        self._transaction_table.setHorizontalHeaderLabels(
            ["Customer", "Type", "Points", "Balance", "Date", "Store", "Cashier", "Reference"]
        )
        self._transaction_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._transaction_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._transaction_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._transaction_table.verticalHeader().setVisible(False)
        self._transaction_table.setAlternatingRowColors(True)
        self._transaction_table.itemSelectionChanged.connect(self._on_transaction_row_selected)
        left_layout.addWidget(self._transaction_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Loyalty Point Transaction Editor")
        form_layout = QFormLayout()
        self._transaction_loyalty_combo = QComboBox()
        self._transaction_customer_combo = QComboBox()
        self._transaction_type_combo = QComboBox()
        self._transaction_type_combo.addItems(
            ["EARNED", "REDEEMED", "EXPIRED", "ADJUSTED", "BONUS", "WELCOME", "BIRTHDAY", "REFUND"]
        )
        self._transaction_points_amount_input = QSpinBox()
        self._transaction_points_amount_input.setRange(-10_000_000, 10_000_000)
        self._transaction_balance_after_input = QLineEdit()
        self._transaction_date_input = QLineEdit()
        self._transaction_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._transaction_expiry_date_input = QLineEdit()
        self._transaction_expiry_date_input.setPlaceholderText("YYYY-MM-DD")
        self._transaction_store_combo = QComboBox()
        self._transaction_cashier_combo = QComboBox()
        self._transaction_head_combo = QComboBox()
        self._transaction_reference_input = QLineEdit()
        self._transaction_description_input = QLineEdit()
        self._transaction_notes_input = QPlainTextEdit()
        self._transaction_notes_input.setMinimumHeight(70)
        form_layout.addRow("Customer Loyalty", self._transaction_loyalty_combo)
        form_layout.addRow("Customer", self._transaction_customer_combo)
        form_layout.addRow("Type", self._transaction_type_combo)
        form_layout.addRow("Points Amount", self._transaction_points_amount_input)
        form_layout.addRow("Balance After", self._transaction_balance_after_input)
        form_layout.addRow("Transaction Date", self._transaction_date_input)
        form_layout.addRow("Expiry Date", self._transaction_expiry_date_input)
        form_layout.addRow("Store", self._transaction_store_combo)
        form_layout.addRow("Cashier", self._transaction_cashier_combo)
        form_layout.addRow("Transaction Head", self._transaction_head_combo)
        form_layout.addRow("Reference Number", self._transaction_reference_input)
        form_layout.addRow("Description", self._transaction_description_input)
        form_layout.addRow("Notes", self._transaction_notes_input)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_transaction_editor)
        save_button.clicked.connect(self._save_transaction)
        delete_button.clicked.connect(self._delete_transaction)
        refresh_editor_button.clicked.connect(self.refresh_point_transactions)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_editor_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form_layout)
        editor_layout.addStretch(1)
        editor_layout.addLayout(action_layout)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([960, 420])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_operations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self._operations_segment_filter_combo = QComboBox()
        self._operations_segment_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        self._operations_active_filter_combo = QComboBox()
        self._operations_active_filter_combo.addItem("All", None)
        self._operations_active_filter_combo.addItem("Active Only", True)
        self._operations_active_filter_combo.addItem("Inactive Only", False)
        self._operations_active_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_operations)
        open_window_button = QPushButton("Open Operations Window")
        open_window_button.clicked.connect(self._open_customer_operations_window)
        open_loyalty_management_button = QPushButton("Open Loyalty Management")
        open_loyalty_management_button.clicked.connect(self._open_loyalty_management_window)
        open_loyalty_operations_button = QPushButton("Open Loyalty Operations")
        open_loyalty_operations_button.clicked.connect(self._open_loyalty_operations_window)
        filter_layout.addWidget(QLabel("Segment"))
        filter_layout.addWidget(self._operations_segment_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._operations_active_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        filter_layout.addWidget(open_loyalty_management_button)
        filter_layout.addWidget(open_loyalty_operations_button)
        filter_layout.addWidget(open_window_button)
        layout.addLayout(filter_layout)

        self._operations_table = QTableWidget(0, 10)
        self._operations_table.setHorizontalHeaderLabels(
            [
                "Customer",
                "Phone",
                "Email",
                "Segments",
                "Program",
                "Tier",
                "Available Points",
                "Lifetime Points",
                "Point Txn Count",
                "Last Point Txn",
            ]
        )
        self._operations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._operations_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._operations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._operations_table.verticalHeader().setVisible(False)
        self._operations_table.setAlternatingRowColors(True)
        layout.addWidget(self._operations_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self.refresh_customers()
        self.refresh_segments()
        self.refresh_segment_members()
        self.refresh_loyalties()
        self.refresh_point_transactions()
        self.refresh_operations()

    def refresh_customers(self) -> None:
        self._reload_lookup_combos()
        search_value = self._customer_search_input.text().strip()
        self._customers = self.service.list_customers(search_text=search_value)
        self._customer_table.setRowCount(len(self._customers))
        for row_index, customer in enumerate(self._customers):
            values = [
                customer.name,
                customer.last_name,
                customer.phone_number,
                customer.email_address,
                customer.date_of_birth.isoformat() if customer.date_of_birth else "",
                "Yes" if customer.is_active else "No",
                "Yes" if customer.is_walkin else "No",
                str(customer.segment_count),
                str(customer.loyalty_available_points),
                customer.loyalty_program_name,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, customer.id)
                self._customer_table.setItem(row_index, col, item)
        self._customer_table.resizeColumnsToContents()

    def refresh_segments(self) -> None:
        self._segments = self.service.list_customer_segments()
        self._segment_table.setRowCount(len(self._segments))
        for row_index, segment in enumerate(self._segments):
            values = [
                segment.code,
                segment.name,
                segment.segment_type,
                "Yes" if segment.is_active else "No",
                str(segment.customer_count),
                str(segment.display_order),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, segment.id)
                self._segment_table.setItem(row_index, col, item)
        self._segment_table.resizeColumnsToContents()
        self._reload_segment_lookup_combos()

    def refresh_segment_members(self) -> None:
        self._members = self.service.list_customer_segment_members(
            customer_id=self._member_customer_filter_combo.currentData(),
            segment_id=self._member_segment_filter_combo.currentData(),
        )
        self._member_table.setRowCount(len(self._members))
        for row_index, member in enumerate(self._members):
            values = [
                member.customer_label,
                member.customer_segment_label,
                member.assigned_date.isoformat(sep=" ") if member.assigned_date else "",
                member.assigned_by,
                "Yes" if member.is_active else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, member.id)
                self._member_table.setItem(row_index, col, item)
        self._member_table.resizeColumnsToContents()

    def refresh_loyalties(self) -> None:
        self._loyalties = self.service.list_customer_loyalties(
            customer_id=self._loyalty_customer_filter_combo.currentData()
        )
        self._loyalty_table.setRowCount(len(self._loyalties))
        for row_index, loyalty in enumerate(self._loyalties):
            values = [
                loyalty.customer_label,
                loyalty.loyalty_program_label,
                loyalty.loyalty_tier_label,
                loyalty.loyalty_card_number,
                str(loyalty.available_points),
                str(loyalty.lifetime_points),
                self._format_amount(loyalty.total_spent),
                "Yes" if loyalty.is_active else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, loyalty.id)
                self._loyalty_table.setItem(row_index, col, item)
        self._loyalty_table.resizeColumnsToContents()
        self._reload_loyalty_lookup_combos()

    def refresh_point_transactions(self) -> None:
        self._transactions = self.service.list_loyalty_point_transactions(
            customer_id=self._transaction_customer_filter_combo.currentData(),
            customer_loyalty_id=self._transaction_loyalty_filter_combo.currentData(),
        )
        self._transaction_table.setRowCount(len(self._transactions))
        for row_index, row in enumerate(self._transactions):
            values = [
                row.customer_label,
                row.transaction_type,
                str(row.points_amount),
                str(row.balance_after),
                row.transaction_date.isoformat(sep=" ") if row.transaction_date else "",
                row.store_label,
                row.cashier_label,
                row.reference_number,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._transaction_table.setItem(row_index, col, item)
        self._transaction_table.resizeColumnsToContents()

    def refresh_operations(self) -> None:
        active_filter_value = self._operations_active_filter_combo.currentData()
        self._operations = self.service.list_customer_operations(
            segment_id=self._operations_segment_filter_combo.currentData(),
            active_only=active_filter_value is True,
        )
        if active_filter_value is False:
            self._operations = [row for row in self._operations if not row.is_active]
        self._operations_table.setRowCount(len(self._operations))
        for row_index, row in enumerate(self._operations):
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
                else "",
            ]
            for col, value in enumerate(values):
                self._operations_table.setItem(row_index, col, QTableWidgetItem(value))
        self._operations_table.resizeColumnsToContents()

    def _on_customer_row_selected(self) -> None:
        selected_items = self._customer_table.selectedItems()
        if not selected_items:
            return
        customer_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._customers if x.id == customer_id), None)
        if selected is None:
            return
        self._selected_customer_id = selected.id
        self._customer_name_input.setText(selected.name)
        self._customer_last_name_input.setText(selected.last_name)
        self._customer_phone_input.setText(selected.phone_number)
        self._customer_phone_normalized_input.setText(selected.phone_normalized)
        self._customer_email_input.setText(selected.email_address)
        self._customer_dob_input.setText(selected.date_of_birth.isoformat() if selected.date_of_birth else "")
        self._customer_gender_combo.setCurrentText(selected.gender)
        self._customer_national_id_input.setText(selected.national_id)
        self._customer_tax_id_input.setText(selected.tax_id)
        self._customer_registration_source_input.setText(selected.registration_source)
        self._customer_zip_code_input.setText(selected.zip_code)
        self._customer_address_1_input.setText(selected.address_line_1)
        self._customer_address_2_input.setText(selected.address_line_2)
        self._customer_address_3_input.setText(selected.address_line_3)
        self._customer_preferences_input.setPlainText(selected.preferences_json)
        self._customer_description_input.setPlainText(selected.description)
        self._customer_marketing_checkbox.setChecked(selected.marketing_consent)
        self._customer_sms_checkbox.setChecked(selected.sms_consent)
        self._customer_email_checkbox.setChecked(selected.email_consent)
        self._customer_walkin_checkbox.setChecked(selected.is_walkin)
        self._customer_active_checkbox.setChecked(selected.is_active)

    def _on_segment_row_selected(self) -> None:
        selected_items = self._segment_table.selectedItems()
        if not selected_items:
            return
        segment_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._segments if x.id == segment_id), None)
        if selected is None:
            return
        self._selected_segment_id = selected.id
        self._segment_code_input.setText(selected.code)
        self._segment_name_input.setText(selected.name)
        self._segment_type_input.setCurrentText(selected.segment_type)
        self._segment_description_input.setPlainText(selected.description)
        self._segment_criteria_input.setPlainText(selected.criteria_json)
        self._segment_display_order_input.setValue(selected.display_order)
        self._segment_color_input.setText(selected.color_code)
        self._segment_icon_input.setText(selected.icon)
        self._segment_active_checkbox.setChecked(selected.is_active)

    def _on_member_row_selected(self) -> None:
        selected_items = self._member_table.selectedItems()
        if not selected_items:
            return
        member_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._members if x.id == member_id), None)
        if selected is None:
            return
        self._selected_member_id = selected.id
        self._member_customer_combo.setCurrentIndex(self._member_customer_combo.findData(selected.customer_id))
        self._member_segment_combo.setCurrentIndex(
            self._member_segment_combo.findData(selected.customer_segment_id)
        )
        self._member_assigned_date_input.setText(
            selected.assigned_date.strftime("%Y-%m-%d %H:%M") if selected.assigned_date else ""
        )
        self._member_assigned_by_input.setText(selected.assigned_by)
        self._member_reason_input.setPlainText(selected.assignment_reason)
        self._member_active_checkbox.setChecked(selected.is_active)

    def _on_loyalty_row_selected(self) -> None:
        selected_items = self._loyalty_table.selectedItems()
        if not selected_items:
            return
        loyalty_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._loyalties if x.id == loyalty_id), None)
        if selected is None:
            return
        self._selected_loyalty_id = selected.id
        self._loyalty_customer_combo.setCurrentIndex(self._loyalty_customer_combo.findData(selected.customer_id))
        self._loyalty_program_combo.setCurrentIndex(
            self._loyalty_program_combo.findData(selected.loyalty_program_id)
        )
        self._reload_loyalty_tier_combos()
        self._loyalty_tier_combo.setCurrentIndex(self._loyalty_tier_combo.findData(selected.loyalty_tier_id))
        self._loyalty_card_number_input.setText(selected.loyalty_card_number)
        self._loyalty_total_points_input.setValue(selected.total_points)
        self._loyalty_available_points_input.setValue(selected.available_points)
        self._loyalty_lifetime_points_input.setValue(selected.lifetime_points)
        self._loyalty_points_to_expire_input.setValue(selected.points_to_expire)
        self._loyalty_points_expiry_date_input.setText(
            selected.points_expiry_date.isoformat() if selected.points_expiry_date else ""
        )
        self._loyalty_enrollment_date_input.setText(
            selected.enrollment_date.strftime("%Y-%m-%d %H:%M") if selected.enrollment_date else ""
        )
        self._loyalty_last_activity_date_input.setText(
            selected.last_activity_date.strftime("%Y-%m-%d %H:%M") if selected.last_activity_date else ""
        )
        self._loyalty_total_purchases_input.setValue(selected.total_purchases)
        self._loyalty_total_spent_input.setText(self._format_amount(selected.total_spent))
        self._loyalty_annual_spent_input.setText(self._format_amount(selected.annual_spent))
        self._loyalty_active_checkbox.setChecked(selected.is_active)

    def _on_transaction_row_selected(self) -> None:
        selected_items = self._transaction_table.selectedItems()
        if not selected_items:
            return
        transaction_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._transactions if x.id == transaction_id), None)
        if selected is None:
            return
        self._selected_transaction_id = selected.id
        self._transaction_loyalty_combo.setCurrentIndex(
            self._transaction_loyalty_combo.findData(selected.customer_loyalty_id)
        )
        self._transaction_customer_combo.setCurrentIndex(
            self._transaction_customer_combo.findData(selected.customer_id)
        )
        self._transaction_type_combo.setCurrentText(selected.transaction_type)
        self._transaction_points_amount_input.setValue(selected.points_amount)
        self._transaction_balance_after_input.setText(str(selected.balance_after))
        self._transaction_date_input.setText(
            selected.transaction_date.strftime("%Y-%m-%d %H:%M") if selected.transaction_date else ""
        )
        self._transaction_expiry_date_input.setText(
            selected.expiry_date.isoformat() if selected.expiry_date else ""
        )
        self._transaction_store_combo.setCurrentIndex(
            self._transaction_store_combo.findData(selected.store_id)
        )
        self._transaction_cashier_combo.setCurrentIndex(
            self._transaction_cashier_combo.findData(selected.cashier_id)
        )
        self._transaction_head_combo.setCurrentIndex(
            self._transaction_head_combo.findData(selected.transaction_head_id)
        )
        self._transaction_reference_input.setText(selected.reference_number)
        self._transaction_description_input.setText(selected.description)
        self._transaction_notes_input.setPlainText(selected.notes)

    def _save_customer(self) -> None:
        payload = {
            "name": self._customer_name_input.text(),
            "last_name": self._customer_last_name_input.text(),
            "phone_number": self._customer_phone_input.text(),
            "phone_normalized": self._customer_phone_normalized_input.text(),
            "email_address": self._customer_email_input.text(),
            "date_of_birth": self._customer_dob_input.text(),
            "gender": self._customer_gender_combo.currentText(),
            "national_id": self._customer_national_id_input.text(),
            "tax_id": self._customer_tax_id_input.text(),
            "registration_source": self._customer_registration_source_input.text(),
            "zip_code": self._customer_zip_code_input.text(),
            "address_line_1": self._customer_address_1_input.text(),
            "address_line_2": self._customer_address_2_input.text(),
            "address_line_3": self._customer_address_3_input.text(),
            "preferences_json": self._customer_preferences_input.toPlainText(),
            "description": self._customer_description_input.toPlainText(),
            "marketing_consent": self._customer_marketing_checkbox.isChecked(),
            "sms_consent": self._customer_sms_checkbox.isChecked(),
            "email_consent": self._customer_email_checkbox.isChecked(),
            "is_walkin": self._customer_walkin_checkbox.isChecked(),
            "is_active": self._customer_active_checkbox.isChecked(),
        }
        result = self.service.save_customer(payload=payload, customer_id=self._selected_customer_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_customer_editor()

    def _delete_customer(self) -> None:
        if not self._selected_customer_id:
            self._set_status(False, "Please select a customer record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Customer",
            "Selected customer will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_customer(self._selected_customer_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_customer_editor()

    def _save_segment(self) -> None:
        payload = {
            "code": self._segment_code_input.text(),
            "name": self._segment_name_input.text(),
            "segment_type": self._segment_type_input.currentText(),
            "description": self._segment_description_input.toPlainText(),
            "criteria_json": self._segment_criteria_input.toPlainText(),
            "display_order": self._segment_display_order_input.value(),
            "color_code": self._segment_color_input.text(),
            "icon": self._segment_icon_input.text(),
            "is_active": self._segment_active_checkbox.isChecked(),
        }
        result = self.service.save_customer_segment(payload=payload, segment_id=self._selected_segment_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_segment_editor()

    def _delete_segment(self) -> None:
        if not self._selected_segment_id:
            self._set_status(False, "Please select a customer segment record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Customer Segment",
            "Selected customer segment will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_customer_segment(self._selected_segment_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_segment_editor()

    def _save_member(self) -> None:
        payload = {
            "customer_id": self._member_customer_combo.currentData(),
            "customer_segment_id": self._member_segment_combo.currentData(),
            "assigned_date": self._member_assigned_date_input.text(),
            "assigned_by": self._member_assigned_by_input.text(),
            "assignment_reason": self._member_reason_input.toPlainText(),
            "is_active": self._member_active_checkbox.isChecked(),
        }
        result = self.service.save_customer_segment_member(
            payload=payload,
            member_id=self._selected_member_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_segment_members()
            self._clear_member_editor()

    def _delete_member(self) -> None:
        if not self._selected_member_id:
            self._set_status(False, "Please select a segment member record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Segment Member",
            "Selected segment member will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_customer_segment_member(self._selected_member_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_segment_members()
            self._clear_member_editor()

    def _save_loyalty(self) -> None:
        payload = {
            "customer_id": self._loyalty_customer_combo.currentData(),
            "loyalty_program_id": self._loyalty_program_combo.currentData(),
            "loyalty_tier_id": self._loyalty_tier_combo.currentData(),
            "loyalty_card_number": self._loyalty_card_number_input.text(),
            "total_points": self._loyalty_total_points_input.value(),
            "available_points": self._loyalty_available_points_input.value(),
            "lifetime_points": self._loyalty_lifetime_points_input.value(),
            "points_to_expire": self._loyalty_points_to_expire_input.value(),
            "points_expiry_date": self._loyalty_points_expiry_date_input.text(),
            "enrollment_date": self._loyalty_enrollment_date_input.text(),
            "last_activity_date": self._loyalty_last_activity_date_input.text(),
            "total_purchases": self._loyalty_total_purchases_input.value(),
            "total_spent": self._loyalty_total_spent_input.text(),
            "annual_spent": self._loyalty_annual_spent_input.text(),
            "is_active": self._loyalty_active_checkbox.isChecked(),
        }
        result = self.service.save_customer_loyalty(payload=payload, loyalty_id=self._selected_loyalty_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_loyalty_editor()

    def _delete_loyalty(self) -> None:
        if not self._selected_loyalty_id:
            self._set_status(False, "Please select a customer loyalty record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Customer Loyalty",
            "Selected customer loyalty will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_customer_loyalty(self._selected_loyalty_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_loyalty_editor()

    def _save_transaction(self) -> None:
        loyalty_id = self._transaction_loyalty_combo.currentData()
        selected_loyalty = next((x for x in self._loyalties if x.id == loyalty_id), None)
        payload = {
            "customer_loyalty_id": loyalty_id,
            "customer_id": self._transaction_customer_combo.currentData(),
            "transaction_type": self._transaction_type_combo.currentText(),
            "points_amount": self._transaction_points_amount_input.value(),
            "balance_after": self._transaction_balance_after_input.text(),
            "transaction_date": self._transaction_date_input.text(),
            "expiry_date": self._transaction_expiry_date_input.text(),
            "store_id": self._transaction_store_combo.currentData(),
            "cashier_id": self._transaction_cashier_combo.currentData(),
            "transaction_head_id": self._transaction_head_combo.currentData(),
            "reference_number": self._transaction_reference_input.text(),
            "description": self._transaction_description_input.text(),
            "notes": self._transaction_notes_input.toPlainText(),
            "available_points_hint": selected_loyalty.available_points if selected_loyalty else 0,
        }
        result = self.service.save_loyalty_point_transaction(
            payload=payload,
            transaction_id=self._selected_transaction_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_transaction_editor()

    def _delete_transaction(self) -> None:
        if not self._selected_transaction_id:
            self._set_status(False, "Please select a loyalty point transaction record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Loyalty Point Transaction",
            "Selected loyalty point transaction will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_loyalty_point_transaction(self._selected_transaction_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_transaction_editor()

    def _clear_customer_editor(self) -> None:
        self._selected_customer_id = None
        self._customer_table.clearSelection()
        self._customer_name_input.clear()
        self._customer_last_name_input.clear()
        self._customer_phone_input.clear()
        self._customer_phone_normalized_input.clear()
        self._customer_email_input.clear()
        self._customer_dob_input.clear()
        self._customer_gender_combo.setCurrentIndex(0)
        self._customer_national_id_input.clear()
        self._customer_tax_id_input.clear()
        self._customer_registration_source_input.clear()
        self._customer_zip_code_input.clear()
        self._customer_address_1_input.clear()
        self._customer_address_2_input.clear()
        self._customer_address_3_input.clear()
        self._customer_preferences_input.clear()
        self._customer_description_input.clear()
        self._customer_marketing_checkbox.setChecked(False)
        self._customer_sms_checkbox.setChecked(False)
        self._customer_email_checkbox.setChecked(False)
        self._customer_walkin_checkbox.setChecked(False)
        self._customer_active_checkbox.setChecked(True)

    def _clear_segment_editor(self) -> None:
        self._selected_segment_id = None
        self._segment_table.clearSelection()
        self._segment_code_input.clear()
        self._segment_name_input.clear()
        self._segment_type_input.setCurrentIndex(0)
        self._segment_description_input.clear()
        self._segment_criteria_input.clear()
        self._segment_display_order_input.setValue(0)
        self._segment_color_input.clear()
        self._segment_icon_input.clear()
        self._segment_active_checkbox.setChecked(True)

    def _clear_member_editor(self) -> None:
        self._selected_member_id = None
        self._member_table.clearSelection()
        self._member_customer_combo.setCurrentIndex(0)
        self._member_segment_combo.setCurrentIndex(0)
        self._member_assigned_date_input.clear()
        self._member_assigned_by_input.clear()
        self._member_reason_input.clear()
        self._member_active_checkbox.setChecked(True)

    def _clear_loyalty_editor(self) -> None:
        self._selected_loyalty_id = None
        self._loyalty_table.clearSelection()
        self._loyalty_customer_combo.setCurrentIndex(0)
        self._loyalty_program_combo.setCurrentIndex(0)
        self._reload_loyalty_tier_combos()
        self._loyalty_tier_combo.setCurrentIndex(0)
        self._loyalty_card_number_input.clear()
        self._loyalty_total_points_input.setValue(0)
        self._loyalty_available_points_input.setValue(0)
        self._loyalty_lifetime_points_input.setValue(0)
        self._loyalty_points_to_expire_input.setValue(0)
        self._loyalty_points_expiry_date_input.clear()
        self._loyalty_enrollment_date_input.clear()
        self._loyalty_last_activity_date_input.clear()
        self._loyalty_total_purchases_input.setValue(0)
        self._loyalty_total_spent_input.clear()
        self._loyalty_annual_spent_input.clear()
        self._loyalty_active_checkbox.setChecked(True)

    def _clear_transaction_editor(self) -> None:
        self._selected_transaction_id = None
        self._transaction_table.clearSelection()
        self._transaction_loyalty_combo.setCurrentIndex(0)
        self._transaction_customer_combo.setCurrentIndex(0)
        self._transaction_type_combo.setCurrentIndex(0)
        self._transaction_points_amount_input.setValue(0)
        self._transaction_balance_after_input.clear()
        self._transaction_date_input.clear()
        self._transaction_expiry_date_input.clear()
        self._transaction_store_combo.setCurrentIndex(0)
        self._transaction_cashier_combo.setCurrentIndex(0)
        self._transaction_head_combo.setCurrentIndex(0)
        self._transaction_reference_input.clear()
        self._transaction_description_input.clear()
        self._transaction_notes_input.clear()

    def _open_customer_operations_window(self) -> None:
        if self._customer_operations_form is None:
            self._customer_operations_form = CustomerOperationsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._customer_operations_form.show()
        self._customer_operations_form.raise_()
        self._customer_operations_form.activateWindow()

    def _open_loyalty_management_window(self) -> None:
        if self._loyalty_management_form is None:
            self._loyalty_management_form = LoyaltyManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._loyalty_management_form.show()
        self._loyalty_management_form.raise_()
        self._loyalty_management_form.activateWindow()

    def _open_loyalty_operations_window(self) -> None:
        if self._loyalty_operations_form is None:
            self._loyalty_operations_form = LoyaltyOperationsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._loyalty_operations_form.show()
        self._loyalty_operations_form.raise_()
        self._loyalty_operations_form.activateWindow()

    def _reload_lookup_combos(self) -> None:
        customer_items = [(item.id, item.label) for item in self.service.list_customer_lookups()]
        segment_items = [(item.id, item.label) for item in self.service.list_customer_segment_lookups()]
        loyalty_program_items = [(item.id, item.label) for item in self.service.list_loyalty_program_lookups()]
        loyalty_items = [(item.id, item.label) for item in self.service.list_customer_loyalty_lookups()]
        store_items = [(item.id, item.label) for item in self.service.list_store_lookups()]
        cashier_items = [(item.id, item.label) for item in self.service.list_cashier_lookups()]
        txn_head_items = [(item.id, item.label) for item in self.service.list_transaction_head_lookups()]

        self._reload_combo(self._member_customer_combo, customer_items, include_empty=False, empty_label="")
        self._reload_combo(self._member_customer_filter_combo, customer_items, include_empty=True, empty_label="All")
        self._reload_combo(self._member_segment_combo, segment_items, include_empty=False, empty_label="")
        self._reload_combo(self._member_segment_filter_combo, segment_items, include_empty=True, empty_label="All")
        self._reload_combo(self._loyalty_customer_combo, customer_items, include_empty=False, empty_label="")
        self._reload_combo(self._loyalty_customer_filter_combo, customer_items, include_empty=True, empty_label="All")
        self._reload_combo(self._loyalty_program_combo, loyalty_program_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._transaction_loyalty_combo,
            loyalty_items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo(
            self._transaction_loyalty_filter_combo,
            loyalty_items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo(
            self._transaction_customer_combo,
            customer_items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo(
            self._transaction_customer_filter_combo,
            customer_items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo(self._transaction_store_combo, store_items, include_empty=True, empty_label="None")
        self._reload_combo(self._transaction_cashier_combo, cashier_items, include_empty=True, empty_label="None")
        self._reload_combo(
            self._transaction_head_combo,
            txn_head_items,
            include_empty=True,
            empty_label="None",
        )
        self._reload_combo(
            self._operations_segment_filter_combo,
            segment_items,
            include_empty=True,
            empty_label="All",
        )

        self._reload_loyalty_tier_combos()

    def _reload_segment_lookup_combos(self) -> None:
        segment_items = [(item.id, item.label) for item in self.service.list_customer_segment_lookups()]
        self._reload_combo(self._member_segment_combo, segment_items, include_empty=False, empty_label="")
        self._reload_combo(self._member_segment_filter_combo, segment_items, include_empty=True, empty_label="All")
        self._reload_combo(
            self._operations_segment_filter_combo,
            segment_items,
            include_empty=True,
            empty_label="All",
        )

    def _reload_loyalty_lookup_combos(self) -> None:
        loyalty_items = [(item.id, item.label) for item in self.service.list_customer_loyalty_lookups()]
        self._reload_combo(
            self._transaction_loyalty_combo,
            loyalty_items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo(
            self._transaction_loyalty_filter_combo,
            loyalty_items,
            include_empty=True,
            empty_label="All",
        )

    def _reload_loyalty_tier_combos(self) -> None:
        selected_program_id = self._loyalty_program_combo.currentData()
        tier_items = [
            (item.id, item.label)
            for item in self.service.list_loyalty_tier_lookups(program_id=selected_program_id)
        ]
        self._reload_combo(self._loyalty_tier_combo, tier_items, include_empty=True, empty_label="None")

    def _set_status(self, success: bool, message: str) -> None:
        self._status_label.setStyleSheet("color: #166534;" if success else "color: #b91c1c;")
        self._status_label.setText(message)

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

    @staticmethod
    def _format_amount(value: Decimal | None) -> str:
        amount = Decimal("0") if value is None else Decimal(str(value))
        return f"{amount:.2f}"
