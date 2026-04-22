"""
Product management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from decimal import Decimal

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
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.product_management_service import (
    ProductAttributeView,
    ProductBarcodeView,
    ProductManagementService,
    ProductManufacturerView,
    ProductUnitView,
    ProductVariantView,
    ProductView,
)
from settings.settings import Settings


class ProductManagementForm(QWidget):
    """Manage product master data and product-related listing workflows."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = ProductManagementService(store_code=bootstrap_context.store_id)
        self.setWindowTitle(f"{Settings().app_name} - Product Management")
        self.setMinimumSize(1360, 920)

        self._products: list[ProductView] = []
        self._manufacturers: list[ProductManufacturerView] = []
        self._units: list[ProductUnitView] = []
        self._attributes: list[ProductAttributeView] = []
        self._variants: list[ProductVariantView] = []
        self._barcodes: list[ProductBarcodeView] = []
        self._cashier_rows: list[tuple[str, int, str, str, bool]] = []

        self._selected_product_id: str | None = None
        self._selected_manufacturer_id: str | None = None
        self._selected_unit_id: str | None = None
        self._selected_attribute_id: str | None = None
        self._selected_variant_id: str | None = None
        self._selected_barcode_id: str | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Product Operations Center")
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
        self._tabs.addTab(self._build_products_tab(), "Products")
        self._tabs.addTab(self._build_catalog_tab(), "Product Catalog")
        self._tabs.addTab(self._build_manufacturer_tab(), "Manufacturers")
        self._tabs.addTab(self._build_units_tab(), "Product Units")
        self._tabs.addTab(self._build_attributes_tab(), "Product Attributes")
        self._tabs.addTab(self._build_variants_tab(), "Product Variants")
        self._tabs.addTab(self._build_barcodes_tab(), "Product Barcodes")
        self._tabs.addTab(self._build_cashier_reference_tab(), "Cashier Reference")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_layout)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_products_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        product_filter_layout = QHBoxLayout()
        self._product_search_input = QLineEdit()
        self._product_search_input.setPlaceholderText("Search by product code, name, or short name")
        self._product_search_input.returnPressed.connect(self.refresh_products)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_products)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_products)
        product_filter_layout.addWidget(self._product_search_input)
        product_filter_layout.addWidget(search_button)
        product_filter_layout.addWidget(refresh_button)
        left_layout.addLayout(product_filter_layout)

        self._product_table = QTableWidget(0, 10)
        self._product_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Name",
                "Manufacturer",
                "Unit",
                "Sale Price",
                "Stock",
                "Department",
                "Sub Department",
                "Barcodes",
                "Variants",
            ]
        )
        self._product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._product_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._product_table.verticalHeader().setVisible(False)
        self._product_table.setAlternatingRowColors(True)
        self._product_table.itemSelectionChanged.connect(self._on_product_row_selected)
        left_layout.addWidget(self._product_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Product Editor")
        editor_grid = QGridLayout()

        self._product_code_input = QLineEdit()
        self._product_name_input = QLineEdit()
        self._product_short_name_input = QLineEdit()
        self._product_old_code_input = QLineEdit()
        self._product_shelf_code_input = QLineEdit()
        self._product_description_input = QPlainTextEdit()
        self._product_description_input.setMinimumHeight(110)
        self._product_sale_price_input = QDoubleSpinBox()
        self._product_sale_price_input.setMaximum(10_000_000_000)
        self._product_sale_price_input.setDecimals(4)
        self._product_purchase_price_input = QDoubleSpinBox()
        self._product_purchase_price_input.setMaximum(10_000_000_000)
        self._product_purchase_price_input.setDecimals(4)
        self._product_stock_input = QSpinBox()
        self._product_stock_input.setRange(0, 10_000_000)
        self._product_min_stock_input = QSpinBox()
        self._product_min_stock_input.setRange(0, 10_000_000)
        self._product_max_stock_input = QSpinBox()
        self._product_max_stock_input.setRange(0, 10_000_000)
        self._product_stock_unit_input = QLineEdit()
        self._product_stock_unit_no_input = QSpinBox()
        self._product_stock_unit_no_input.setRange(1, 100_000)
        self._product_discount_percent_input = QSpinBox()
        self._product_discount_percent_input.setRange(0, 100)
        self._product_vat_no_input = QSpinBox()
        self._product_vat_no_input.setRange(0, 50)
        self._product_manufacturer_combo = QComboBox()
        self._product_unit_combo = QComboBox()
        self._product_vat_combo = QComboBox()
        self._product_department_combo = QComboBox()
        self._product_department_combo.currentIndexChanged.connect(
            self._reload_sub_department_combos
        )
        self._product_sub_department_combo = QComboBox()
        self._product_warehouse_combo = QComboBox()
        self._product_scalable_checkbox = QCheckBox("Scalable Product")
        self._product_allow_discount_checkbox = QCheckBox("Discount Allowed")
        self._product_allow_discount_checkbox.setChecked(True)
        self._product_allow_negative_stock_checkbox = QCheckBox("Allow Negative Stock")
        self._product_allow_return_checkbox = QCheckBox("Return Allowed")
        self._product_allow_return_checkbox.setChecked(True)

        editor_grid.addWidget(QLabel("Product Code"), 0, 0)
        editor_grid.addWidget(self._product_code_input, 0, 1)
        editor_grid.addWidget(QLabel("Product Name"), 1, 0)
        editor_grid.addWidget(self._product_name_input, 1, 1)
        editor_grid.addWidget(QLabel("Short Name"), 2, 0)
        editor_grid.addWidget(self._product_short_name_input, 2, 1)
        editor_grid.addWidget(QLabel("Old Code"), 3, 0)
        editor_grid.addWidget(self._product_old_code_input, 3, 1)
        editor_grid.addWidget(QLabel("Shelf Code"), 4, 0)
        editor_grid.addWidget(self._product_shelf_code_input, 4, 1)
        editor_grid.addWidget(QLabel("Sale Price"), 5, 0)
        editor_grid.addWidget(self._product_sale_price_input, 5, 1)
        editor_grid.addWidget(QLabel("Purchase Price"), 6, 0)
        editor_grid.addWidget(self._product_purchase_price_input, 6, 1)
        editor_grid.addWidget(QLabel("Stock"), 7, 0)
        editor_grid.addWidget(self._product_stock_input, 7, 1)
        editor_grid.addWidget(QLabel("Min Stock"), 8, 0)
        editor_grid.addWidget(self._product_min_stock_input, 8, 1)
        editor_grid.addWidget(QLabel("Max Stock"), 9, 0)
        editor_grid.addWidget(self._product_max_stock_input, 9, 1)
        editor_grid.addWidget(QLabel("Stock Unit"), 10, 0)
        editor_grid.addWidget(self._product_stock_unit_input, 10, 1)
        editor_grid.addWidget(QLabel("Stock Unit No"), 11, 0)
        editor_grid.addWidget(self._product_stock_unit_no_input, 11, 1)
        editor_grid.addWidget(QLabel("Discount %"), 12, 0)
        editor_grid.addWidget(self._product_discount_percent_input, 12, 1)
        editor_grid.addWidget(QLabel("VAT Number"), 13, 0)
        editor_grid.addWidget(self._product_vat_no_input, 13, 1)
        editor_grid.addWidget(QLabel("Manufacturer"), 14, 0)
        editor_grid.addWidget(self._product_manufacturer_combo, 14, 1)
        editor_grid.addWidget(QLabel("Unit"), 15, 0)
        editor_grid.addWidget(self._product_unit_combo, 15, 1)
        editor_grid.addWidget(QLabel("VAT"), 16, 0)
        editor_grid.addWidget(self._product_vat_combo, 16, 1)
        editor_grid.addWidget(QLabel("Department"), 17, 0)
        editor_grid.addWidget(self._product_department_combo, 17, 1)
        editor_grid.addWidget(QLabel("Sub Department"), 18, 0)
        editor_grid.addWidget(self._product_sub_department_combo, 18, 1)
        editor_grid.addWidget(QLabel("Primary Warehouse"), 19, 0)
        editor_grid.addWidget(self._product_warehouse_combo, 19, 1)
        editor_grid.addWidget(self._product_scalable_checkbox, 20, 1)
        editor_grid.addWidget(self._product_allow_discount_checkbox, 21, 1)
        editor_grid.addWidget(self._product_allow_negative_stock_checkbox, 22, 1)
        editor_grid.addWidget(self._product_allow_return_checkbox, 23, 1)
        editor_grid.addWidget(QLabel("Description"), 24, 0)
        editor_grid.addWidget(self._product_description_input, 24, 1)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_product_editor)
        save_button.clicked.connect(self._save_product)
        delete_button.clicked.connect(self._delete_product)
        refresh_editor_button.clicked.connect(self.refresh_products)
        action_layout.addWidget(new_button)
        action_layout.addWidget(save_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(refresh_editor_button)

        editor_content = QWidget()
        editor_content_layout = QVBoxLayout()
        editor_content_layout.setContentsMargins(0, 0, 0, 0)
        editor_content_layout.addLayout(editor_grid)
        editor_content_layout.addStretch(1)
        editor_content_layout.addLayout(action_layout)
        editor_content.setLayout(editor_content_layout)

        editor_scroll = QScrollArea()
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        editor_scroll.setWidget(editor_content)

        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(6, 6, 6, 6)
        editor_layout.addWidget(editor_scroll)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([900, 420])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_catalog_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self._catalog_search_input = QLineEdit()
        self._catalog_search_input.setPlaceholderText("Search products for catalog list")
        self._catalog_search_input.returnPressed.connect(self.refresh_catalog_table)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_catalog_table)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_catalog_table)
        filter_layout.addWidget(self._catalog_search_input)
        filter_layout.addWidget(search_button)
        filter_layout.addWidget(refresh_button)
        layout.addLayout(filter_layout)

        self._catalog_table = QTableWidget(0, 11)
        self._catalog_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Name",
                "Short Name",
                "Manufacturer",
                "Unit",
                "VAT",
                "Sale Price",
                "Purchase Price",
                "Stock",
                "Attributes",
                "Barcodes",
            ]
        )
        self._catalog_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._catalog_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._catalog_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._catalog_table.verticalHeader().setVisible(False)
        self._catalog_table.setAlternatingRowColors(True)
        layout.addWidget(self._catalog_table)

        tab.setLayout(layout)
        return tab

    def _build_manufacturer_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._manufacturer_table = QTableWidget(0, 2)
        self._manufacturer_table.setHorizontalHeaderLabels(["Name", "Description"])
        self._manufacturer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._manufacturer_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._manufacturer_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._manufacturer_table.verticalHeader().setVisible(False)
        self._manufacturer_table.setAlternatingRowColors(True)
        self._manufacturer_table.itemSelectionChanged.connect(self._on_manufacturer_row_selected)

        table_wrap = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._manufacturer_table)
        table_wrap.setLayout(table_layout)

        editor_box = QGroupBox("Manufacturer Editor")
        form_layout = QFormLayout()
        self._manufacturer_name_input = QLineEdit()
        self._manufacturer_description_input = QLineEdit()
        form_layout.addRow("Name", self._manufacturer_name_input)
        form_layout.addRow("Description", self._manufacturer_description_input)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_manufacturer_editor)
        save_button.clicked.connect(self._save_manufacturer)
        delete_button.clicked.connect(self._delete_manufacturer)
        refresh_button.clicked.connect(self.refresh_manufacturers)
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
        splitter.setSizes([900, 360])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_units_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        self._unit_table = QTableWidget(0, 5)
        self._unit_table.setHorizontalHeaderLabels(["Code", "Name", "Symbol", "Base Amount", "Description"])
        self._unit_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._unit_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._unit_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._unit_table.verticalHeader().setVisible(False)
        self._unit_table.setAlternatingRowColors(True)
        self._unit_table.itemSelectionChanged.connect(self._on_unit_row_selected)

        table_wrap = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self._unit_table)
        table_wrap.setLayout(table_layout)

        editor_box = QGroupBox("Product Unit Editor")
        form_layout = QFormLayout()
        self._unit_code_input = QLineEdit()
        self._unit_name_input = QLineEdit()
        self._unit_symbol_input = QLineEdit()
        self._unit_base_amount_input = QDoubleSpinBox()
        self._unit_base_amount_input.setDecimals(4)
        self._unit_base_amount_input.setMaximum(100_000)
        self._unit_description_input = QLineEdit()
        form_layout.addRow("Code", self._unit_code_input)
        form_layout.addRow("Name", self._unit_name_input)
        form_layout.addRow("Symbol", self._unit_symbol_input)
        form_layout.addRow("Base Amount", self._unit_base_amount_input)
        form_layout.addRow("Description", self._unit_description_input)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_unit_editor)
        save_button.clicked.connect(self._save_unit)
        delete_button.clicked.connect(self._delete_unit)
        refresh_button.clicked.connect(self.refresh_units)
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
        splitter.setSizes([900, 360])

        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_attributes_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._attribute_product_filter_combo = QComboBox()
        self._attribute_product_filter_combo.currentIndexChanged.connect(self.refresh_attributes)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_attributes)
        filter_layout.addWidget(QLabel("Product"))
        filter_layout.addWidget(self._attribute_product_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._attribute_table = QTableWidget(0, 8)
        self._attribute_table.setHorizontalHeaderLabels(
            [
                "Product",
                "Attribute",
                "Value",
                "Type",
                "Category",
                "Unit",
                "Searchable",
                "Filterable",
            ]
        )
        self._attribute_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._attribute_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._attribute_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._attribute_table.verticalHeader().setVisible(False)
        self._attribute_table.setAlternatingRowColors(True)
        self._attribute_table.itemSelectionChanged.connect(self._on_attribute_row_selected)
        left_layout.addWidget(self._attribute_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Product Attribute Editor")
        form_layout = QFormLayout()
        self._attribute_product_combo = QComboBox()
        self._attribute_name_input = QLineEdit()
        self._attribute_value_input = QLineEdit()
        self._attribute_type_combo = QComboBox()
        self._attribute_type_combo.addItems(["text", "number", "boolean", "date"])
        self._attribute_category_input = QLineEdit()
        self._attribute_unit_input = QLineEdit()
        self._attribute_searchable_checkbox = QCheckBox("Searchable")
        self._attribute_searchable_checkbox.setChecked(True)
        self._attribute_filterable_checkbox = QCheckBox("Filterable")
        self._attribute_filterable_checkbox.setChecked(True)
        self._attribute_visible_checkbox = QCheckBox("Visible on Product")
        self._attribute_visible_checkbox.setChecked(True)
        form_layout.addRow("Product", self._attribute_product_combo)
        form_layout.addRow("Attribute Name", self._attribute_name_input)
        form_layout.addRow("Attribute Value", self._attribute_value_input)
        form_layout.addRow("Attribute Type", self._attribute_type_combo)
        form_layout.addRow("Category", self._attribute_category_input)
        form_layout.addRow("Unit", self._attribute_unit_input)
        form_layout.addRow(self._attribute_searchable_checkbox)
        form_layout.addRow(self._attribute_filterable_checkbox)
        form_layout.addRow(self._attribute_visible_checkbox)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_attribute_editor)
        save_button.clicked.connect(self._save_attribute)
        delete_button.clicked.connect(self._delete_attribute)
        refresh_editor_button.clicked.connect(self.refresh_attributes)
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
        splitter.setSizes([900, 360])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_variants_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._variant_product_filter_combo = QComboBox()
        self._variant_product_filter_combo.currentIndexChanged.connect(self.refresh_variants)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_variants)
        filter_layout.addWidget(QLabel("Product"))
        filter_layout.addWidget(self._variant_product_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._variant_table = QTableWidget(0, 8)
        self._variant_table.setHorizontalHeaderLabels(
            ["Product", "Variant Name", "Variant Code", "Color", "Size", "Sort", "Active", "Default"]
        )
        self._variant_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._variant_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._variant_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._variant_table.verticalHeader().setVisible(False)
        self._variant_table.setAlternatingRowColors(True)
        self._variant_table.itemSelectionChanged.connect(self._on_variant_row_selected)
        left_layout.addWidget(self._variant_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Product Variant Editor")
        form_layout = QFormLayout()
        self._variant_product_combo = QComboBox()
        self._variant_name_input = QLineEdit()
        self._variant_code_input = QLineEdit()
        self._variant_color_input = QLineEdit()
        self._variant_size_input = QLineEdit()
        self._variant_sort_order_input = QSpinBox()
        self._variant_sort_order_input.setRange(0, 100_000)
        self._variant_active_checkbox = QCheckBox("Active")
        self._variant_active_checkbox.setChecked(True)
        self._variant_default_checkbox = QCheckBox("Default Variant")
        form_layout.addRow("Product", self._variant_product_combo)
        form_layout.addRow("Variant Name", self._variant_name_input)
        form_layout.addRow("Variant Code", self._variant_code_input)
        form_layout.addRow("Color", self._variant_color_input)
        form_layout.addRow("Size", self._variant_size_input)
        form_layout.addRow("Sort Order", self._variant_sort_order_input)
        form_layout.addRow(self._variant_active_checkbox)
        form_layout.addRow(self._variant_default_checkbox)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_variant_editor)
        save_button.clicked.connect(self._save_variant)
        delete_button.clicked.connect(self._delete_variant)
        refresh_editor_button.clicked.connect(self.refresh_variants)
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
        splitter.setSizes([900, 360])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_barcodes_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._barcode_product_filter_combo = QComboBox()
        self._barcode_product_filter_combo.currentIndexChanged.connect(self.refresh_barcodes)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_barcodes)
        filter_layout.addWidget(QLabel("Product"))
        filter_layout.addWidget(self._barcode_product_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._barcode_table = QTableWidget(0, 6)
        self._barcode_table.setHorizontalHeaderLabels(
            ["Product", "Barcode", "Old Barcode", "Purchase Price", "Sale Price", "Barcode Mask"]
        )
        self._barcode_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._barcode_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._barcode_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._barcode_table.verticalHeader().setVisible(False)
        self._barcode_table.setAlternatingRowColors(True)
        self._barcode_table.itemSelectionChanged.connect(self._on_barcode_row_selected)
        left_layout.addWidget(self._barcode_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Product Barcode Editor")
        form_layout = QFormLayout()
        self._barcode_product_combo = QComboBox()
        self._barcode_value_input = QLineEdit()
        self._barcode_old_value_input = QLineEdit()
        self._barcode_purchase_price_input = QDoubleSpinBox()
        self._barcode_purchase_price_input.setMaximum(10_000_000_000)
        self._barcode_purchase_price_input.setDecimals(4)
        self._barcode_sale_price_input = QDoubleSpinBox()
        self._barcode_sale_price_input.setMaximum(10_000_000_000)
        self._barcode_sale_price_input.setDecimals(4)
        self._barcode_mask_combo = QComboBox()
        form_layout.addRow("Product", self._barcode_product_combo)
        form_layout.addRow("Barcode", self._barcode_value_input)
        form_layout.addRow("Old Barcode", self._barcode_old_value_input)
        form_layout.addRow("Purchase Price", self._barcode_purchase_price_input)
        form_layout.addRow("Sale Price", self._barcode_sale_price_input)
        form_layout.addRow("Barcode Mask", self._barcode_mask_combo)

        action_layout = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_editor_button = QPushButton("Refresh")
        new_button.clicked.connect(self._clear_barcode_editor)
        save_button.clicked.connect(self._save_barcode)
        delete_button.clicked.connect(self._delete_barcode)
        refresh_editor_button.clicked.connect(self.refresh_barcodes)
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
        splitter.setSizes([900, 360])
        root = QVBoxLayout()
        root.addWidget(splitter)
        tab.setLayout(root)
        return tab

    def _build_cashier_reference_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        self._cashier_reference_table = QTableWidget(0, 4)
        self._cashier_reference_table.setHorizontalHeaderLabels(["No", "Username", "Name", "Active"])
        self._cashier_reference_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._cashier_reference_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._cashier_reference_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._cashier_reference_table.verticalHeader().setVisible(False)
        self._cashier_reference_table.setAlternatingRowColors(True)
        layout.addWidget(self._cashier_reference_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self.refresh_manufacturers()
        self.refresh_units()
        self.refresh_products()
        self.refresh_catalog_table()
        self.refresh_attributes()
        self.refresh_variants()
        self.refresh_barcodes()
        self.refresh_cashier_reference()

    def refresh_products(self) -> None:
        self._reload_product_related_combos()
        search_value = self._product_search_input.text().strip()
        self._products = self.service.list_products(search_text=search_value)
        self._product_table.setRowCount(len(self._products))
        for row_index, product in enumerate(self._products):
            values = [
                product.code,
                product.name,
                product.manufacturer_name,
                product.unit_name,
                self._format_amount(product.sale_price),
                str(product.stock),
                product.department_name,
                product.sub_department_name,
                str(product.barcode_count),
                str(product.variant_count),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, product.id)
                self._product_table.setItem(row_index, col, item)
        self._product_table.resizeColumnsToContents()
        self._reload_product_lookup_combos()

    def refresh_catalog_table(self) -> None:
        search_value = self._catalog_search_input.text().strip()
        rows = self.service.list_products(search_text=search_value)
        self._catalog_table.setRowCount(len(rows))
        for row_index, product in enumerate(rows):
            values = [
                product.code,
                product.name,
                product.short_name,
                product.manufacturer_name,
                product.unit_name,
                product.vat_name,
                self._format_amount(product.sale_price),
                self._format_amount(product.purchase_price),
                str(product.stock),
                str(product.attribute_count),
                str(product.barcode_count),
            ]
            for col, value in enumerate(values):
                self._catalog_table.setItem(row_index, col, QTableWidgetItem(value))
        self._catalog_table.resizeColumnsToContents()

    def refresh_manufacturers(self) -> None:
        self._manufacturers = self.service.list_manufacturers()
        self._manufacturer_table.setRowCount(len(self._manufacturers))
        for row_index, manufacturer in enumerate(self._manufacturers):
            values = [manufacturer.name, manufacturer.description]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, manufacturer.id)
                self._manufacturer_table.setItem(row_index, col, item)
        self._manufacturer_table.resizeColumnsToContents()

    def refresh_units(self) -> None:
        self._units = self.service.list_product_units()
        self._unit_table.setRowCount(len(self._units))
        for row_index, unit in enumerate(self._units):
            values = [
                unit.code,
                unit.name,
                unit.symbol,
                f"{unit.base_amount:.4f}" if unit.base_amount is not None else "",
                unit.description,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, unit.id)
                self._unit_table.setItem(row_index, col, item)
        self._unit_table.resizeColumnsToContents()

    def refresh_attributes(self) -> None:
        selected_product_id = self._attribute_product_filter_combo.currentData()
        self._attributes = self.service.list_product_attributes(product_id=selected_product_id)
        self._attribute_table.setRowCount(len(self._attributes))
        for row_index, attribute in enumerate(self._attributes):
            values = [
                attribute.product_name,
                attribute.attribute_name,
                attribute.attribute_value,
                attribute.attribute_type,
                attribute.category,
                attribute.unit,
                "Yes" if attribute.is_searchable else "No",
                "Yes" if attribute.is_filterable else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, attribute.id)
                self._attribute_table.setItem(row_index, col, item)
        self._attribute_table.resizeColumnsToContents()

    def refresh_variants(self) -> None:
        selected_product_id = self._variant_product_filter_combo.currentData()
        self._variants = self.service.list_product_variants(product_id=selected_product_id)
        self._variant_table.setRowCount(len(self._variants))
        for row_index, variant in enumerate(self._variants):
            values = [
                variant.product_name,
                variant.variant_name,
                variant.variant_code,
                variant.color,
                variant.size,
                str(variant.sort_order),
                "Yes" if variant.is_active else "No",
                "Yes" if variant.is_default else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, variant.id)
                self._variant_table.setItem(row_index, col, item)
        self._variant_table.resizeColumnsToContents()

    def refresh_barcodes(self) -> None:
        selected_product_id = self._barcode_product_filter_combo.currentData()
        self._barcodes = self.service.list_product_barcodes(product_id=selected_product_id)
        self._barcode_table.setRowCount(len(self._barcodes))
        for row_index, barcode in enumerate(self._barcodes):
            values = [
                barcode.product_name,
                barcode.barcode,
                barcode.old_barcode,
                self._format_amount(barcode.purchase_price),
                self._format_amount(barcode.sale_price),
                barcode.mask_label,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, barcode.id)
                self._barcode_table.setItem(row_index, col, item)
        self._barcode_table.resizeColumnsToContents()

    def refresh_cashier_reference(self) -> None:
        rows = self.service.list_cashier_summaries()
        self._cashier_rows = [
            (row.id, row.no, row.user_name, row.full_name, row.is_active)
            for row in rows
        ]
        self._cashier_reference_table.setRowCount(len(self._cashier_rows))
        for row_index, row in enumerate(self._cashier_rows):
            _row_id, no, user_name, full_name, is_active = row
            values = [str(no), user_name, full_name, "Yes" if is_active else "No"]
            for col, value in enumerate(values):
                self._cashier_reference_table.setItem(row_index, col, QTableWidgetItem(value))
        self._cashier_reference_table.resizeColumnsToContents()

    def _reload_product_related_combos(self) -> None:
        self._reload_combo_with_optional_all(
            self._product_manufacturer_combo,
            [(item.id, item.label) for item in self.service.list_manufacturer_lookups()],
            include_empty=True,
            empty_label="None",
        )
        self._reload_combo_with_optional_all(
            self._product_unit_combo,
            [(item.id, item.label) for item in self.service.list_product_unit_lookups()],
            include_empty=True,
            empty_label="None",
        )
        self._reload_combo_with_optional_all(
            self._product_vat_combo,
            [(item.id, item.label) for item in self.service.list_vat_lookups()],
            include_empty=True,
            empty_label="None",
        )
        self._reload_combo_with_optional_all(
            self._product_department_combo,
            [(item.id, item.label) for item in self.service.list_department_main_group_lookups()],
            include_empty=False,
            empty_label="",
        )
        self._reload_sub_department_combos()
        self._reload_combo_with_optional_all(
            self._product_warehouse_combo,
            [(item.id, item.label) for item in self.service.list_warehouse_lookups()],
            include_empty=True,
            empty_label="None",
        )

    def _reload_sub_department_combos(self) -> None:
        main_group_id = self._product_department_combo.currentData()
        sub_groups = [
            (item.id, item.label)
            for item in self.service.list_department_sub_group_lookups(main_group_id=main_group_id)
        ]
        self._reload_combo_with_optional_all(
            self._product_sub_department_combo,
            sub_groups,
            include_empty=False,
            empty_label="",
        )

    def _reload_product_lookup_combos(self) -> None:
        items = [(item.id, item.label) for item in self.service.list_product_lookups()]
        self._reload_combo_with_optional_all(
            self._attribute_product_combo,
            items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo_with_optional_all(
            self._attribute_product_filter_combo,
            items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo_with_optional_all(
            self._variant_product_combo,
            items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo_with_optional_all(
            self._variant_product_filter_combo,
            items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo_with_optional_all(
            self._barcode_product_combo,
            items,
            include_empty=False,
            empty_label="",
        )
        self._reload_combo_with_optional_all(
            self._barcode_product_filter_combo,
            items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo_with_optional_all(
            self._barcode_mask_combo,
            [(item.id, item.label) for item in self.service.list_barcode_mask_lookups()],
            include_empty=True,
            empty_label="None",
        )

    def _on_product_row_selected(self) -> None:
        selected_items = self._product_table.selectedItems()
        if not selected_items:
            return
        product_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._products if x.id == product_id), None)
        if selected is None:
            return
        self._selected_product_id = selected.id
        self._product_code_input.setText(selected.code)
        self._product_name_input.setText(selected.name)
        self._product_short_name_input.setText(selected.short_name)
        self._product_old_code_input.setText(selected.old_code)
        self._product_shelf_code_input.setText(selected.shelf_code)
        self._product_description_input.setPlainText(selected.description)
        self._product_sale_price_input.setValue(float(selected.sale_price))
        self._product_purchase_price_input.setValue(float(selected.purchase_price))
        self._product_stock_input.setValue(selected.stock)
        self._product_min_stock_input.setValue(selected.min_stock)
        self._product_max_stock_input.setValue(selected.max_stock)
        self._product_stock_unit_input.setText(selected.stock_unit)
        self._product_stock_unit_no_input.setValue(selected.stock_unit_no)
        self._product_discount_percent_input.setValue(selected.discount_percent)
        self._product_vat_no_input.setValue(selected.vat_no)
        self._product_manufacturer_combo.setCurrentIndex(
            self._product_manufacturer_combo.findData(selected.fk_manufacturer_id)
        )
        self._product_unit_combo.setCurrentIndex(
            self._product_unit_combo.findData(selected.fk_product_unit_id)
        )
        self._product_vat_combo.setCurrentIndex(self._product_vat_combo.findData(selected.fk_vat_id))
        self._product_department_combo.setCurrentIndex(
            self._product_department_combo.findData(selected.fk_department_main_group_id)
        )
        self._reload_sub_department_combos()
        self._product_sub_department_combo.setCurrentIndex(
            self._product_sub_department_combo.findData(selected.fk_department_sub_group_id)
        )
        self._product_warehouse_combo.setCurrentIndex(
            self._product_warehouse_combo.findData(selected.fk_primary_warehouse_id)
        )
        self._product_scalable_checkbox.setChecked(selected.is_scalable)
        self._product_allow_discount_checkbox.setChecked(selected.is_allowed_discount)
        self._product_allow_negative_stock_checkbox.setChecked(selected.is_allowed_negative_stock)
        self._product_allow_return_checkbox.setChecked(selected.is_allowed_return)

    def _on_manufacturer_row_selected(self) -> None:
        selected_items = self._manufacturer_table.selectedItems()
        if not selected_items:
            return
        row_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._manufacturers if x.id == row_id), None)
        if selected is None:
            return
        self._selected_manufacturer_id = selected.id
        self._manufacturer_name_input.setText(selected.name)
        self._manufacturer_description_input.setText(selected.description)

    def _on_unit_row_selected(self) -> None:
        selected_items = self._unit_table.selectedItems()
        if not selected_items:
            return
        row_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._units if x.id == row_id), None)
        if selected is None:
            return
        self._selected_unit_id = selected.id
        self._unit_code_input.setText(selected.code)
        self._unit_name_input.setText(selected.name)
        self._unit_symbol_input.setText(selected.symbol)
        self._unit_base_amount_input.setValue(float(selected.base_amount or 0))
        self._unit_description_input.setText(selected.description)

    def _on_attribute_row_selected(self) -> None:
        selected_items = self._attribute_table.selectedItems()
        if not selected_items:
            return
        row_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._attributes if x.id == row_id), None)
        if selected is None:
            return
        self._selected_attribute_id = selected.id
        self._attribute_product_combo.setCurrentIndex(
            self._attribute_product_combo.findData(selected.product_id)
        )
        self._attribute_name_input.setText(selected.attribute_name)
        self._attribute_value_input.setText(selected.attribute_value)
        self._attribute_type_combo.setCurrentText(selected.attribute_type)
        self._attribute_category_input.setText(selected.category)
        self._attribute_unit_input.setText(selected.unit)
        self._attribute_searchable_checkbox.setChecked(selected.is_searchable)
        self._attribute_filterable_checkbox.setChecked(selected.is_filterable)
        self._attribute_visible_checkbox.setChecked(selected.is_visible_on_product)

    def _on_variant_row_selected(self) -> None:
        selected_items = self._variant_table.selectedItems()
        if not selected_items:
            return
        row_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._variants if x.id == row_id), None)
        if selected is None:
            return
        self._selected_variant_id = selected.id
        self._variant_product_combo.setCurrentIndex(self._variant_product_combo.findData(selected.product_id))
        self._variant_name_input.setText(selected.variant_name)
        self._variant_code_input.setText(selected.variant_code)
        self._variant_color_input.setText(selected.color)
        self._variant_size_input.setText(selected.size)
        self._variant_sort_order_input.setValue(selected.sort_order)
        self._variant_active_checkbox.setChecked(selected.is_active)
        self._variant_default_checkbox.setChecked(selected.is_default)

    def _on_barcode_row_selected(self) -> None:
        selected_items = self._barcode_table.selectedItems()
        if not selected_items:
            return
        row_id = selected_items[0].data(Qt.UserRole)
        selected = next((x for x in self._barcodes if x.id == row_id), None)
        if selected is None:
            return
        self._selected_barcode_id = selected.id
        self._barcode_product_combo.setCurrentIndex(self._barcode_product_combo.findData(selected.product_id))
        self._barcode_value_input.setText(selected.barcode)
        self._barcode_old_value_input.setText(selected.old_barcode)
        self._barcode_purchase_price_input.setValue(float(selected.purchase_price))
        self._barcode_sale_price_input.setValue(float(selected.sale_price))
        self._barcode_mask_combo.setCurrentIndex(
            self._barcode_mask_combo.findData(selected.fk_barcode_mask_id)
        )

    def _clear_product_editor(self) -> None:
        self._selected_product_id = None
        self._product_table.clearSelection()
        self._product_code_input.clear()
        self._product_name_input.clear()
        self._product_short_name_input.clear()
        self._product_old_code_input.clear()
        self._product_shelf_code_input.clear()
        self._product_description_input.clear()
        self._product_sale_price_input.setValue(0)
        self._product_purchase_price_input.setValue(0)
        self._product_stock_input.setValue(0)
        self._product_min_stock_input.setValue(0)
        self._product_max_stock_input.setValue(0)
        self._product_stock_unit_input.clear()
        self._product_stock_unit_no_input.setValue(1)
        self._product_discount_percent_input.setValue(0)
        self._product_vat_no_input.setValue(1)
        self._product_manufacturer_combo.setCurrentIndex(0)
        self._product_unit_combo.setCurrentIndex(0)
        self._product_vat_combo.setCurrentIndex(0)
        self._product_department_combo.setCurrentIndex(0)
        self._reload_sub_department_combos()
        self._product_sub_department_combo.setCurrentIndex(0)
        self._product_warehouse_combo.setCurrentIndex(0)
        self._product_scalable_checkbox.setChecked(False)
        self._product_allow_discount_checkbox.setChecked(True)
        self._product_allow_negative_stock_checkbox.setChecked(False)
        self._product_allow_return_checkbox.setChecked(True)

    def _clear_manufacturer_editor(self) -> None:
        self._selected_manufacturer_id = None
        self._manufacturer_table.clearSelection()
        self._manufacturer_name_input.clear()
        self._manufacturer_description_input.clear()

    def _clear_unit_editor(self) -> None:
        self._selected_unit_id = None
        self._unit_table.clearSelection()
        self._unit_code_input.clear()
        self._unit_name_input.clear()
        self._unit_symbol_input.clear()
        self._unit_base_amount_input.setValue(0)
        self._unit_description_input.clear()

    def _clear_attribute_editor(self) -> None:
        self._selected_attribute_id = None
        self._attribute_table.clearSelection()
        self._attribute_product_combo.setCurrentIndex(0)
        self._attribute_name_input.clear()
        self._attribute_value_input.clear()
        self._attribute_type_combo.setCurrentText("text")
        self._attribute_category_input.clear()
        self._attribute_unit_input.clear()
        self._attribute_searchable_checkbox.setChecked(True)
        self._attribute_filterable_checkbox.setChecked(True)
        self._attribute_visible_checkbox.setChecked(True)

    def _clear_variant_editor(self) -> None:
        self._selected_variant_id = None
        self._variant_table.clearSelection()
        self._variant_product_combo.setCurrentIndex(0)
        self._variant_name_input.clear()
        self._variant_code_input.clear()
        self._variant_color_input.clear()
        self._variant_size_input.clear()
        self._variant_sort_order_input.setValue(0)
        self._variant_active_checkbox.setChecked(True)
        self._variant_default_checkbox.setChecked(False)

    def _clear_barcode_editor(self) -> None:
        self._selected_barcode_id = None
        self._barcode_table.clearSelection()
        self._barcode_product_combo.setCurrentIndex(0)
        self._barcode_value_input.clear()
        self._barcode_old_value_input.clear()
        self._barcode_purchase_price_input.setValue(0)
        self._barcode_sale_price_input.setValue(0)
        self._barcode_mask_combo.setCurrentIndex(0)

    def _save_product(self) -> None:
        payload = {
            "name": self._product_name_input.text(),
            "short_name": self._product_short_name_input.text(),
            "code": self._product_code_input.text(),
            "old_code": self._product_old_code_input.text(),
            "shelf_code": self._product_shelf_code_input.text(),
            "description": self._product_description_input.toPlainText(),
            "sale_price": self._product_sale_price_input.value(),
            "purchase_price": self._product_purchase_price_input.value(),
            "stock": self._product_stock_input.value(),
            "min_stock": self._product_min_stock_input.value(),
            "max_stock": self._product_max_stock_input.value(),
            "stock_unit": self._product_stock_unit_input.text(),
            "stock_unit_no": self._product_stock_unit_no_input.value(),
            "vat_no": self._product_vat_no_input.value(),
            "discount_percent": self._product_discount_percent_input.value(),
            "fk_manufacturer_id": self._product_manufacturer_combo.currentData(),
            "fk_product_unit_id": self._product_unit_combo.currentData(),
            "fk_vat_id": self._product_vat_combo.currentData(),
            "fk_department_main_group_id": self._product_department_combo.currentData(),
            "fk_department_sub_group_id": self._product_sub_department_combo.currentData(),
            "fk_primary_warehouse_id": self._product_warehouse_combo.currentData(),
            "is_scalable": self._product_scalable_checkbox.isChecked(),
            "is_allowed_discount": self._product_allow_discount_checkbox.isChecked(),
            "is_allowed_negative_stock": self._product_allow_negative_stock_checkbox.isChecked(),
            "is_allowed_return": self._product_allow_return_checkbox.isChecked(),
        }
        result = self.service.save_product(payload=payload, product_id=self._selected_product_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_products()
            self.refresh_catalog_table()
            self._clear_product_editor()

    def _delete_product(self) -> None:
        if not self._selected_product_id:
            self._set_status(False, "Please select a product record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Product",
            "Selected product will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_product(self._selected_product_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_product_editor()

    def _save_manufacturer(self) -> None:
        payload = {
            "name": self._manufacturer_name_input.text(),
            "description": self._manufacturer_description_input.text(),
        }
        result = self.service.save_manufacturer(
            payload=payload,
            manufacturer_id=self._selected_manufacturer_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_manufacturers()
            self.refresh_products()
            self._clear_manufacturer_editor()

    def _delete_manufacturer(self) -> None:
        if not self._selected_manufacturer_id:
            self._set_status(False, "Please select a manufacturer record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Manufacturer",
            "Selected manufacturer will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_manufacturer(self._selected_manufacturer_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_manufacturers()
            self.refresh_products()
            self._clear_manufacturer_editor()

    def _save_unit(self) -> None:
        payload = {
            "code": self._unit_code_input.text(),
            "name": self._unit_name_input.text(),
            "symbol": self._unit_symbol_input.text(),
            "base_amount": self._unit_base_amount_input.value(),
            "description": self._unit_description_input.text(),
        }
        result = self.service.save_product_unit(payload=payload, unit_id=self._selected_unit_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_units()
            self.refresh_products()
            self._clear_unit_editor()

    def _delete_unit(self) -> None:
        if not self._selected_unit_id:
            self._set_status(False, "Please select a product unit record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Product Unit",
            "Selected product unit will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_product_unit(self._selected_unit_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_units()
            self.refresh_products()
            self._clear_unit_editor()

    def _save_attribute(self) -> None:
        payload = {
            "product_id": self._attribute_product_combo.currentData(),
            "attribute_name": self._attribute_name_input.text(),
            "attribute_value": self._attribute_value_input.text(),
            "attribute_type": self._attribute_type_combo.currentText(),
            "category": self._attribute_category_input.text(),
            "unit": self._attribute_unit_input.text(),
            "is_searchable": self._attribute_searchable_checkbox.isChecked(),
            "is_filterable": self._attribute_filterable_checkbox.isChecked(),
            "is_visible_on_product": self._attribute_visible_checkbox.isChecked(),
        }
        result = self.service.save_product_attribute(
            payload=payload,
            attribute_id=self._selected_attribute_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_attributes()
            self.refresh_catalog_table()
            self._clear_attribute_editor()

    def _delete_attribute(self) -> None:
        if not self._selected_attribute_id:
            self._set_status(False, "Please select a product attribute record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Product Attribute",
            "Selected product attribute will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_product_attribute(self._selected_attribute_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_attributes()
            self.refresh_catalog_table()
            self._clear_attribute_editor()

    def _save_variant(self) -> None:
        payload = {
            "product_id": self._variant_product_combo.currentData(),
            "variant_name": self._variant_name_input.text(),
            "variant_code": self._variant_code_input.text(),
            "color": self._variant_color_input.text(),
            "size": self._variant_size_input.text(),
            "sort_order": self._variant_sort_order_input.value(),
            "is_active": self._variant_active_checkbox.isChecked(),
            "is_default": self._variant_default_checkbox.isChecked(),
        }
        result = self.service.save_product_variant(payload=payload, variant_id=self._selected_variant_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_variants()
            self.refresh_products()
            self._clear_variant_editor()

    def _delete_variant(self) -> None:
        if not self._selected_variant_id:
            self._set_status(False, "Please select a product variant record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Product Variant",
            "Selected product variant will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_product_variant(self._selected_variant_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_variants()
            self.refresh_products()
            self._clear_variant_editor()

    def _save_barcode(self) -> None:
        payload = {
            "product_id": self._barcode_product_combo.currentData(),
            "barcode": self._barcode_value_input.text(),
            "old_barcode": self._barcode_old_value_input.text(),
            "purchase_price": self._barcode_purchase_price_input.value(),
            "sale_price": self._barcode_sale_price_input.value(),
            "fk_barcode_mask_id": self._barcode_mask_combo.currentData(),
        }
        result = self.service.save_product_barcode(payload=payload, barcode_id=self._selected_barcode_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_barcodes()
            self.refresh_products()
            self.refresh_catalog_table()
            self._clear_barcode_editor()

    def _delete_barcode(self) -> None:
        if not self._selected_barcode_id:
            self._set_status(False, "Please select a product barcode record to delete.")
            return
        answer = QMessageBox.question(
            self,
            "Delete Product Barcode",
            "Selected product barcode will be soft deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        result = self.service.delete_product_barcode(self._selected_barcode_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_barcodes()
            self.refresh_products()
            self.refresh_catalog_table()
            self._clear_barcode_editor()

    def _set_status(self, success: bool, message: str) -> None:
        self._status_label.setStyleSheet("color: #166534;" if success else "color: #b91c1c;")
        self._status_label.setText(message)

    @staticmethod
    def _reload_combo_with_optional_all(
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
