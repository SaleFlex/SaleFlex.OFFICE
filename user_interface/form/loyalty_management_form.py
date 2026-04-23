"""
Loyalty management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from decimal import Decimal
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
from office.service.customer_management_service import (
    CustomerLoyaltyView,
    CustomerManagementService,
    LoyaltyPointTransactionView,
)
from office.service.loyalty_management_service import (
    CouponUsageView,
    CouponView,
    LoyaltyEarnRuleView,
    LoyaltyManagementService,
    LoyaltyProgramPolicyView,
    LoyaltyProgramView,
    LoyaltyRedemptionPolicyView,
    LoyaltyTierView,
)
from settings.settings import Settings
from user_interface.form.loyalty_operations_form import LoyaltyOperationsForm


class LoyaltyManagementForm(QWidget):
    """Manage loyalty definition, profile, and transaction tables."""

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
        self.setWindowTitle(f"{Settings().app_name} - Loyalty Management")
        self.setMinimumSize(1480, 960)

        self._programs: list[LoyaltyProgramView] = []
        self._tiers: list[LoyaltyTierView] = []
        self._rules: list[LoyaltyEarnRuleView] = []
        self._program_policies: list[LoyaltyProgramPolicyView] = []
        self._redemption_policies: list[LoyaltyRedemptionPolicyView] = []
        self._customer_loyalties: list[CustomerLoyaltyView] = []
        self._transactions: list[LoyaltyPointTransactionView] = []
        self._coupons: list[CouponView] = []
        self._coupon_usages: list[CouponUsageView] = []

        self._selected_program_id: str | None = None
        self._selected_tier_id: str | None = None
        self._selected_rule_id: str | None = None
        self._selected_program_policy_id: str | None = None
        self._selected_redemption_policy_id: str | None = None
        self._selected_customer_loyalty_id: str | None = None
        self._selected_transaction_id: str | None = None

        self._operations_form: LoyaltyOperationsForm | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Loyalty Management Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)
        open_operations_button = QPushButton("Open Loyalty Operations Window")
        open_operations_button.clicked.connect(self._open_operations_window)
        action_row = QHBoxLayout()
        action_row.addStretch(1)
        action_row.addWidget(open_operations_button)
        action_row.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_programs_tab(), "Loyalty Programs")
        self._tabs.addTab(self._build_tiers_tab(), "Loyalty Tiers")
        self._tabs.addTab(self._build_rules_tab(), "Loyalty Earn Rules")
        self._tabs.addTab(self._build_program_policy_tab(), "Program Policies")
        self._tabs.addTab(self._build_redemption_policy_tab(), "Redemption Policies")
        self._tabs.addTab(self._build_customer_loyalty_tab(), "Customer Loyalty")
        self._tabs.addTab(self._build_transactions_tab(), "Point Transactions")
        self._tabs.addTab(self._build_operations_tab(), "Loyalty Operations")
        self._tabs.addTab(self._build_coupons_tab(), "Customer Coupons")
        self._tabs.addTab(self._build_coupon_usage_tab(), "Coupon Usage History")

        root = QVBoxLayout()
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)
        root.addWidget(header)
        root.addWidget(subtitle)
        root.addLayout(action_row)
        root.addWidget(self._status_label)
        root.addWidget(self._tabs)
        self.setLayout(root)

    def _build_programs_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        self._program_table = QTableWidget(0, 8)
        self._program_table.setHorizontalHeaderLabels(
            ["Name", "Active", "Points/Currency", "Currency/Point", "Min Purchase", "Expiry Days", "Welcome", "Birthday"]
        )
        self._init_table(self._program_table, self._on_program_selected)

        editor = QGroupBox("Loyalty Program Editor")
        form = QFormLayout()
        self._program_name_input = QLineEdit()
        self._program_description_input = QPlainTextEdit()
        self._program_description_input.setMinimumHeight(60)
        self._program_points_per_currency_input = QLineEdit()
        self._program_currency_per_point_input = QLineEdit()
        self._program_min_purchase_input = QLineEdit()
        self._program_expiry_days_input = QSpinBox()
        self._program_expiry_days_input.setRange(0, 10000)
        self._program_start_date_input = QLineEdit()
        self._program_start_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._program_end_date_input = QLineEdit()
        self._program_end_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._program_welcome_points_input = QSpinBox()
        self._program_welcome_points_input.setRange(0, 1_000_000)
        self._program_birthday_points_input = QSpinBox()
        self._program_birthday_points_input.setRange(0, 1_000_000)
        self._program_terms_input = QPlainTextEdit()
        self._program_terms_input.setMinimumHeight(60)
        self._program_settings_json_input = QPlainTextEdit()
        self._program_settings_json_input.setMinimumHeight(60)
        self._program_active_checkbox = QCheckBox("Active")
        self._program_active_checkbox.setChecked(True)
        form.addRow("Name", self._program_name_input)
        form.addRow("Description", self._program_description_input)
        form.addRow("Points Per Currency", self._program_points_per_currency_input)
        form.addRow("Currency Per Point", self._program_currency_per_point_input)
        form.addRow("Min Purchase For Points", self._program_min_purchase_input)
        form.addRow("Point Expiry Days", self._program_expiry_days_input)
        form.addRow("Start Date", self._program_start_date_input)
        form.addRow("End Date", self._program_end_date_input)
        form.addRow("Welcome Points", self._program_welcome_points_input)
        form.addRow("Birthday Points", self._program_birthday_points_input)
        form.addRow("Terms", self._program_terms_input)
        form.addRow("Settings JSON", self._program_settings_json_input)
        form.addRow(self._program_active_checkbox)
        editor.setLayout(self._editor_layout(form, self._save_program, self._delete_program, self._clear_program_editor, self.refresh_programs))

        splitter.addWidget(self._wrap(self._program_table))
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_tiers_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._tier_program_filter_combo = QComboBox()
        self._tier_program_filter_combo.currentIndexChanged.connect(self.refresh_tiers)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_tiers)
        filter_layout.addWidget(QLabel("Program"))
        filter_layout.addWidget(self._tier_program_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._tier_table = QTableWidget(0, 8)
        self._tier_table.setHorizontalHeaderLabels(
            ["Program", "Code", "Name", "Level", "Multiplier", "Discount %", "Display", "Active"]
        )
        self._init_table(self._tier_table, self._on_tier_selected)
        left_layout.addWidget(self._tier_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Loyalty Tier Editor")
        form = QFormLayout()
        self._tier_program_combo = QComboBox()
        self._tier_name_input = QLineEdit()
        self._tier_code_input = QLineEdit()
        self._tier_description_input = QPlainTextEdit()
        self._tier_description_input.setMinimumHeight(50)
        self._tier_level_input = QSpinBox()
        self._tier_level_input.setRange(1, 100)
        self._tier_min_points_input = QSpinBox()
        self._tier_min_points_input.setRange(0, 10_000_000)
        self._tier_min_annual_spending_input = QLineEdit()
        self._tier_points_multiplier_input = QLineEdit()
        self._tier_discount_percentage_input = QLineEdit()
        self._tier_display_order_input = QSpinBox()
        self._tier_display_order_input.setRange(0, 100_000)
        self._tier_color_input = QLineEdit()
        self._tier_icon_input = QLineEdit()
        self._tier_special_benefits_input = QPlainTextEdit()
        self._tier_special_benefits_input.setMinimumHeight(50)
        self._tier_active_checkbox = QCheckBox("Active")
        self._tier_active_checkbox.setChecked(True)
        form.addRow("Program", self._tier_program_combo)
        form.addRow("Name", self._tier_name_input)
        form.addRow("Code", self._tier_code_input)
        form.addRow("Description", self._tier_description_input)
        form.addRow("Tier Level", self._tier_level_input)
        form.addRow("Min Points Required", self._tier_min_points_input)
        form.addRow("Min Annual Spending", self._tier_min_annual_spending_input)
        form.addRow("Points Multiplier", self._tier_points_multiplier_input)
        form.addRow("Discount Percentage", self._tier_discount_percentage_input)
        form.addRow("Display Order", self._tier_display_order_input)
        form.addRow("Color", self._tier_color_input)
        form.addRow("Icon", self._tier_icon_input)
        form.addRow("Special Benefits", self._tier_special_benefits_input)
        form.addRow(self._tier_active_checkbox)
        editor.setLayout(self._editor_layout(form, self._save_tier, self._delete_tier, self._clear_tier_editor, self.refresh_tiers))

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_rules_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._rule_program_filter_combo = QComboBox()
        self._rule_program_filter_combo.currentIndexChanged.connect(self.refresh_rules)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_rules)
        filter_layout.addWidget(QLabel("Program"))
        filter_layout.addWidget(self._rule_program_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._rule_table = QTableWidget(0, 6)
        self._rule_table.setHorizontalHeaderLabels(
            ["Program", "Rule Code", "Type", "Priority", "Active", "Description"]
        )
        self._init_table(self._rule_table, self._on_rule_selected)
        left_layout.addWidget(self._rule_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Loyalty Earn Rule Editor")
        form = QFormLayout()
        self._rule_program_combo = QComboBox()
        self._rule_code_input = QLineEdit()
        self._rule_type_combo = QComboBox()
        self._rule_type_combo.addItems(["DOCUMENT_TOTAL", "LINE_ITEM", "PRODUCT_SET", "CATEGORY", "CUSTOM"])
        self._rule_priority_input = QSpinBox()
        self._rule_priority_input.setRange(1, 100_000)
        self._rule_config_json_input = QPlainTextEdit()
        self._rule_config_json_input.setMinimumHeight(80)
        self._rule_description_input = QPlainTextEdit()
        self._rule_description_input.setMinimumHeight(60)
        self._rule_active_checkbox = QCheckBox("Active")
        self._rule_active_checkbox.setChecked(True)
        form.addRow("Program", self._rule_program_combo)
        form.addRow("Rule Code", self._rule_code_input)
        form.addRow("Rule Type", self._rule_type_combo)
        form.addRow("Priority", self._rule_priority_input)
        form.addRow("Config JSON", self._rule_config_json_input)
        form.addRow("Description", self._rule_description_input)
        form.addRow(self._rule_active_checkbox)
        editor.setLayout(self._editor_layout(form, self._save_rule, self._delete_rule, self._clear_rule_editor, self.refresh_rules))

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_program_policy_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        self._program_policy_table = QTableWidget(0, 6)
        self._program_policy_table.setHorizontalHeaderLabels(
            ["Program", "Identifier", "Require Phone", "Void Policy", "Provider", "Phone Prefix"]
        )
        self._init_table(self._program_policy_table, self._on_program_policy_selected)
        editor = QGroupBox("Program Policy Editor")
        form = QFormLayout()
        self._program_policy_program_combo = QComboBox()
        self._program_policy_identifier_combo = QComboBox()
        self._program_policy_identifier_combo.addItems(["PHONE", "LOYALTY_CARD"])
        self._program_policy_require_phone_checkbox = QCheckBox("Require Customer Phone")
        self._program_policy_require_phone_checkbox.setChecked(True)
        self._program_policy_phone_prefix_input = QLineEdit()
        self._program_policy_void_policy_combo = QComboBox()
        self._program_policy_void_policy_combo.addItems(["NONE", "CLAWBACK_FULL", "CLAWBACK_PROPORTIONAL"])
        self._program_policy_integration_provider_combo = QComboBox()
        self._program_policy_integration_provider_combo.addItems(["LOCAL", "GATE", "EXTERNAL"])
        self._program_policy_integration_json_input = QPlainTextEdit()
        self._program_policy_integration_json_input.setMinimumHeight(80)
        form.addRow("Program", self._program_policy_program_combo)
        form.addRow("Customer Identifier", self._program_policy_identifier_combo)
        form.addRow(self._program_policy_require_phone_checkbox)
        form.addRow("Default Phone Prefix", self._program_policy_phone_prefix_input)
        form.addRow("Void Loyalty Policy", self._program_policy_void_policy_combo)
        form.addRow("Integration Provider", self._program_policy_integration_provider_combo)
        form.addRow("Integration Settings JSON", self._program_policy_integration_json_input)
        editor.setLayout(
            self._editor_layout(
                form,
                self._save_program_policy,
                self._delete_program_policy,
                self._clear_program_policy_editor,
                self.refresh_program_policies,
            )
        )
        splitter.addWidget(self._wrap(self._program_policy_table))
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_redemption_policy_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        self._redemption_policy_table = QTableWidget(0, 5)
        self._redemption_policy_table.setHorizontalHeaderLabels(
            ["Program", "Max Basket Share", "Minimum Points", "Step", "Allow Partial"]
        )
        self._init_table(self._redemption_policy_table, self._on_redemption_policy_selected)

        editor = QGroupBox("Redemption Policy Editor")
        form = QFormLayout()
        self._redemption_policy_program_combo = QComboBox()
        self._redemption_policy_max_share_input = QLineEdit()
        self._redemption_policy_min_points_input = QSpinBox()
        self._redemption_policy_min_points_input.setRange(0, 10_000_000)
        self._redemption_policy_step_input = QSpinBox()
        self._redemption_policy_step_input.setRange(1, 10_000_000)
        self._redemption_policy_partial_checkbox = QCheckBox("Allow Partial Redemption")
        self._redemption_policy_partial_checkbox.setChecked(True)
        form.addRow("Program", self._redemption_policy_program_combo)
        form.addRow("Max Basket Share (0-1)", self._redemption_policy_max_share_input)
        form.addRow("Minimum Points To Redeem", self._redemption_policy_min_points_input)
        form.addRow("Redemption Step", self._redemption_policy_step_input)
        form.addRow(self._redemption_policy_partial_checkbox)
        editor.setLayout(
            self._editor_layout(
                form,
                self._save_redemption_policy,
                self._delete_redemption_policy,
                self._clear_redemption_policy_editor,
                self.refresh_redemption_policies,
            )
        )

        splitter.addWidget(self._wrap(self._redemption_policy_table))
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_customer_loyalty_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._customer_loyalty_customer_filter_combo = QComboBox()
        self._customer_loyalty_customer_filter_combo.currentIndexChanged.connect(self.refresh_customer_loyalties)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_customer_loyalties)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._customer_loyalty_customer_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)
        self._customer_loyalty_table = QTableWidget(0, 8)
        self._customer_loyalty_table.setHorizontalHeaderLabels(
            ["Customer", "Program", "Tier", "Card Number", "Available", "Lifetime", "Total Spent", "Active"]
        )
        self._init_table(self._customer_loyalty_table, self._on_customer_loyalty_selected)
        left_layout.addWidget(self._customer_loyalty_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Customer Loyalty Editor")
        form = QFormLayout()
        self._customer_loyalty_customer_combo = QComboBox()
        self._customer_loyalty_program_combo = QComboBox()
        self._customer_loyalty_program_combo.currentIndexChanged.connect(
            self._reload_customer_loyalty_tier_combo
        )
        self._customer_loyalty_tier_combo = QComboBox()
        self._customer_loyalty_card_input = QLineEdit()
        self._customer_loyalty_total_points_input = QSpinBox()
        self._customer_loyalty_total_points_input.setRange(-10_000_000, 10_000_000)
        self._customer_loyalty_available_points_input = QSpinBox()
        self._customer_loyalty_available_points_input.setRange(-10_000_000, 10_000_000)
        self._customer_loyalty_lifetime_points_input = QSpinBox()
        self._customer_loyalty_lifetime_points_input.setRange(0, 10_000_000)
        self._customer_loyalty_points_to_expire_input = QSpinBox()
        self._customer_loyalty_points_to_expire_input.setRange(0, 10_000_000)
        self._customer_loyalty_expiry_date_input = QLineEdit()
        self._customer_loyalty_expiry_date_input.setPlaceholderText("YYYY-MM-DD")
        self._customer_loyalty_enrollment_date_input = QLineEdit()
        self._customer_loyalty_enrollment_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._customer_loyalty_last_activity_date_input = QLineEdit()
        self._customer_loyalty_last_activity_date_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        self._customer_loyalty_total_purchases_input = QSpinBox()
        self._customer_loyalty_total_purchases_input.setRange(0, 100_000_000)
        self._customer_loyalty_total_spent_input = QLineEdit()
        self._customer_loyalty_annual_spent_input = QLineEdit()
        self._customer_loyalty_active_checkbox = QCheckBox("Active")
        self._customer_loyalty_active_checkbox.setChecked(True)
        form.addRow("Customer", self._customer_loyalty_customer_combo)
        form.addRow("Program", self._customer_loyalty_program_combo)
        form.addRow("Tier", self._customer_loyalty_tier_combo)
        form.addRow("Card Number", self._customer_loyalty_card_input)
        form.addRow("Total Points", self._customer_loyalty_total_points_input)
        form.addRow("Available Points", self._customer_loyalty_available_points_input)
        form.addRow("Lifetime Points", self._customer_loyalty_lifetime_points_input)
        form.addRow("Points To Expire", self._customer_loyalty_points_to_expire_input)
        form.addRow("Points Expiry Date", self._customer_loyalty_expiry_date_input)
        form.addRow("Enrollment Date", self._customer_loyalty_enrollment_date_input)
        form.addRow("Last Activity Date", self._customer_loyalty_last_activity_date_input)
        form.addRow("Total Purchases", self._customer_loyalty_total_purchases_input)
        form.addRow("Total Spent", self._customer_loyalty_total_spent_input)
        form.addRow("Annual Spent", self._customer_loyalty_annual_spent_input)
        form.addRow(self._customer_loyalty_active_checkbox)
        editor.setLayout(
            self._editor_layout(
                form,
                self._save_customer_loyalty,
                self._delete_customer_loyalty,
                self._clear_customer_loyalty_editor,
                self.refresh_customer_loyalties,
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_transactions_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._transaction_customer_filter_combo = QComboBox()
        self._transaction_customer_filter_combo.currentIndexChanged.connect(self.refresh_transactions)
        self._transaction_loyalty_filter_combo = QComboBox()
        self._transaction_loyalty_filter_combo.currentIndexChanged.connect(self.refresh_transactions)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_transactions)
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
        self._init_table(self._transaction_table, self._on_transaction_selected)
        left_layout.addWidget(self._transaction_table)
        left.setLayout(left_layout)

        editor = QGroupBox("Loyalty Point Transaction Editor")
        form = QFormLayout()
        self._transaction_loyalty_combo = QComboBox()
        self._transaction_customer_combo = QComboBox()
        self._transaction_type_combo = QComboBox()
        self._transaction_type_combo.addItems(
            ["EARNED", "REDEEMED", "EXPIRED", "ADJUSTED", "BONUS", "WELCOME", "BIRTHDAY", "REFUND"]
        )
        self._transaction_points_input = QSpinBox()
        self._transaction_points_input.setRange(-10_000_000, 10_000_000)
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
        self._transaction_notes_input.setMinimumHeight(60)
        form.addRow("Customer Loyalty", self._transaction_loyalty_combo)
        form.addRow("Customer", self._transaction_customer_combo)
        form.addRow("Type", self._transaction_type_combo)
        form.addRow("Points", self._transaction_points_input)
        form.addRow("Balance After", self._transaction_balance_after_input)
        form.addRow("Transaction Date", self._transaction_date_input)
        form.addRow("Expiry Date", self._transaction_expiry_date_input)
        form.addRow("Store", self._transaction_store_combo)
        form.addRow("Cashier", self._transaction_cashier_combo)
        form.addRow("Transaction Head", self._transaction_head_combo)
        form.addRow("Reference Number", self._transaction_reference_input)
        form.addRow("Description", self._transaction_description_input)
        form.addRow("Notes", self._transaction_notes_input)
        editor.setLayout(
            self._editor_layout(
                form,
                self._save_transaction,
                self._delete_transaction,
                self._clear_transaction_editor,
                self.refresh_transactions,
            )
        )

        splitter.addWidget(left)
        splitter.addWidget(editor)
        splitter.setSizes([980, 450])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_operations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._operations_program_filter_combo = QComboBox()
        self._operations_program_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        self._operations_customer_filter_combo = QComboBox()
        self._operations_customer_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        self._operations_active_filter_combo = QComboBox()
        self._operations_active_filter_combo.addItem("All", None)
        self._operations_active_filter_combo.addItem("Active Only", True)
        self._operations_active_filter_combo.addItem("Inactive Only", False)
        self._operations_active_filter_combo.currentIndexChanged.connect(self.refresh_operations)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_operations)
        open_window_button = QPushButton("Open Operations Window")
        open_window_button.clicked.connect(self._open_operations_window)
        filter_layout.addWidget(QLabel("Program"))
        filter_layout.addWidget(self._operations_program_filter_combo)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._operations_customer_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._operations_active_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        filter_layout.addWidget(open_window_button)
        layout.addLayout(filter_layout)
        self._operations_table = QTableWidget(0, 11)
        self._operations_table.setHorizontalHeaderLabels(
            [
                "Customer",
                "Program",
                "Tier",
                "Card Number",
                "Available Points",
                "Lifetime Points",
                "Total Spent",
                "Transactions",
                "Earned",
                "Redeemed",
                "Last Transaction",
            ]
        )
        self._init_table(self._operations_table, None)
        layout.addWidget(self._operations_table)
        tab.setLayout(layout)
        return tab

    def _build_coupons_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._coupon_customer_filter_combo = QComboBox()
        self._coupon_customer_filter_combo.currentIndexChanged.connect(self.refresh_coupons)
        self._coupon_campaign_filter_combo = QComboBox()
        self._coupon_campaign_filter_combo.currentIndexChanged.connect(self.refresh_coupons)
        self._coupon_active_filter_combo = QComboBox()
        self._coupon_active_filter_combo.addItem("All", None)
        self._coupon_active_filter_combo.addItem("Active Only", True)
        self._coupon_active_filter_combo.addItem("Inactive Only", False)
        self._coupon_active_filter_combo.currentIndexChanged.connect(self.refresh_coupons)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_coupons)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._coupon_customer_filter_combo)
        filter_layout.addWidget(QLabel("Campaign"))
        filter_layout.addWidget(self._coupon_campaign_filter_combo)
        filter_layout.addWidget(QLabel("Status"))
        filter_layout.addWidget(self._coupon_active_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)
        self._coupon_table = QTableWidget(0, 11)
        self._coupon_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Name",
                "Type",
                "Campaign",
                "Customer",
                "Start Date",
                "End Date",
                "Usage Limit",
                "Usage Count",
                "Sent",
                "Active",
            ]
        )
        self._init_table(self._coupon_table, None)
        layout.addWidget(self._coupon_table)
        tab.setLayout(layout)
        return tab

    def _build_coupon_usage_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._coupon_usage_customer_filter_combo = QComboBox()
        self._coupon_usage_customer_filter_combo.currentIndexChanged.connect(self.refresh_coupon_usages)
        self._coupon_usage_coupon_filter_combo = QComboBox()
        self._coupon_usage_coupon_filter_combo.currentIndexChanged.connect(self.refresh_coupon_usages)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_coupon_usages)
        filter_layout.addWidget(QLabel("Customer"))
        filter_layout.addWidget(self._coupon_usage_customer_filter_combo)
        filter_layout.addWidget(QLabel("Coupon"))
        filter_layout.addWidget(self._coupon_usage_coupon_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        layout.addLayout(filter_layout)
        self._coupon_usage_table = QTableWidget(0, 8)
        self._coupon_usage_table.setHorizontalHeaderLabels(
            [
                "Coupon Code",
                "Coupon Name",
                "Customer",
                "Discount Amount",
                "Usage Date",
                "Store",
                "Cashier",
                "Notes",
            ]
        )
        self._init_table(self._coupon_usage_table, None)
        layout.addWidget(self._coupon_usage_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self._reload_lookup_combos()
        self.refresh_programs()
        self.refresh_tiers()
        self.refresh_rules()
        self.refresh_program_policies()
        self.refresh_redemption_policies()
        self.refresh_customer_loyalties()
        self.refresh_transactions()
        self.refresh_operations()
        self.refresh_coupons()
        self.refresh_coupon_usages()

    def refresh_programs(self) -> None:
        self._programs = self.loyalty_service.list_loyalty_programs()
        self._program_table.setRowCount(len(self._programs))
        for row_index, row in enumerate(self._programs):
            values = [
                row.name,
                "Yes" if row.is_active else "No",
                self._format_amount(row.points_per_currency),
                self._format_amount(row.currency_per_point),
                self._format_amount(row.min_purchase_for_points),
                str(row.point_expiry_days),
                str(row.welcome_points),
                str(row.birthday_points),
            ]
            self._set_row(self._program_table, row_index, values, row.id)
        self._program_table.resizeColumnsToContents()
        self._reload_program_combos()

    def refresh_tiers(self) -> None:
        self._tiers = self.loyalty_service.list_loyalty_tiers(
            program_id=self._tier_program_filter_combo.currentData()
        )
        self._tier_table.setRowCount(len(self._tiers))
        for row_index, row in enumerate(self._tiers):
            values = [
                row.loyalty_program_label,
                row.code,
                row.name,
                str(row.tier_level),
                self._format_amount(row.points_multiplier),
                self._format_amount(row.discount_percentage),
                str(row.display_order),
                "Yes" if row.is_active else "No",
            ]
            self._set_row(self._tier_table, row_index, values, row.id)
        self._tier_table.resizeColumnsToContents()

    def refresh_rules(self) -> None:
        self._rules = self.loyalty_service.list_loyalty_earn_rules(
            program_id=self._rule_program_filter_combo.currentData()
        )
        self._rule_table.setRowCount(len(self._rules))
        for row_index, row in enumerate(self._rules):
            values = [
                row.loyalty_program_label,
                row.rule_code,
                row.rule_type,
                str(row.priority),
                "Yes" if row.is_active else "No",
                row.description,
            ]
            self._set_row(self._rule_table, row_index, values, row.id)
        self._rule_table.resizeColumnsToContents()

    def refresh_program_policies(self) -> None:
        self._program_policies = self.loyalty_service.list_loyalty_program_policies()
        self._program_policy_table.setRowCount(len(self._program_policies))
        for row_index, row in enumerate(self._program_policies):
            values = [
                row.loyalty_program_label,
                row.customer_identifier_type,
                "Yes" if row.require_customer_phone_for_enrollment else "No",
                row.void_loyalty_points_policy,
                row.integration_provider,
                row.default_phone_country_calling_code,
            ]
            self._set_row(self._program_policy_table, row_index, values, row.id)
        self._program_policy_table.resizeColumnsToContents()

    def refresh_redemption_policies(self) -> None:
        self._redemption_policies = self.loyalty_service.list_loyalty_redemption_policies()
        self._redemption_policy_table.setRowCount(len(self._redemption_policies))
        for row_index, row in enumerate(self._redemption_policies):
            values = [
                row.loyalty_program_label,
                self._format_amount(row.max_basket_amount_share_from_points),
                str(row.minimum_points_to_redeem),
                str(row.points_redemption_step),
                "Yes" if row.allow_partial_redemption else "No",
            ]
            self._set_row(self._redemption_policy_table, row_index, values, row.id)
        self._redemption_policy_table.resizeColumnsToContents()

    def refresh_customer_loyalties(self) -> None:
        self._customer_loyalties = self.customer_service.list_customer_loyalties(
            customer_id=self._customer_loyalty_customer_filter_combo.currentData()
        )
        self._customer_loyalty_table.setRowCount(len(self._customer_loyalties))
        for row_index, row in enumerate(self._customer_loyalties):
            values = [
                row.customer_label,
                row.loyalty_program_label,
                row.loyalty_tier_label,
                row.loyalty_card_number,
                str(row.available_points),
                str(row.lifetime_points),
                self._format_amount(row.total_spent),
                "Yes" if row.is_active else "No",
            ]
            self._set_row(self._customer_loyalty_table, row_index, values, row.id)
        self._customer_loyalty_table.resizeColumnsToContents()
        self._reload_customer_loyalty_lookup_combos()

    def refresh_transactions(self) -> None:
        self._transactions = self.customer_service.list_loyalty_point_transactions(
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
            self._set_row(self._transaction_table, row_index, values, row.id)
        self._transaction_table.resizeColumnsToContents()

    def refresh_operations(self) -> None:
        rows = self.loyalty_service.list_loyalty_operations(
            program_id=self._operations_program_filter_combo.currentData(),
            customer_id=self._operations_customer_filter_combo.currentData(),
            active_only=self._operations_active_filter_combo.currentData(),
        )
        self._operations_table.setRowCount(len(rows))
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
                row.last_transaction_at.isoformat(sep=" ") if row.last_transaction_at else "",
            ]
            self._set_row(self._operations_table, row_index, values, row.customer_loyalty_id)
        self._operations_table.resizeColumnsToContents()

    def refresh_coupons(self) -> None:
        self._coupons = self.loyalty_service.list_coupons(
            customer_id=self._coupon_customer_filter_combo.currentData(),
            campaign_id=self._coupon_campaign_filter_combo.currentData(),
            active_only=self._coupon_active_filter_combo.currentData(),
        )
        self._coupon_table.setRowCount(len(self._coupons))
        for row_index, row in enumerate(self._coupons):
            values = [
                row.code,
                row.name,
                row.coupon_type,
                row.campaign_label,
                row.customer_label,
                row.start_date.strftime("%Y-%m-%d") if row.start_date else "",
                row.end_date.strftime("%Y-%m-%d") if row.end_date else "",
                str(row.usage_limit) if row.usage_limit is not None else "Unlimited",
                str(row.usage_count),
                "Yes" if row.is_sent else "No",
                "Yes" if row.is_active else "No",
            ]
            self._set_row(self._coupon_table, row_index, values, row.id)
        self._coupon_table.resizeColumnsToContents()
        self._reload_coupon_filter_combos()

    def refresh_coupon_usages(self) -> None:
        self._coupon_usages = self.loyalty_service.list_coupon_usages(
            customer_id=self._coupon_usage_customer_filter_combo.currentData(),
            coupon_id=self._coupon_usage_coupon_filter_combo.currentData(),
        )
        self._coupon_usage_table.setRowCount(len(self._coupon_usages))
        for row_index, row in enumerate(self._coupon_usages):
            values = [
                row.coupon_code,
                row.coupon_name,
                row.customer_label,
                self._format_amount(row.discount_amount),
                row.usage_date.isoformat(sep=" ") if row.usage_date else "",
                row.store_label,
                row.cashier_label,
                row.notes,
            ]
            self._set_row(self._coupon_usage_table, row_index, values, row.id)
        self._coupon_usage_table.resizeColumnsToContents()

    def _save_program(self) -> None:
        payload = {
            "name": self._program_name_input.text(),
            "description": self._program_description_input.toPlainText(),
            "points_per_currency": self._program_points_per_currency_input.text(),
            "currency_per_point": self._program_currency_per_point_input.text(),
            "min_purchase_for_points": self._program_min_purchase_input.text(),
            "point_expiry_days": self._program_expiry_days_input.value(),
            "start_date": self._program_start_date_input.text(),
            "end_date": self._program_end_date_input.text(),
            "welcome_points": self._program_welcome_points_input.value(),
            "birthday_points": self._program_birthday_points_input.value(),
            "terms_conditions": self._program_terms_input.toPlainText(),
            "settings_json": self._program_settings_json_input.toPlainText(),
            "is_active": self._program_active_checkbox.isChecked(),
        }
        result = self.loyalty_service.save_loyalty_program(payload=payload, program_id=self._selected_program_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_program_editor()

    def _save_tier(self) -> None:
        payload = {
            "loyalty_program_id": self._tier_program_combo.currentData(),
            "name": self._tier_name_input.text(),
            "code": self._tier_code_input.text(),
            "description": self._tier_description_input.toPlainText(),
            "tier_level": self._tier_level_input.value(),
            "min_points_required": self._tier_min_points_input.value(),
            "min_annual_spending": self._tier_min_annual_spending_input.text(),
            "points_multiplier": self._tier_points_multiplier_input.text(),
            "discount_percentage": self._tier_discount_percentage_input.text(),
            "display_order": self._tier_display_order_input.value(),
            "color_code": self._tier_color_input.text(),
            "icon": self._tier_icon_input.text(),
            "special_benefits": self._tier_special_benefits_input.toPlainText(),
            "is_active": self._tier_active_checkbox.isChecked(),
        }
        result = self.loyalty_service.save_loyalty_tier(payload=payload, tier_id=self._selected_tier_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_tiers()
            self._clear_tier_editor()

    def _save_rule(self) -> None:
        payload = {
            "loyalty_program_id": self._rule_program_combo.currentData(),
            "rule_code": self._rule_code_input.text(),
            "rule_type": self._rule_type_combo.currentText(),
            "priority": self._rule_priority_input.value(),
            "config_json": self._rule_config_json_input.toPlainText(),
            "description": self._rule_description_input.toPlainText(),
            "is_active": self._rule_active_checkbox.isChecked(),
        }
        result = self.loyalty_service.save_loyalty_earn_rule(payload=payload, rule_id=self._selected_rule_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_rules()
            self._clear_rule_editor()

    def _save_program_policy(self) -> None:
        payload = {
            "loyalty_program_id": self._program_policy_program_combo.currentData(),
            "customer_identifier_type": self._program_policy_identifier_combo.currentText(),
            "require_customer_phone_for_enrollment": self._program_policy_require_phone_checkbox.isChecked(),
            "default_phone_country_calling_code": self._program_policy_phone_prefix_input.text(),
            "void_loyalty_points_policy": self._program_policy_void_policy_combo.currentText(),
            "integration_provider": self._program_policy_integration_provider_combo.currentText(),
            "integration_settings_json": self._program_policy_integration_json_input.toPlainText(),
        }
        result = self.loyalty_service.save_loyalty_program_policy(
            payload=payload,
            policy_id=self._selected_program_policy_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_program_policies()
            self._clear_program_policy_editor()

    def _save_redemption_policy(self) -> None:
        payload = {
            "loyalty_program_id": self._redemption_policy_program_combo.currentData(),
            "max_basket_amount_share_from_points": self._redemption_policy_max_share_input.text(),
            "minimum_points_to_redeem": self._redemption_policy_min_points_input.value(),
            "points_redemption_step": self._redemption_policy_step_input.value(),
            "allow_partial_redemption": self._redemption_policy_partial_checkbox.isChecked(),
        }
        result = self.loyalty_service.save_loyalty_redemption_policy(
            payload=payload,
            policy_id=self._selected_redemption_policy_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_redemption_policies()
            self._clear_redemption_policy_editor()

    def _save_customer_loyalty(self) -> None:
        payload = {
            "customer_id": self._customer_loyalty_customer_combo.currentData(),
            "loyalty_program_id": self._customer_loyalty_program_combo.currentData(),
            "loyalty_tier_id": self._customer_loyalty_tier_combo.currentData(),
            "loyalty_card_number": self._customer_loyalty_card_input.text(),
            "total_points": self._customer_loyalty_total_points_input.value(),
            "available_points": self._customer_loyalty_available_points_input.value(),
            "lifetime_points": self._customer_loyalty_lifetime_points_input.value(),
            "points_to_expire": self._customer_loyalty_points_to_expire_input.value(),
            "points_expiry_date": self._customer_loyalty_expiry_date_input.text(),
            "enrollment_date": self._customer_loyalty_enrollment_date_input.text(),
            "last_activity_date": self._customer_loyalty_last_activity_date_input.text(),
            "total_purchases": self._customer_loyalty_total_purchases_input.value(),
            "total_spent": self._customer_loyalty_total_spent_input.text(),
            "annual_spent": self._customer_loyalty_annual_spent_input.text(),
            "is_active": self._customer_loyalty_active_checkbox.isChecked(),
        }
        result = self.customer_service.save_customer_loyalty(
            payload=payload,
            loyalty_id=self._selected_customer_loyalty_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_customer_loyalty_editor()

    def _save_transaction(self) -> None:
        loyalty_id = self._transaction_loyalty_combo.currentData()
        selected = next((x for x in self._customer_loyalties if x.id == loyalty_id), None)
        payload = {
            "customer_loyalty_id": loyalty_id,
            "customer_id": self._transaction_customer_combo.currentData(),
            "transaction_type": self._transaction_type_combo.currentText(),
            "points_amount": self._transaction_points_input.value(),
            "balance_after": self._transaction_balance_after_input.text(),
            "transaction_date": self._transaction_date_input.text(),
            "expiry_date": self._transaction_expiry_date_input.text(),
            "store_id": self._transaction_store_combo.currentData(),
            "cashier_id": self._transaction_cashier_combo.currentData(),
            "transaction_head_id": self._transaction_head_combo.currentData(),
            "reference_number": self._transaction_reference_input.text(),
            "description": self._transaction_description_input.text(),
            "notes": self._transaction_notes_input.toPlainText(),
            "available_points_hint": selected.available_points if selected else 0,
        }
        result = self.customer_service.save_loyalty_point_transaction(
            payload=payload,
            transaction_id=self._selected_transaction_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_transaction_editor()

    def _delete_program(self) -> None:
        self._delete_record(
            selected_id=self._selected_program_id,
            title="Delete Loyalty Program",
            question="Selected loyalty program will be soft deleted. Continue?",
            deleter=self.loyalty_service.delete_loyalty_program,
            refresh=self.refresh_programs,
            clear=self._clear_program_editor,
        )

    def _delete_tier(self) -> None:
        self._delete_record(
            selected_id=self._selected_tier_id,
            title="Delete Loyalty Tier",
            question="Selected loyalty tier will be soft deleted. Continue?",
            deleter=self.loyalty_service.delete_loyalty_tier,
            refresh=self.refresh_tiers,
            clear=self._clear_tier_editor,
        )

    def _delete_rule(self) -> None:
        self._delete_record(
            selected_id=self._selected_rule_id,
            title="Delete Loyalty Earn Rule",
            question="Selected loyalty earn rule will be soft deleted. Continue?",
            deleter=self.loyalty_service.delete_loyalty_earn_rule,
            refresh=self.refresh_rules,
            clear=self._clear_rule_editor,
        )

    def _delete_program_policy(self) -> None:
        self._delete_record(
            selected_id=self._selected_program_policy_id,
            title="Delete Program Policy",
            question="Selected program policy will be soft deleted. Continue?",
            deleter=self.loyalty_service.delete_loyalty_program_policy,
            refresh=self.refresh_program_policies,
            clear=self._clear_program_policy_editor,
        )

    def _delete_redemption_policy(self) -> None:
        self._delete_record(
            selected_id=self._selected_redemption_policy_id,
            title="Delete Redemption Policy",
            question="Selected redemption policy will be soft deleted. Continue?",
            deleter=self.loyalty_service.delete_loyalty_redemption_policy,
            refresh=self.refresh_redemption_policies,
            clear=self._clear_redemption_policy_editor,
        )

    def _delete_customer_loyalty(self) -> None:
        self._delete_record(
            selected_id=self._selected_customer_loyalty_id,
            title="Delete Customer Loyalty",
            question="Selected customer loyalty will be soft deleted. Continue?",
            deleter=self.customer_service.delete_customer_loyalty,
            refresh=self.refresh_customer_loyalties,
            clear=self._clear_customer_loyalty_editor,
        )

    def _delete_transaction(self) -> None:
        self._delete_record(
            selected_id=self._selected_transaction_id,
            title="Delete Loyalty Point Transaction",
            question="Selected loyalty point transaction will be soft deleted. Continue?",
            deleter=self.customer_service.delete_loyalty_point_transaction,
            refresh=self.refresh_transactions,
            clear=self._clear_transaction_editor,
        )

    def _on_program_selected(self) -> None:
        selected = self._selected_row(self._program_table, self._programs)
        if selected is None:
            return
        self._selected_program_id = selected.id
        self._program_name_input.setText(selected.name)
        self._program_description_input.setPlainText(selected.description)
        self._program_points_per_currency_input.setText(self._format_amount(selected.points_per_currency))
        self._program_currency_per_point_input.setText(self._format_amount(selected.currency_per_point))
        self._program_min_purchase_input.setText(self._format_amount(selected.min_purchase_for_points))
        self._program_expiry_days_input.setValue(selected.point_expiry_days)
        self._program_start_date_input.setText(
            selected.start_date.strftime("%Y-%m-%d %H:%M") if selected.start_date else ""
        )
        self._program_end_date_input.setText(
            selected.end_date.strftime("%Y-%m-%d %H:%M") if selected.end_date else ""
        )
        self._program_welcome_points_input.setValue(selected.welcome_points)
        self._program_birthday_points_input.setValue(selected.birthday_points)
        self._program_terms_input.setPlainText(selected.terms_conditions)
        self._program_settings_json_input.setPlainText(selected.settings_json)
        self._program_active_checkbox.setChecked(selected.is_active)

    def _on_tier_selected(self) -> None:
        selected = self._selected_row(self._tier_table, self._tiers)
        if selected is None:
            return
        self._selected_tier_id = selected.id
        self._tier_program_combo.setCurrentIndex(self._tier_program_combo.findData(selected.loyalty_program_id))
        self._tier_name_input.setText(selected.name)
        self._tier_code_input.setText(selected.code)
        self._tier_description_input.setPlainText(selected.description)
        self._tier_level_input.setValue(selected.tier_level)
        self._tier_min_points_input.setValue(selected.min_points_required)
        self._tier_min_annual_spending_input.setText(self._format_amount(selected.min_annual_spending))
        self._tier_points_multiplier_input.setText(self._format_amount(selected.points_multiplier))
        self._tier_discount_percentage_input.setText(self._format_amount(selected.discount_percentage))
        self._tier_display_order_input.setValue(selected.display_order)
        self._tier_color_input.setText(selected.color_code)
        self._tier_icon_input.setText(selected.icon)
        self._tier_special_benefits_input.setPlainText(selected.special_benefits)
        self._tier_active_checkbox.setChecked(selected.is_active)

    def _on_rule_selected(self) -> None:
        selected = self._selected_row(self._rule_table, self._rules)
        if selected is None:
            return
        self._selected_rule_id = selected.id
        self._rule_program_combo.setCurrentIndex(self._rule_program_combo.findData(selected.loyalty_program_id))
        self._rule_code_input.setText(selected.rule_code)
        self._rule_type_combo.setCurrentText(selected.rule_type)
        self._rule_priority_input.setValue(selected.priority)
        self._rule_config_json_input.setPlainText(selected.config_json)
        self._rule_description_input.setPlainText(selected.description)
        self._rule_active_checkbox.setChecked(selected.is_active)

    def _on_program_policy_selected(self) -> None:
        selected = self._selected_row(self._program_policy_table, self._program_policies)
        if selected is None:
            return
        self._selected_program_policy_id = selected.id
        self._program_policy_program_combo.setCurrentIndex(
            self._program_policy_program_combo.findData(selected.loyalty_program_id)
        )
        self._program_policy_identifier_combo.setCurrentText(selected.customer_identifier_type)
        self._program_policy_require_phone_checkbox.setChecked(selected.require_customer_phone_for_enrollment)
        self._program_policy_phone_prefix_input.setText(selected.default_phone_country_calling_code)
        self._program_policy_void_policy_combo.setCurrentText(selected.void_loyalty_points_policy)
        self._program_policy_integration_provider_combo.setCurrentText(selected.integration_provider)
        self._program_policy_integration_json_input.setPlainText(selected.integration_settings_json)

    def _on_redemption_policy_selected(self) -> None:
        selected = self._selected_row(self._redemption_policy_table, self._redemption_policies)
        if selected is None:
            return
        self._selected_redemption_policy_id = selected.id
        self._redemption_policy_program_combo.setCurrentIndex(
            self._redemption_policy_program_combo.findData(selected.loyalty_program_id)
        )
        self._redemption_policy_max_share_input.setText(
            self._format_amount(selected.max_basket_amount_share_from_points)
        )
        self._redemption_policy_min_points_input.setValue(selected.minimum_points_to_redeem)
        self._redemption_policy_step_input.setValue(selected.points_redemption_step)
        self._redemption_policy_partial_checkbox.setChecked(selected.allow_partial_redemption)

    def _on_customer_loyalty_selected(self) -> None:
        selected = self._selected_row(self._customer_loyalty_table, self._customer_loyalties)
        if selected is None:
            return
        self._selected_customer_loyalty_id = selected.id
        self._customer_loyalty_customer_combo.setCurrentIndex(
            self._customer_loyalty_customer_combo.findData(selected.customer_id)
        )
        self._customer_loyalty_program_combo.setCurrentIndex(
            self._customer_loyalty_program_combo.findData(selected.loyalty_program_id)
        )
        self._reload_customer_loyalty_tier_combo()
        self._customer_loyalty_tier_combo.setCurrentIndex(
            self._customer_loyalty_tier_combo.findData(selected.loyalty_tier_id)
        )
        self._customer_loyalty_card_input.setText(selected.loyalty_card_number)
        self._customer_loyalty_total_points_input.setValue(selected.total_points)
        self._customer_loyalty_available_points_input.setValue(selected.available_points)
        self._customer_loyalty_lifetime_points_input.setValue(selected.lifetime_points)
        self._customer_loyalty_points_to_expire_input.setValue(selected.points_to_expire)
        self._customer_loyalty_expiry_date_input.setText(
            selected.points_expiry_date.isoformat() if selected.points_expiry_date else ""
        )
        self._customer_loyalty_enrollment_date_input.setText(
            selected.enrollment_date.strftime("%Y-%m-%d %H:%M") if selected.enrollment_date else ""
        )
        self._customer_loyalty_last_activity_date_input.setText(
            selected.last_activity_date.strftime("%Y-%m-%d %H:%M") if selected.last_activity_date else ""
        )
        self._customer_loyalty_total_purchases_input.setValue(selected.total_purchases)
        self._customer_loyalty_total_spent_input.setText(self._format_amount(selected.total_spent))
        self._customer_loyalty_annual_spent_input.setText(self._format_amount(selected.annual_spent))
        self._customer_loyalty_active_checkbox.setChecked(selected.is_active)

    def _on_transaction_selected(self) -> None:
        selected = self._selected_row(self._transaction_table, self._transactions)
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
        self._transaction_points_input.setValue(selected.points_amount)
        self._transaction_balance_after_input.setText(str(selected.balance_after))
        self._transaction_date_input.setText(
            selected.transaction_date.strftime("%Y-%m-%d %H:%M") if selected.transaction_date else ""
        )
        self._transaction_expiry_date_input.setText(
            selected.expiry_date.isoformat() if selected.expiry_date else ""
        )
        self._transaction_store_combo.setCurrentIndex(self._transaction_store_combo.findData(selected.store_id))
        self._transaction_cashier_combo.setCurrentIndex(
            self._transaction_cashier_combo.findData(selected.cashier_id)
        )
        self._transaction_head_combo.setCurrentIndex(
            self._transaction_head_combo.findData(selected.transaction_head_id)
        )
        self._transaction_reference_input.setText(selected.reference_number)
        self._transaction_description_input.setText(selected.description)
        self._transaction_notes_input.setPlainText(selected.notes)

    def _reload_lookup_combos(self) -> None:
        self._reload_program_combos()
        customer_items = [(item.id, item.label) for item in self.customer_service.list_customer_lookups()]
        loyalty_items = [(item.id, item.label) for item in self.customer_service.list_customer_loyalty_lookups()]
        store_items = [(item.id, item.label) for item in self.customer_service.list_store_lookups()]
        cashier_items = [(item.id, item.label) for item in self.customer_service.list_cashier_lookups()]
        txn_head_items = [(item.id, item.label) for item in self.customer_service.list_transaction_head_lookups()]
        self._reload_combo(
            self._customer_loyalty_customer_combo, customer_items, include_empty=False, empty_label=""
        )
        self._reload_combo(
            self._customer_loyalty_customer_filter_combo, customer_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._transaction_loyalty_combo, loyalty_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._transaction_loyalty_filter_combo, loyalty_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._transaction_customer_combo, customer_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._transaction_customer_filter_combo, customer_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(self._transaction_store_combo, store_items, include_empty=True, empty_label="None")
        self._reload_combo(self._transaction_cashier_combo, cashier_items, include_empty=True, empty_label="None")
        self._reload_combo(self._transaction_head_combo, txn_head_items, include_empty=True, empty_label="None")
        self._reload_combo(
            self._operations_customer_filter_combo, customer_items, include_empty=True, empty_label="All"
        )
        self._reload_customer_loyalty_tier_combo()
        self._reload_combo(
            self._coupon_customer_filter_combo, customer_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._coupon_usage_customer_filter_combo, customer_items, include_empty=True, empty_label="All"
        )
        self._reload_coupon_filter_combos()

    def _reload_program_combos(self) -> None:
        program_items = [(item.id, item.label) for item in self.loyalty_service.list_loyalty_program_lookups()]
        for combo, include_empty, empty_label in (
            (self._tier_program_combo, False, ""),
            (self._tier_program_filter_combo, True, "All"),
            (self._rule_program_combo, False, ""),
            (self._rule_program_filter_combo, True, "All"),
            (self._program_policy_program_combo, False, ""),
            (self._redemption_policy_program_combo, False, ""),
            (self._customer_loyalty_program_combo, False, ""),
            (self._operations_program_filter_combo, True, "All"),
        ):
            self._reload_combo(combo, program_items, include_empty=include_empty, empty_label=empty_label)

    def _reload_customer_loyalty_tier_combo(self) -> None:
        selected_program_id = self._customer_loyalty_program_combo.currentData()
        tier_items = [
            (item.id, item.label)
            for item in self.loyalty_service.list_loyalty_tier_lookups(program_id=selected_program_id)
        ]
        self._reload_combo(self._customer_loyalty_tier_combo, tier_items, include_empty=True, empty_label="None")

    def _reload_customer_loyalty_lookup_combos(self) -> None:
        loyalty_items = [(item.id, item.label) for item in self.customer_service.list_customer_loyalty_lookups()]
        self._reload_combo(self._transaction_loyalty_combo, loyalty_items, include_empty=False, empty_label="")
        self._reload_combo(
            self._transaction_loyalty_filter_combo, loyalty_items, include_empty=True, empty_label="All"
        )

    def _reload_coupon_filter_combos(self) -> None:
        campaign_items = [(item.id, item.label) for item in self.loyalty_service.list_campaign_lookups()]
        coupon_items = [(item.id, item.label) for item in self.loyalty_service.list_coupon_lookups()]
        self._reload_combo(
            self._coupon_campaign_filter_combo, campaign_items, include_empty=True, empty_label="All"
        )
        self._reload_combo(
            self._coupon_usage_coupon_filter_combo, coupon_items, include_empty=True, empty_label="All"
        )

    def _clear_program_editor(self) -> None:
        self._selected_program_id = None
        self._program_table.clearSelection()
        self._program_name_input.clear()
        self._program_description_input.clear()
        self._program_points_per_currency_input.clear()
        self._program_currency_per_point_input.clear()
        self._program_min_purchase_input.clear()
        self._program_expiry_days_input.setValue(0)
        self._program_start_date_input.clear()
        self._program_end_date_input.clear()
        self._program_welcome_points_input.setValue(0)
        self._program_birthday_points_input.setValue(0)
        self._program_terms_input.clear()
        self._program_settings_json_input.clear()
        self._program_active_checkbox.setChecked(True)

    def _clear_tier_editor(self) -> None:
        self._selected_tier_id = None
        self._tier_table.clearSelection()
        self._tier_program_combo.setCurrentIndex(0)
        self._tier_name_input.clear()
        self._tier_code_input.clear()
        self._tier_description_input.clear()
        self._tier_level_input.setValue(1)
        self._tier_min_points_input.setValue(0)
        self._tier_min_annual_spending_input.clear()
        self._tier_points_multiplier_input.clear()
        self._tier_discount_percentage_input.clear()
        self._tier_display_order_input.setValue(0)
        self._tier_color_input.clear()
        self._tier_icon_input.clear()
        self._tier_special_benefits_input.clear()
        self._tier_active_checkbox.setChecked(True)

    def _clear_rule_editor(self) -> None:
        self._selected_rule_id = None
        self._rule_table.clearSelection()
        self._rule_program_combo.setCurrentIndex(0)
        self._rule_code_input.clear()
        self._rule_type_combo.setCurrentIndex(0)
        self._rule_priority_input.setValue(100)
        self._rule_config_json_input.clear()
        self._rule_description_input.clear()
        self._rule_active_checkbox.setChecked(True)

    def _clear_program_policy_editor(self) -> None:
        self._selected_program_policy_id = None
        self._program_policy_table.clearSelection()
        self._program_policy_program_combo.setCurrentIndex(0)
        self._program_policy_identifier_combo.setCurrentText("PHONE")
        self._program_policy_require_phone_checkbox.setChecked(True)
        self._program_policy_phone_prefix_input.clear()
        self._program_policy_void_policy_combo.setCurrentText("NONE")
        self._program_policy_integration_provider_combo.setCurrentText("LOCAL")
        self._program_policy_integration_json_input.clear()

    def _clear_redemption_policy_editor(self) -> None:
        self._selected_redemption_policy_id = None
        self._redemption_policy_table.clearSelection()
        self._redemption_policy_program_combo.setCurrentIndex(0)
        self._redemption_policy_max_share_input.clear()
        self._redemption_policy_min_points_input.setValue(0)
        self._redemption_policy_step_input.setValue(1)
        self._redemption_policy_partial_checkbox.setChecked(True)

    def _clear_customer_loyalty_editor(self) -> None:
        self._selected_customer_loyalty_id = None
        self._customer_loyalty_table.clearSelection()
        self._customer_loyalty_customer_combo.setCurrentIndex(0)
        self._customer_loyalty_program_combo.setCurrentIndex(0)
        self._reload_customer_loyalty_tier_combo()
        self._customer_loyalty_tier_combo.setCurrentIndex(0)
        self._customer_loyalty_card_input.clear()
        self._customer_loyalty_total_points_input.setValue(0)
        self._customer_loyalty_available_points_input.setValue(0)
        self._customer_loyalty_lifetime_points_input.setValue(0)
        self._customer_loyalty_points_to_expire_input.setValue(0)
        self._customer_loyalty_expiry_date_input.clear()
        self._customer_loyalty_enrollment_date_input.clear()
        self._customer_loyalty_last_activity_date_input.clear()
        self._customer_loyalty_total_purchases_input.setValue(0)
        self._customer_loyalty_total_spent_input.clear()
        self._customer_loyalty_annual_spent_input.clear()
        self._customer_loyalty_active_checkbox.setChecked(True)

    def _clear_transaction_editor(self) -> None:
        self._selected_transaction_id = None
        self._transaction_table.clearSelection()
        self._transaction_loyalty_combo.setCurrentIndex(0)
        self._transaction_customer_combo.setCurrentIndex(0)
        self._transaction_type_combo.setCurrentIndex(0)
        self._transaction_points_input.setValue(0)
        self._transaction_balance_after_input.clear()
        self._transaction_date_input.clear()
        self._transaction_expiry_date_input.clear()
        self._transaction_store_combo.setCurrentIndex(0)
        self._transaction_cashier_combo.setCurrentIndex(0)
        self._transaction_head_combo.setCurrentIndex(0)
        self._transaction_reference_input.clear()
        self._transaction_description_input.clear()
        self._transaction_notes_input.clear()

    def _open_operations_window(self) -> None:
        if self._operations_form is None:
            self._operations_form = LoyaltyOperationsForm(
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

    @staticmethod
    def _format_amount(value: Decimal | None) -> str:
        amount = Decimal("0") if value is None else Decimal(str(value))
        return f"{amount:.2f}"
