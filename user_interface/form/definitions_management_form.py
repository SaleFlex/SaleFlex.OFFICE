"""
Definitions management form with spreadsheet-style tabbed workspaces.

Tabs: Countries | Country Regions | Cities | Districts |
      Currencies | Currency Rates | Payment Types | VAT
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
    QPushButton,
    QSpinBox,
    QSplitter,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.definitions_management_service import (
    CityView,
    CountryRegionView,
    CountryView,
    CurrencyRateView,
    CurrencyView,
    DefinitionsManagementService,
    DistrictView,
    LookupItem,
    PaymentTypeView,
    TransactionDiscountTypeView,
    TransactionDocumentTypeView,
    VatView,
)
from settings.settings import Settings


class DefinitionsManagementForm(QWidget):
    """Manage all static definition tables through spreadsheet-style tabs."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = DefinitionsManagementService()
        self.setWindowTitle(f"{Settings().app_name} - Definitions Management")
        self.setMinimumSize(1400, 900)

        self._countries: list[CountryView] = []
        self._country_regions: list[CountryRegionView] = []
        self._cities: list[CityView] = []
        self._districts: list[DistrictView] = []
        self._currencies: list[CurrencyView] = []
        self._currency_rates: list[CurrencyRateView] = []
        self._payment_types: list[PaymentTypeView] = []
        self._vats: list[VatView] = []

        self._selected_country_id: str | None = None
        self._selected_region_id: str | None = None
        self._selected_city_id: str | None = None
        self._selected_district_id: str | None = None
        self._selected_currency_id: str | None = None
        self._selected_rate_id: str | None = None
        self._selected_payment_type_id: str | None = None
        self._selected_vat_id: str | None = None
        self._selected_doc_type_id: str | None = None
        self._selected_discount_type_id: str | None = None

        self._doc_types: list[TransactionDocumentTypeView] = []
        self._discount_types: list[TransactionDiscountTypeView] = []

        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        header = QLabel("Definitions Management Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}"
            f"  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)
        refresh_all_button = QPushButton("Refresh All")
        refresh_all_button.clicked.connect(self.refresh_all)
        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch(1)
        header_layout.addWidget(refresh_all_button)
        header_layout.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_countries_tab(), "Countries")
        self._tabs.addTab(self._build_country_regions_tab(), "Country Regions")
        self._tabs.addTab(self._build_cities_tab(), "Cities")
        self._tabs.addTab(self._build_districts_tab(), "Districts")
        self._tabs.addTab(self._build_currencies_tab(), "Currencies")
        self._tabs.addTab(self._build_currency_rates_tab(), "Currency Rates")
        self._tabs.addTab(self._build_payment_types_tab(), "Payment Types")
        self._tabs.addTab(self._build_vat_tab(), "VAT")
        self._tabs.addTab(self._build_transaction_settings_tab(), "Transaction Settings")

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)
        root.addLayout(header_layout)
        root.addWidget(subtitle)
        root.addWidget(self._tabs, stretch=1)
        root.addWidget(self._status_label)
        self.setLayout(root)

    # ------------------------------------------------------------------
    # Countries tab
    # ------------------------------------------------------------------

    def _build_countries_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._country_table = QTableWidget(0, 5)
        self._country_table.setHorizontalHeaderLabels(
            ["ID", "Name", "ISO Alpha-2", "ISO Alpha-3", "ISO Numeric"]
        )
        self._country_table.setColumnHidden(0, True)
        self._country_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._country_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._country_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._country_table.verticalHeader().setVisible(False)
        self._country_table.setAlternatingRowColors(True)
        self._country_table.itemSelectionChanged.connect(self._on_country_selected)

        splitter.addWidget(self._country_table)

        detail_group = QGroupBox("Country Detail")
        form = QFormLayout()
        self._country_name = QLineEdit()
        self._country_iso2 = QLineEdit()
        self._country_iso2.setMaxLength(2)
        self._country_iso3 = QLineEdit()
        self._country_iso3.setMaxLength(3)
        self._country_iso_num = QLineEdit()
        form.addRow("Name *", self._country_name)
        form.addRow("ISO Alpha-2 *", self._country_iso2)
        form.addRow("ISO Alpha-3", self._country_iso3)
        form.addRow("ISO Numeric", self._country_iso_num)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_country_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_country_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_country_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._country_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_countries)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([500, 260])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Country Regions tab
    # ------------------------------------------------------------------

    def _build_country_regions_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter by Country:"))
        self._region_country_filter = QComboBox()
        self._region_country_filter.currentIndexChanged.connect(self._load_country_regions)
        filter_row.addWidget(self._region_country_filter, stretch=1)

        self._region_table = QTableWidget(0, 8)
        self._region_table.setHorizontalHeaderLabels(
            ["ID", "Country", "ISO 3166-2", "Region Code", "Name", "Type", "Special", "Order"]
        )
        self._region_table.setColumnHidden(0, True)
        self._region_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._region_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._region_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._region_table.verticalHeader().setVisible(False)
        self._region_table.setAlternatingRowColors(True)
        self._region_table.itemSelectionChanged.connect(self._on_region_selected)

        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addLayout(filter_row)
        top_layout.addWidget(self._region_table)
        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)

        detail_group = QGroupBox("Country Region Detail")
        form = QFormLayout()
        self._region_country_combo = QComboBox()
        self._region_iso_3166_2 = QLineEdit()
        self._region_code = QLineEdit()
        self._region_name = QLineEdit()
        self._region_type = QLineEdit()
        self._region_has_special = QCheckBox("Has Special Requirements")
        self._region_display_order = QLineEdit()
        self._region_description = QLineEdit()
        form.addRow("Country *", self._region_country_combo)
        form.addRow("ISO 3166-2", self._region_iso_3166_2)
        form.addRow("Region Code *", self._region_code)
        form.addRow("Name *", self._region_name)
        form.addRow("Region Type", self._region_type)
        form.addRow("", self._region_has_special)
        form.addRow("Display Order", self._region_display_order)
        form.addRow("Description", self._region_description)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_region_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_region_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_region_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._region_clear_form)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([400, 360])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Cities tab
    # ------------------------------------------------------------------

    def _build_cities_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter by Country:"))
        self._city_country_filter = QComboBox()
        self._city_country_filter.currentIndexChanged.connect(self._load_cities)
        filter_row.addWidget(self._city_country_filter, stretch=1)

        self._city_table = QTableWidget(0, 6)
        self._city_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Code", "Short Name", "Numeric Code", "Country"]
        )
        self._city_table.setColumnHidden(0, True)
        self._city_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._city_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._city_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._city_table.verticalHeader().setVisible(False)
        self._city_table.setAlternatingRowColors(True)
        self._city_table.itemSelectionChanged.connect(self._on_city_selected)

        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addLayout(filter_row)
        top_layout.addWidget(self._city_table)
        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)

        detail_group = QGroupBox("City Detail")
        form = QFormLayout()
        self._city_name = QLineEdit()
        self._city_code = QLineEdit()
        self._city_short_name = QLineEdit()
        self._city_numeric_code = QLineEdit()
        self._city_country_combo = QComboBox()
        form.addRow("Name *", self._city_name)
        form.addRow("Code *", self._city_code)
        form.addRow("Short Name", self._city_short_name)
        form.addRow("Numeric Code", self._city_numeric_code)
        form.addRow("Country *", self._city_country_combo)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_city_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_city_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_city_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._city_clear_form)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([440, 280])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Districts tab
    # ------------------------------------------------------------------

    def _build_districts_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter by City:"))
        self._district_city_filter = QComboBox()
        self._district_city_filter.currentIndexChanged.connect(self._load_districts)
        filter_row.addWidget(self._district_city_filter, stretch=1)

        self._district_table = QTableWidget(0, 6)
        self._district_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Code", "Short Name", "Numeric Code", "City"]
        )
        self._district_table.setColumnHidden(0, True)
        self._district_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._district_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._district_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._district_table.verticalHeader().setVisible(False)
        self._district_table.setAlternatingRowColors(True)
        self._district_table.itemSelectionChanged.connect(self._on_district_selected)

        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addLayout(filter_row)
        top_layout.addWidget(self._district_table)
        top_widget.setLayout(top_layout)
        splitter.addWidget(top_widget)

        detail_group = QGroupBox("District Detail")
        form = QFormLayout()
        self._district_name = QLineEdit()
        self._district_code = QLineEdit()
        self._district_short_name = QLineEdit()
        self._district_numeric_code = QLineEdit()
        self._district_city_combo = QComboBox()
        form.addRow("Name *", self._district_name)
        form.addRow("Code *", self._district_code)
        form.addRow("Short Name", self._district_short_name)
        form.addRow("Numeric Code", self._district_numeric_code)
        form.addRow("City *", self._district_city_combo)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_district_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_district_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_district_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._district_clear_form)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([440, 260])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Currencies tab
    # ------------------------------------------------------------------

    def _build_currencies_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._currency_table = QTableWidget(0, 8)
        self._currency_table.setHorizontalHeaderLabels(
            ["ID", "No", "Name", "Code", "Sign", "Direction", "Symbol", "Decimals"]
        )
        self._currency_table.setColumnHidden(0, True)
        self._currency_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._currency_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._currency_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._currency_table.verticalHeader().setVisible(False)
        self._currency_table.setAlternatingRowColors(True)
        self._currency_table.itemSelectionChanged.connect(self._on_currency_selected)
        splitter.addWidget(self._currency_table)

        detail_group = QGroupBox("Currency Detail")
        form = QFormLayout()
        self._currency_no = QSpinBox()
        self._currency_no.setRange(0, 9999)
        self._currency_name = QLineEdit()
        self._currency_code_field = QLineEdit()
        self._currency_sign = QLineEdit()
        self._currency_sign.setMaxLength(10)
        self._currency_sign_direction = QComboBox()
        self._currency_sign_direction.addItems(["LEFT", "RIGHT"])
        self._currency_symbol = QLineEdit()
        self._currency_symbol.setMaxLength(10)
        self._currency_decimal_places = QSpinBox()
        self._currency_decimal_places.setRange(0, 4)
        self._currency_decimal_places.setValue(2)
        form.addRow("No *", self._currency_no)
        form.addRow("Name *", self._currency_name)
        form.addRow("Currency Code", self._currency_code_field)
        form.addRow("Sign", self._currency_sign)
        form.addRow("Sign Direction", self._currency_sign_direction)
        form.addRow("Symbol", self._currency_symbol)
        form.addRow("Decimal Places", self._currency_decimal_places)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_currency_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_currency_update)
        btn_del = QPushButton("Deactivate")
        btn_del.clicked.connect(self._on_currency_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._currency_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_currencies)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([420, 340])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Currency Rates tab
    # ------------------------------------------------------------------

    def _build_currency_rates_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._rate_table = QTableWidget(0, 5)
        self._rate_table.setHorizontalHeaderLabels(
            ["ID", "Base Currency", "Target Currency", "Rate", ""]
        )
        self._rate_table.setColumnHidden(0, True)
        self._rate_table.setColumnHidden(4, True)
        self._rate_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._rate_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._rate_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rate_table.verticalHeader().setVisible(False)
        self._rate_table.setAlternatingRowColors(True)
        self._rate_table.itemSelectionChanged.connect(self._on_rate_selected)
        splitter.addWidget(self._rate_table)

        detail_group = QGroupBox("Exchange Rate Detail")
        form = QFormLayout()
        self._rate_base_combo = QComboBox()
        self._rate_target_combo = QComboBox()
        self._rate_value = QDoubleSpinBox()
        self._rate_value.setRange(0.0, 9_999_999.0)
        self._rate_value.setDecimals(4)
        self._rate_value.setSingleStep(0.0001)
        form.addRow("Base Currency *", self._rate_base_combo)
        form.addRow("Target Currency *", self._rate_target_combo)
        form.addRow("Rate (1 base = ? target) *", self._rate_value)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_rate_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_rate_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_rate_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._rate_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_currency_rates)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([460, 240])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Payment Types tab
    # ------------------------------------------------------------------

    def _build_payment_types_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._pt_table = QTableWidget(0, 5)
        self._pt_table.setHorizontalHeaderLabels(
            ["ID", "No", "Name", "Description", "Culture Info"]
        )
        self._pt_table.setColumnHidden(0, True)
        self._pt_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._pt_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._pt_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._pt_table.verticalHeader().setVisible(False)
        self._pt_table.setAlternatingRowColors(True)
        self._pt_table.itemSelectionChanged.connect(self._on_pt_selected)
        splitter.addWidget(self._pt_table)

        detail_group = QGroupBox("Payment Type Detail")
        form = QFormLayout()
        self._pt_no = QSpinBox()
        self._pt_no.setRange(0, 9999)
        self._pt_name = QLineEdit()
        self._pt_description = QLineEdit()
        self._pt_culture_info = QLineEdit()
        self._pt_culture_info.setPlaceholderText("e.g. en-GB")
        form.addRow("No *", self._pt_no)
        form.addRow("Name *", self._pt_name)
        form.addRow("Description", self._pt_description)
        form.addRow("Culture Info", self._pt_culture_info)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_pt_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_pt_update)
        btn_del = QPushButton("Deactivate")
        btn_del.clicked.connect(self._on_pt_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._pt_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_payment_types)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([460, 240])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # VAT tab
    # ------------------------------------------------------------------

    def _build_vat_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._vat_table = QTableWidget(0, 5)
        self._vat_table.setHorizontalHeaderLabels(
            ["ID", "No", "Name", "Rate (%)", "Description"]
        )
        self._vat_table.setColumnHidden(0, True)
        self._vat_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._vat_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._vat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._vat_table.verticalHeader().setVisible(False)
        self._vat_table.setAlternatingRowColors(True)
        self._vat_table.itemSelectionChanged.connect(self._on_vat_selected)
        splitter.addWidget(self._vat_table)

        detail_group = QGroupBox("VAT Detail")
        form = QFormLayout()
        self._vat_no = QSpinBox()
        self._vat_no.setRange(0, 999)
        self._vat_name = QLineEdit()
        self._vat_rate = QDoubleSpinBox()
        self._vat_rate.setRange(0.0, 100.0)
        self._vat_rate.setDecimals(2)
        self._vat_rate.setSuffix(" %")
        self._vat_description = QLineEdit()
        form.addRow("No *", self._vat_no)
        form.addRow("Name *", self._vat_name)
        form.addRow("Rate *", self._vat_rate)
        form.addRow("Description", self._vat_description)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_vat_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_vat_update)
        btn_del = QPushButton("Deactivate")
        btn_del.clicked.connect(self._on_vat_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._vat_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_vats)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([460, 240])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Transaction Settings tab
    # ------------------------------------------------------------------

    def _build_transaction_settings_tab(self) -> QWidget:
        """Two sub-tabs: Document Types and Discount Types."""
        sub_tabs = QTabWidget()
        sub_tabs.addTab(self._build_doc_types_sub_tab(), "Document Types")
        sub_tabs.addTab(self._build_discount_types_sub_tab(), "Discount Types")

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(sub_tabs)
        container.setLayout(layout)
        return container

    def _build_doc_types_sub_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._doc_type_table = QTableWidget(0, 5)
        self._doc_type_table.setHorizontalHeaderLabels(
            ["ID", "No", "Name", "Display Name", "Description"]
        )
        self._doc_type_table.setColumnHidden(0, True)
        self._doc_type_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._doc_type_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._doc_type_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._doc_type_table.verticalHeader().setVisible(False)
        self._doc_type_table.setAlternatingRowColors(True)
        self._doc_type_table.itemSelectionChanged.connect(self._on_doc_type_selected)
        splitter.addWidget(self._doc_type_table)

        detail_group = QGroupBox("Document Type Detail")
        form = QFormLayout()
        self._doc_type_no = QSpinBox()
        self._doc_type_no.setRange(0, 9999)
        self._doc_type_name = QLineEdit()
        self._doc_type_display_name = QLineEdit()
        self._doc_type_description = QLineEdit()
        form.addRow("No *", self._doc_type_no)
        form.addRow("Name *", self._doc_type_name)
        form.addRow("Display Name", self._doc_type_display_name)
        form.addRow("Description", self._doc_type_description)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_doc_type_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_doc_type_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_doc_type_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._doc_type_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_transaction_document_types)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([460, 240])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    def _build_discount_types_sub_tab(self) -> QWidget:
        splitter = QSplitter(Qt.Vertical)

        self._discount_type_table = QTableWidget(0, 5)
        self._discount_type_table.setHorizontalHeaderLabels(
            ["ID", "Code", "Name", "Display Name", "Description"]
        )
        self._discount_type_table.setColumnHidden(0, True)
        self._discount_type_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._discount_type_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._discount_type_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._discount_type_table.verticalHeader().setVisible(False)
        self._discount_type_table.setAlternatingRowColors(True)
        self._discount_type_table.itemSelectionChanged.connect(self._on_discount_type_selected)
        splitter.addWidget(self._discount_type_table)

        detail_group = QGroupBox("Discount Type Detail")
        form = QFormLayout()
        self._discount_type_code = QLineEdit()
        self._discount_type_code.setMaxLength(50)
        self._discount_type_name = QLineEdit()
        self._discount_type_display_name = QLineEdit()
        self._discount_type_description = QLineEdit()
        form.addRow("Code *", self._discount_type_code)
        form.addRow("Name *", self._discount_type_name)
        form.addRow("Display Name", self._discount_type_display_name)
        form.addRow("Description", self._discount_type_description)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._on_discount_type_add)
        btn_upd = QPushButton("Update")
        btn_upd.clicked.connect(self._on_discount_type_update)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self._on_discount_type_delete)
        btn_clr = QPushButton("Clear")
        btn_clr.clicked.connect(self._discount_type_clear_form)
        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self._load_transaction_discount_types)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_upd)
        btn_row.addWidget(btn_del)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_clr)
        btn_row.addWidget(btn_ref)

        detail_layout = QVBoxLayout()
        detail_layout.addLayout(form)
        detail_layout.addLayout(btn_row)
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        splitter.setSizes([460, 240])

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------

    def refresh_all(self) -> None:
        """Reload all tabs from the database."""
        self._load_countries()
        self._reload_country_filter_combos()
        self._load_country_regions()
        self._reload_city_filter_combos()
        self._load_cities()
        self._reload_district_filter_combos()
        self._load_districts()
        self._load_currencies()
        self._reload_currency_combos()
        self._load_currency_rates()
        self._load_payment_types()
        self._load_vats()
        self._load_transaction_document_types()
        self._load_transaction_discount_types()

    def _load_countries(self) -> None:
        self._countries = self.service.list_countries()
        self._country_table.setRowCount(len(self._countries))
        for i, row in enumerate(self._countries):
            self._country_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._country_table.setItem(i, 1, QTableWidgetItem(row.name))
            self._country_table.setItem(i, 2, QTableWidgetItem(row.iso_alpha2))
            self._country_table.setItem(i, 3, QTableWidgetItem(row.iso_alpha3))
            self._country_table.setItem(i, 4, QTableWidgetItem(str(row.iso_numeric) if row.iso_numeric else ""))
        self._country_table.resizeColumnsToContents()
        self._country_table.horizontalHeader().setStretchLastSection(True)

    def _reload_country_filter_combos(self) -> None:
        lookups = self.service.list_country_lookups()
        for combo in (self._region_country_filter, self._city_country_filter):
            current_id = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("All Countries", None)
            for item in lookups:
                combo.addItem(item.label, item.id)
            if current_id:
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)
        for combo in (self._region_country_combo, self._city_country_combo):
            current_id = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for item in lookups:
                combo.addItem(item.label, item.id)
            if current_id:
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _load_country_regions(self) -> None:
        country_id = self._region_country_filter.currentData()
        self._country_regions = self.service.list_country_regions(country_id=country_id)
        self._region_table.setRowCount(len(self._country_regions))
        for i, row in enumerate(self._country_regions):
            self._region_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._region_table.setItem(i, 1, QTableWidgetItem(row.country_name))
            self._region_table.setItem(i, 2, QTableWidgetItem(row.iso_3166_2))
            self._region_table.setItem(i, 3, QTableWidgetItem(row.region_code))
            self._region_table.setItem(i, 4, QTableWidgetItem(row.name))
            self._region_table.setItem(i, 5, QTableWidgetItem(row.region_type))
            self._region_table.setItem(i, 6, QTableWidgetItem("Yes" if row.has_special_requirements else "No"))
            self._region_table.setItem(i, 7, QTableWidgetItem(row.display_order))
        self._region_table.resizeColumnsToContents()
        self._region_table.horizontalHeader().setStretchLastSection(True)

    def _reload_city_filter_combos(self) -> None:
        lookups = self.service.list_city_lookups()
        for combo in (self._district_city_filter, self._district_city_combo):
            current_id = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if combo is self._district_city_filter:
                combo.addItem("All Cities", None)
            for item in lookups:
                combo.addItem(item.label, item.id)
            if current_id:
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _load_cities(self) -> None:
        country_id = self._city_country_filter.currentData()
        self._cities = self.service.list_cities(country_id=country_id)
        self._city_table.setRowCount(len(self._cities))
        for i, row in enumerate(self._cities):
            self._city_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._city_table.setItem(i, 1, QTableWidgetItem(row.name))
            self._city_table.setItem(i, 2, QTableWidgetItem(row.code))
            self._city_table.setItem(i, 3, QTableWidgetItem(row.short_name))
            self._city_table.setItem(i, 4, QTableWidgetItem(str(row.numeric_code) if row.numeric_code else ""))
            self._city_table.setItem(i, 5, QTableWidgetItem(row.country_name))
        self._city_table.resizeColumnsToContents()
        self._city_table.horizontalHeader().setStretchLastSection(True)

    def _reload_district_filter_combos(self) -> None:
        lookups = self.service.list_city_lookups()
        for combo in (self._district_city_filter, self._district_city_combo):
            current_id = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            if combo is self._district_city_filter:
                combo.addItem("All Cities", None)
            for item in lookups:
                combo.addItem(item.label, item.id)
            if current_id:
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _load_districts(self) -> None:
        city_id = self._district_city_filter.currentData()
        self._districts = self.service.list_districts(city_id=city_id)
        self._district_table.setRowCount(len(self._districts))
        for i, row in enumerate(self._districts):
            self._district_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._district_table.setItem(i, 1, QTableWidgetItem(row.name))
            self._district_table.setItem(i, 2, QTableWidgetItem(row.code))
            self._district_table.setItem(i, 3, QTableWidgetItem(row.short_name))
            self._district_table.setItem(i, 4, QTableWidgetItem(str(row.numeric_code) if row.numeric_code else ""))
            self._district_table.setItem(i, 5, QTableWidgetItem(row.city_name))
        self._district_table.resizeColumnsToContents()
        self._district_table.horizontalHeader().setStretchLastSection(True)

    def _load_currencies(self) -> None:
        self._currencies = self.service.list_currencies()
        self._currency_table.setRowCount(len(self._currencies))
        for i, row in enumerate(self._currencies):
            self._currency_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._currency_table.setItem(i, 1, QTableWidgetItem(str(row.no)))
            self._currency_table.setItem(i, 2, QTableWidgetItem(row.name))
            self._currency_table.setItem(i, 3, QTableWidgetItem(str(row.currency_code) if row.currency_code else ""))
            self._currency_table.setItem(i, 4, QTableWidgetItem(row.sign))
            self._currency_table.setItem(i, 5, QTableWidgetItem(row.sign_direction))
            self._currency_table.setItem(i, 6, QTableWidgetItem(row.currency_symbol))
            self._currency_table.setItem(i, 7, QTableWidgetItem(str(row.decimal_places)))
        self._currency_table.resizeColumnsToContents()
        self._currency_table.horizontalHeader().setStretchLastSection(True)

    def _reload_currency_combos(self) -> None:
        lookups = self.service.list_currency_lookups()
        for combo in (self._rate_base_combo, self._rate_target_combo):
            current_id = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for item in lookups:
                combo.addItem(item.label, item.id)
            if current_id:
                idx = combo.findData(current_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def _load_currency_rates(self) -> None:
        self._currency_rates = self.service.list_currency_rates()
        self._rate_table.setRowCount(len(self._currency_rates))
        for i, row in enumerate(self._currency_rates):
            self._rate_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._rate_table.setItem(i, 1, QTableWidgetItem(row.base_currency_name))
            self._rate_table.setItem(i, 2, QTableWidgetItem(row.target_currency_name))
            self._rate_table.setItem(i, 3, QTableWidgetItem(f"{row.rate:.4f}"))
            self._rate_table.setItem(i, 4, QTableWidgetItem(row.fk_base_currency_id))
        self._rate_table.resizeColumnsToContents()
        self._rate_table.horizontalHeader().setStretchLastSection(True)

    def _load_payment_types(self) -> None:
        self._payment_types = self.service.list_payment_types()
        self._pt_table.setRowCount(len(self._payment_types))
        for i, row in enumerate(self._payment_types):
            self._pt_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._pt_table.setItem(i, 1, QTableWidgetItem(str(row.type_no)))
            self._pt_table.setItem(i, 2, QTableWidgetItem(row.type_name))
            self._pt_table.setItem(i, 3, QTableWidgetItem(row.type_description))
            self._pt_table.setItem(i, 4, QTableWidgetItem(row.culture_info))
        self._pt_table.resizeColumnsToContents()
        self._pt_table.horizontalHeader().setStretchLastSection(True)

    def _load_vats(self) -> None:
        self._vats = self.service.list_vats()
        self._vat_table.setRowCount(len(self._vats))
        for i, row in enumerate(self._vats):
            self._vat_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._vat_table.setItem(i, 1, QTableWidgetItem(str(row.no)))
            self._vat_table.setItem(i, 2, QTableWidgetItem(row.name))
            self._vat_table.setItem(i, 3, QTableWidgetItem(f"{row.rate:.2f}"))
            self._vat_table.setItem(i, 4, QTableWidgetItem(row.description))
        self._vat_table.resizeColumnsToContents()
        self._vat_table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Selection handlers
    # ------------------------------------------------------------------

    def _on_country_selected(self) -> None:
        rows = self._country_table.selectedItems()
        if not rows:
            return
        row_idx = self._country_table.currentRow()
        self._selected_country_id = self._country_table.item(row_idx, 0).text()
        record = next((c for c in self._countries if c.id == self._selected_country_id), None)
        if record is None:
            return
        self._country_name.setText(record.name)
        self._country_iso2.setText(record.iso_alpha2)
        self._country_iso3.setText(record.iso_alpha3)
        self._country_iso_num.setText(str(record.iso_numeric) if record.iso_numeric else "")

    def _on_region_selected(self) -> None:
        rows = self._region_table.selectedItems()
        if not rows:
            return
        row_idx = self._region_table.currentRow()
        self._selected_region_id = self._region_table.item(row_idx, 0).text()
        record = next((r for r in self._country_regions if r.id == self._selected_region_id), None)
        if record is None:
            return
        self._set_combo_by_id(self._region_country_combo, record.fk_country_id)
        self._region_iso_3166_2.setText(record.iso_3166_2)
        self._region_code.setText(record.region_code)
        self._region_name.setText(record.name)
        self._region_type.setText(record.region_type)
        self._region_has_special.setChecked(record.has_special_requirements)
        self._region_display_order.setText(record.display_order)
        self._region_description.setText(record.description)

    def _on_city_selected(self) -> None:
        rows = self._city_table.selectedItems()
        if not rows:
            return
        row_idx = self._city_table.currentRow()
        self._selected_city_id = self._city_table.item(row_idx, 0).text()
        record = next((c for c in self._cities if c.id == self._selected_city_id), None)
        if record is None:
            return
        self._city_name.setText(record.name)
        self._city_code.setText(record.code)
        self._city_short_name.setText(record.short_name)
        self._city_numeric_code.setText(str(record.numeric_code) if record.numeric_code else "")
        self._set_combo_by_id(self._city_country_combo, record.fk_country_id)

    def _on_district_selected(self) -> None:
        rows = self._district_table.selectedItems()
        if not rows:
            return
        row_idx = self._district_table.currentRow()
        self._selected_district_id = self._district_table.item(row_idx, 0).text()
        record = next((d for d in self._districts if d.id == self._selected_district_id), None)
        if record is None:
            return
        self._district_name.setText(record.name)
        self._district_code.setText(record.code)
        self._district_short_name.setText(record.short_name)
        self._district_numeric_code.setText(str(record.numeric_code) if record.numeric_code else "")
        self._set_combo_by_id(self._district_city_combo, record.fk_city_id)

    def _on_currency_selected(self) -> None:
        rows = self._currency_table.selectedItems()
        if not rows:
            return
        row_idx = self._currency_table.currentRow()
        self._selected_currency_id = self._currency_table.item(row_idx, 0).text()
        record = next((c for c in self._currencies if c.id == self._selected_currency_id), None)
        if record is None:
            return
        self._currency_no.setValue(record.no)
        self._currency_name.setText(record.name)
        self._currency_code_field.setText(str(record.currency_code) if record.currency_code else "")
        self._currency_sign.setText(record.sign)
        idx = self._currency_sign_direction.findText(record.sign_direction)
        if idx >= 0:
            self._currency_sign_direction.setCurrentIndex(idx)
        self._currency_symbol.setText(record.currency_symbol)
        self._currency_decimal_places.setValue(record.decimal_places)

    def _on_rate_selected(self) -> None:
        rows = self._rate_table.selectedItems()
        if not rows:
            return
        row_idx = self._rate_table.currentRow()
        self._selected_rate_id = self._rate_table.item(row_idx, 0).text()
        record = next((r for r in self._currency_rates if r.id == self._selected_rate_id), None)
        if record is None:
            return
        self._set_combo_by_id(self._rate_base_combo, record.fk_base_currency_id)
        self._set_combo_by_id(self._rate_target_combo, record.fk_target_currency_id)
        self._rate_value.setValue(float(record.rate))

    def _on_pt_selected(self) -> None:
        rows = self._pt_table.selectedItems()
        if not rows:
            return
        row_idx = self._pt_table.currentRow()
        self._selected_payment_type_id = self._pt_table.item(row_idx, 0).text()
        record = next((p for p in self._payment_types if p.id == self._selected_payment_type_id), None)
        if record is None:
            return
        self._pt_no.setValue(record.type_no)
        self._pt_name.setText(record.type_name)
        self._pt_description.setText(record.type_description)
        self._pt_culture_info.setText(record.culture_info)

    def _on_vat_selected(self) -> None:
        rows = self._vat_table.selectedItems()
        if not rows:
            return
        row_idx = self._vat_table.currentRow()
        self._selected_vat_id = self._vat_table.item(row_idx, 0).text()
        record = next((v for v in self._vats if v.id == self._selected_vat_id), None)
        if record is None:
            return
        self._vat_no.setValue(record.no)
        self._vat_name.setText(record.name)
        self._vat_rate.setValue(float(record.rate))
        self._vat_description.setText(record.description)

    # ------------------------------------------------------------------
    # CRUD action handlers – Countries
    # ------------------------------------------------------------------

    def _on_country_add(self) -> None:
        data = self._collect_country_data()
        if not data:
            return
        result = self.service.add_country(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_countries()
            self._reload_country_filter_combos()
            self._country_clear_form()

    def _on_country_update(self) -> None:
        if not self._selected_country_id:
            self._show_status(False, "Select a country row first.")
            return
        data = self._collect_country_data()
        if not data:
            return
        result = self.service.update_country(self._selected_country_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_countries()
            self._reload_country_filter_combos()

    def _on_country_delete(self) -> None:
        if not self._selected_country_id:
            self._show_status(False, "Select a country row first.")
            return
        if not self._confirm("Delete country? This may fail if cities or regions reference it."):
            return
        result = self.service.delete_country(self._selected_country_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_country_id = None
            self._load_countries()
            self._reload_country_filter_combos()
            self._country_clear_form()

    def _collect_country_data(self) -> dict | None:
        name = self._country_name.text().strip()
        iso2 = self._country_iso2.text().strip().upper()
        if not name or not iso2:
            self._show_status(False, "Name and ISO Alpha-2 are required.")
            return None
        return {
            "name": name,
            "iso_alpha2": iso2,
            "iso_alpha3": self._country_iso3.text().strip().upper() or None,
            "iso_numeric": self._country_iso_num.text().strip() or None,
        }

    def _country_clear_form(self) -> None:
        self._selected_country_id = None
        self._country_name.clear()
        self._country_iso2.clear()
        self._country_iso3.clear()
        self._country_iso_num.clear()

    # ------------------------------------------------------------------
    # CRUD action handlers – Country Regions
    # ------------------------------------------------------------------

    def _on_region_add(self) -> None:
        data = self._collect_region_data()
        if not data:
            return
        result = self.service.add_country_region(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_country_regions()
            self._region_clear_form()

    def _on_region_update(self) -> None:
        if not self._selected_region_id:
            self._show_status(False, "Select a region row first.")
            return
        data = self._collect_region_data()
        if not data:
            return
        result = self.service.update_country_region(self._selected_region_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_country_regions()

    def _on_region_delete(self) -> None:
        if not self._selected_region_id:
            self._show_status(False, "Select a region row first.")
            return
        if not self._confirm("Delete country region?"):
            return
        result = self.service.delete_country_region(self._selected_region_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_region_id = None
            self._load_country_regions()
            self._region_clear_form()

    def _collect_region_data(self) -> dict | None:
        country_id = self._region_country_combo.currentData()
        code = self._region_code.text().strip()
        name = self._region_name.text().strip()
        if not country_id or not code or not name:
            self._show_status(False, "Country, Region Code, and Name are required.")
            return None
        return {
            "fk_country_id": country_id,
            "iso_3166_2": self._region_iso_3166_2.text().strip() or None,
            "region_code": code,
            "name": name,
            "region_type": self._region_type.text().strip() or None,
            "has_special_requirements": self._region_has_special.isChecked(),
            "display_order": self._region_display_order.text().strip() or None,
            "description": self._region_description.text().strip() or None,
        }

    def _region_clear_form(self) -> None:
        self._selected_region_id = None
        self._region_iso_3166_2.clear()
        self._region_code.clear()
        self._region_name.clear()
        self._region_type.clear()
        self._region_has_special.setChecked(False)
        self._region_display_order.clear()
        self._region_description.clear()

    # ------------------------------------------------------------------
    # CRUD action handlers – Cities
    # ------------------------------------------------------------------

    def _on_city_add(self) -> None:
        data = self._collect_city_data()
        if not data:
            return
        result = self.service.add_city(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_cities()
            self._reload_city_filter_combos()
            self._reload_district_filter_combos()
            self._city_clear_form()

    def _on_city_update(self) -> None:
        if not self._selected_city_id:
            self._show_status(False, "Select a city row first.")
            return
        data = self._collect_city_data()
        if not data:
            return
        result = self.service.update_city(self._selected_city_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_cities()
            self._reload_city_filter_combos()
            self._reload_district_filter_combos()

    def _on_city_delete(self) -> None:
        if not self._selected_city_id:
            self._show_status(False, "Select a city row first.")
            return
        if not self._confirm("Delete city? This may fail if districts reference it."):
            return
        result = self.service.delete_city(self._selected_city_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_city_id = None
            self._load_cities()
            self._reload_city_filter_combos()
            self._reload_district_filter_combos()
            self._city_clear_form()

    def _collect_city_data(self) -> dict | None:
        name = self._city_name.text().strip()
        code = self._city_code.text().strip()
        country_id = self._city_country_combo.currentData()
        if not name or not code or not country_id:
            self._show_status(False, "Name, Code, and Country are required.")
            return None
        return {
            "name": name,
            "code": code,
            "short_name": self._city_short_name.text().strip() or None,
            "numeric_code": self._city_numeric_code.text().strip() or None,
            "fk_country_id": country_id,
        }

    def _city_clear_form(self) -> None:
        self._selected_city_id = None
        self._city_name.clear()
        self._city_code.clear()
        self._city_short_name.clear()
        self._city_numeric_code.clear()

    # ------------------------------------------------------------------
    # CRUD action handlers – Districts
    # ------------------------------------------------------------------

    def _on_district_add(self) -> None:
        data = self._collect_district_data()
        if not data:
            return
        result = self.service.add_district(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_districts()
            self._district_clear_form()

    def _on_district_update(self) -> None:
        if not self._selected_district_id:
            self._show_status(False, "Select a district row first.")
            return
        data = self._collect_district_data()
        if not data:
            return
        result = self.service.update_district(self._selected_district_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_districts()

    def _on_district_delete(self) -> None:
        if not self._selected_district_id:
            self._show_status(False, "Select a district row first.")
            return
        if not self._confirm("Delete district?"):
            return
        result = self.service.delete_district(self._selected_district_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_district_id = None
            self._load_districts()
            self._district_clear_form()

    def _collect_district_data(self) -> dict | None:
        name = self._district_name.text().strip()
        code = self._district_code.text().strip()
        city_id = self._district_city_combo.currentData()
        if not name or not code or not city_id:
            self._show_status(False, "Name, Code, and City are required.")
            return None
        return {
            "name": name,
            "code": code,
            "short_name": self._district_short_name.text().strip() or None,
            "numeric_code": self._district_numeric_code.text().strip() or None,
            "fk_city_id": city_id,
        }

    def _district_clear_form(self) -> None:
        self._selected_district_id = None
        self._district_name.clear()
        self._district_code.clear()
        self._district_short_name.clear()
        self._district_numeric_code.clear()

    # ------------------------------------------------------------------
    # CRUD action handlers – Currencies
    # ------------------------------------------------------------------

    def _on_currency_add(self) -> None:
        data = self._collect_currency_data()
        if not data:
            return
        result = self.service.add_currency(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_currencies()
            self._reload_currency_combos()
            self._currency_clear_form()

    def _on_currency_update(self) -> None:
        if not self._selected_currency_id:
            self._show_status(False, "Select a currency row first.")
            return
        data = self._collect_currency_data()
        if not data:
            return
        result = self.service.update_currency(self._selected_currency_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_currencies()
            self._reload_currency_combos()

    def _on_currency_delete(self) -> None:
        if not self._selected_currency_id:
            self._show_status(False, "Select a currency row first.")
            return
        if not self._confirm("Deactivate this currency?"):
            return
        result = self.service.soft_delete_currency(self._selected_currency_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_currency_id = None
            self._load_currencies()
            self._reload_currency_combos()
            self._currency_clear_form()

    def _collect_currency_data(self) -> dict | None:
        name = self._currency_name.text().strip()
        if not name:
            self._show_status(False, "Name is required.")
            return None
        return {
            "no": self._currency_no.value(),
            "name": name,
            "currency_code": self._currency_code_field.text().strip() or None,
            "sign": self._currency_sign.text().strip() or None,
            "sign_direction": self._currency_sign_direction.currentText(),
            "currency_symbol": self._currency_symbol.text().strip() or None,
            "decimal_places": self._currency_decimal_places.value(),
        }

    def _currency_clear_form(self) -> None:
        self._selected_currency_id = None
        self._currency_no.setValue(0)
        self._currency_name.clear()
        self._currency_code_field.clear()
        self._currency_sign.clear()
        self._currency_sign_direction.setCurrentIndex(0)
        self._currency_symbol.clear()
        self._currency_decimal_places.setValue(2)

    # ------------------------------------------------------------------
    # CRUD action handlers – Currency Rates
    # ------------------------------------------------------------------

    def _on_rate_add(self) -> None:
        data = self._collect_rate_data()
        if not data:
            return
        result = self.service.add_currency_rate(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_currency_rates()
            self._rate_clear_form()

    def _on_rate_update(self) -> None:
        if not self._selected_rate_id:
            self._show_status(False, "Select a rate row first.")
            return
        data = self._collect_rate_data()
        if not data:
            return
        result = self.service.update_currency_rate(self._selected_rate_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_currency_rates()

    def _on_rate_delete(self) -> None:
        if not self._selected_rate_id:
            self._show_status(False, "Select a rate row first.")
            return
        if not self._confirm("Delete this exchange rate?"):
            return
        result = self.service.soft_delete_currency_rate(self._selected_rate_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_rate_id = None
            self._load_currency_rates()
            self._rate_clear_form()

    def _collect_rate_data(self) -> dict | None:
        base_id = self._rate_base_combo.currentData()
        target_id = self._rate_target_combo.currentData()
        if not base_id or not target_id:
            self._show_status(False, "Base and target currencies are required.")
            return None
        if base_id == target_id:
            self._show_status(False, "Base and target currencies must be different.")
            return None
        return {
            "fk_base_currency_id": base_id,
            "fk_target_currency_id": target_id,
            "rate": str(self._rate_value.value()),
        }

    def _rate_clear_form(self) -> None:
        self._selected_rate_id = None
        self._rate_value.setValue(1.0)

    # ------------------------------------------------------------------
    # CRUD action handlers – Payment Types
    # ------------------------------------------------------------------

    def _on_pt_add(self) -> None:
        data = self._collect_pt_data()
        if not data:
            return
        result = self.service.add_payment_type(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_payment_types()
            self._pt_clear_form()

    def _on_pt_update(self) -> None:
        if not self._selected_payment_type_id:
            self._show_status(False, "Select a payment type row first.")
            return
        data = self._collect_pt_data()
        if not data:
            return
        result = self.service.update_payment_type(self._selected_payment_type_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_payment_types()

    def _on_pt_delete(self) -> None:
        if not self._selected_payment_type_id:
            self._show_status(False, "Select a payment type row first.")
            return
        if not self._confirm("Deactivate this payment type?"):
            return
        result = self.service.soft_delete_payment_type(self._selected_payment_type_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_payment_type_id = None
            self._load_payment_types()
            self._pt_clear_form()

    def _collect_pt_data(self) -> dict | None:
        name = self._pt_name.text().strip()
        if not name:
            self._show_status(False, "Name is required.")
            return None
        return {
            "type_no": self._pt_no.value(),
            "type_name": name,
            "type_description": self._pt_description.text().strip() or None,
            "culture_info": self._pt_culture_info.text().strip() or "en-GB",
        }

    def _pt_clear_form(self) -> None:
        self._selected_payment_type_id = None
        self._pt_no.setValue(0)
        self._pt_name.clear()
        self._pt_description.clear()
        self._pt_culture_info.clear()

    # ------------------------------------------------------------------
    # CRUD action handlers – VAT
    # ------------------------------------------------------------------

    def _on_vat_add(self) -> None:
        data = self._collect_vat_data()
        if not data:
            return
        result = self.service.add_vat(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_vats()
            self._vat_clear_form()

    def _on_vat_update(self) -> None:
        if not self._selected_vat_id:
            self._show_status(False, "Select a VAT row first.")
            return
        data = self._collect_vat_data()
        if not data:
            return
        result = self.service.update_vat(self._selected_vat_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_vats()

    def _on_vat_delete(self) -> None:
        if not self._selected_vat_id:
            self._show_status(False, "Select a VAT row first.")
            return
        if not self._confirm("Deactivate this VAT rate?"):
            return
        result = self.service.soft_delete_vat(self._selected_vat_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_vat_id = None
            self._load_vats()
            self._vat_clear_form()

    def _collect_vat_data(self) -> dict | None:
        name = self._vat_name.text().strip()
        if not name:
            self._show_status(False, "Name is required.")
            return None
        return {
            "no": self._vat_no.value(),
            "name": name,
            "rate": str(self._vat_rate.value()),
            "description": self._vat_description.text().strip() or None,
        }

    def _vat_clear_form(self) -> None:
        self._selected_vat_id = None
        self._vat_no.setValue(0)
        self._vat_name.clear()
        self._vat_rate.setValue(0.0)
        self._vat_description.clear()

    # ------------------------------------------------------------------
    # Load helpers – Transaction Document Types
    # ------------------------------------------------------------------

    def _load_transaction_document_types(self) -> None:
        self._doc_types = self.service.list_transaction_document_types()
        self._doc_type_table.setRowCount(len(self._doc_types))
        for i, row in enumerate(self._doc_types):
            self._doc_type_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._doc_type_table.setItem(i, 1, QTableWidgetItem(str(row.no)))
            self._doc_type_table.setItem(i, 2, QTableWidgetItem(row.name))
            self._doc_type_table.setItem(i, 3, QTableWidgetItem(row.display_name))
            self._doc_type_table.setItem(i, 4, QTableWidgetItem(row.description))
        self._doc_type_table.resizeColumnsToContents()
        self._doc_type_table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Load helpers – Transaction Discount Types
    # ------------------------------------------------------------------

    def _load_transaction_discount_types(self) -> None:
        self._discount_types = self.service.list_transaction_discount_types()
        self._discount_type_table.setRowCount(len(self._discount_types))
        for i, row in enumerate(self._discount_types):
            self._discount_type_table.setItem(i, 0, QTableWidgetItem(row.id))
            self._discount_type_table.setItem(i, 1, QTableWidgetItem(row.code))
            self._discount_type_table.setItem(i, 2, QTableWidgetItem(row.name))
            self._discount_type_table.setItem(i, 3, QTableWidgetItem(row.display_name))
            self._discount_type_table.setItem(i, 4, QTableWidgetItem(row.description))
        self._discount_type_table.resizeColumnsToContents()
        self._discount_type_table.horizontalHeader().setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Selection handlers – Transaction Document Types
    # ------------------------------------------------------------------

    def _on_doc_type_selected(self) -> None:
        rows = self._doc_type_table.selectedItems()
        if not rows:
            return
        row_idx = self._doc_type_table.currentRow()
        self._selected_doc_type_id = self._doc_type_table.item(row_idx, 0).text()
        record = next((d for d in self._doc_types if d.id == self._selected_doc_type_id), None)
        if record is None:
            return
        self._doc_type_no.setValue(record.no)
        self._doc_type_name.setText(record.name)
        self._doc_type_display_name.setText(record.display_name)
        self._doc_type_description.setText(record.description)

    # ------------------------------------------------------------------
    # Selection handlers – Transaction Discount Types
    # ------------------------------------------------------------------

    def _on_discount_type_selected(self) -> None:
        rows = self._discount_type_table.selectedItems()
        if not rows:
            return
        row_idx = self._discount_type_table.currentRow()
        self._selected_discount_type_id = self._discount_type_table.item(row_idx, 0).text()
        record = next((d for d in self._discount_types if d.id == self._selected_discount_type_id), None)
        if record is None:
            return
        self._discount_type_code.setText(record.code)
        self._discount_type_name.setText(record.name)
        self._discount_type_display_name.setText(record.display_name)
        self._discount_type_description.setText(record.description)

    # ------------------------------------------------------------------
    # CRUD – Transaction Document Types
    # ------------------------------------------------------------------

    def _on_doc_type_add(self) -> None:
        data = self._collect_doc_type_data()
        if not data:
            return
        result = self.service.add_transaction_document_type(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_transaction_document_types()
            self._doc_type_clear_form()

    def _on_doc_type_update(self) -> None:
        if not self._selected_doc_type_id:
            self._show_status(False, "Select a document type row first.")
            return
        data = self._collect_doc_type_data()
        if not data:
            return
        result = self.service.update_transaction_document_type(self._selected_doc_type_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_transaction_document_types()

    def _on_doc_type_delete(self) -> None:
        if not self._selected_doc_type_id:
            self._show_status(False, "Select a document type row first.")
            return
        if not self._confirm("Delete this transaction document type?"):
            return
        result = self.service.delete_transaction_document_type(self._selected_doc_type_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_doc_type_id = None
            self._load_transaction_document_types()
            self._doc_type_clear_form()

    def _collect_doc_type_data(self) -> dict | None:
        name = self._doc_type_name.text().strip()
        if not name:
            self._show_status(False, "Name is required.")
            return None
        return {
            "no": self._doc_type_no.value(),
            "name": name,
            "display_name": self._doc_type_display_name.text().strip() or None,
            "description": self._doc_type_description.text().strip() or None,
        }

    def _doc_type_clear_form(self) -> None:
        self._selected_doc_type_id = None
        self._doc_type_no.setValue(0)
        self._doc_type_name.clear()
        self._doc_type_display_name.clear()
        self._doc_type_description.clear()

    # ------------------------------------------------------------------
    # CRUD – Transaction Discount Types
    # ------------------------------------------------------------------

    def _on_discount_type_add(self) -> None:
        data = self._collect_discount_type_data()
        if not data:
            return
        result = self.service.add_transaction_discount_type(data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_transaction_discount_types()
            self._discount_type_clear_form()

    def _on_discount_type_update(self) -> None:
        if not self._selected_discount_type_id:
            self._show_status(False, "Select a discount type row first.")
            return
        data = self._collect_discount_type_data()
        if not data:
            return
        result = self.service.update_transaction_discount_type(self._selected_discount_type_id, data)
        self._show_status(result.success, result.message)
        if result.success:
            self._load_transaction_discount_types()

    def _on_discount_type_delete(self) -> None:
        if not self._selected_discount_type_id:
            self._show_status(False, "Select a discount type row first.")
            return
        if not self._confirm("Delete this transaction discount type?"):
            return
        result = self.service.delete_transaction_discount_type(self._selected_discount_type_id)
        self._show_status(result.success, result.message)
        if result.success:
            self._selected_discount_type_id = None
            self._load_transaction_discount_types()
            self._discount_type_clear_form()

    def _collect_discount_type_data(self) -> dict | None:
        code = self._discount_type_code.text().strip()
        name = self._discount_type_name.text().strip()
        if not code or not name:
            self._show_status(False, "Code and Name are required.")
            return None
        return {
            "code": code,
            "name": name,
            "display_name": self._discount_type_display_name.text().strip() or None,
            "description": self._discount_type_description.text().strip() or None,
        }

    def _discount_type_clear_form(self) -> None:
        self._selected_discount_type_id = None
        self._discount_type_code.clear()
        self._discount_type_name.clear()
        self._discount_type_display_name.clear()
        self._discount_type_description.clear()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _set_combo_by_id(self, combo: QComboBox, target_id: str) -> None:
        idx = combo.findData(target_id)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _confirm(self, message: str) -> bool:
        answer = QMessageBox.question(
            self,
            "Confirm",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def _show_status(self, success: bool, message: str) -> None:
        color = "#166534" if success else "#991b1b"
        self._status_label.setStyleSheet(f"color: {color};")
        self._status_label.setText(message)
