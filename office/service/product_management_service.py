"""
Service layer for product management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import asc, func
from sqlalchemy.exc import SQLAlchemyError

from data_layer.engine import Engine
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.department_main_group import DepartmentMainGroup
from data_layer.model.definition.department_sub_group import DepartmentSubGroup
from data_layer.model.definition.product import Product
from data_layer.model.definition.product_attribute import ProductAttribute
from data_layer.model.definition.product_barcode import ProductBarcode
from data_layer.model.definition.product_barcode_mask import ProductBarcodeMask
from data_layer.model.definition.product_manufacturer import ProductManufacturer
from data_layer.model.definition.product_unit import ProductUnit
from data_layer.model.definition.product_variant import ProductVariant
from data_layer.model.definition.store import Store
from data_layer.model.definition.vat import Vat
from data_layer.model.definition.warehouse import Warehouse


@dataclass(frozen=True)
class ServiceResult:
    success: bool
    message: str


@dataclass(frozen=True)
class LookupItem:
    id: str
    label: str


@dataclass(frozen=True)
class CashierSummaryView:
    id: str
    no: int
    user_name: str
    full_name: str
    is_active: bool


@dataclass(frozen=True)
class ProductView:
    id: str
    code: str
    name: str
    short_name: str
    sale_price: Decimal
    purchase_price: Decimal
    stock: int
    min_stock: int
    max_stock: int
    vat_no: int
    manufacturer_name: str
    unit_name: str
    vat_name: str
    department_name: str
    sub_department_name: str
    barcode_count: int
    variant_count: int
    attribute_count: int
    fk_vat_id: str | None
    fk_product_unit_id: str | None
    fk_department_main_group_id: str
    fk_department_sub_group_id: str
    fk_manufacturer_id: str | None
    fk_primary_warehouse_id: str | None
    old_code: str
    shelf_code: str
    description: str
    stock_unit: str
    stock_unit_no: int
    is_scalable: bool
    is_allowed_discount: bool
    discount_percent: int
    is_allowed_negative_stock: bool
    is_allowed_return: bool


@dataclass(frozen=True)
class ProductManufacturerView:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class ProductUnitView:
    id: str
    code: str
    name: str
    symbol: str
    base_amount: float | None
    description: str


@dataclass(frozen=True)
class ProductAttributeView:
    id: str
    product_id: str
    product_name: str
    attribute_name: str
    attribute_value: str
    attribute_type: str
    category: str
    unit: str
    is_searchable: bool
    is_filterable: bool
    is_visible_on_product: bool


@dataclass(frozen=True)
class ProductVariantView:
    id: str
    product_id: str
    product_name: str
    variant_name: str
    variant_code: str
    color: str
    size: str
    sort_order: int
    is_active: bool
    is_default: bool


@dataclass(frozen=True)
class ProductBarcodeView:
    id: str
    product_id: str
    product_name: str
    barcode: str
    old_barcode: str
    purchase_price: Decimal
    sale_price: Decimal
    fk_barcode_mask_id: str | None
    mask_label: str


class ProductManagementService:
    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_cashier_summaries(self) -> list[CashierSummaryView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Cashier)
                .filter(Cashier.is_deleted.is_(False))
                .order_by(asc(Cashier.no))
                .all()
            )
            return [
                CashierSummaryView(
                    id=str(row.id),
                    no=row.no,
                    user_name=row.user_name,
                    full_name=f"{row.name} {row.last_name}".strip(),
                    is_active=bool(row.is_active),
                )
                for row in rows
            ]

    def list_products(self, search_text: str | None = None) -> list[ProductView]:
        with self._engine.get_session() as session:
            barcode_counts = (
                session.query(
                    ProductBarcode.fk_product_id.label("product_id"),
                    func.count(ProductBarcode.id).label("barcode_count"),
                )
                .filter(ProductBarcode.is_deleted.is_(False))
                .group_by(ProductBarcode.fk_product_id)
                .subquery()
            )
            variant_counts = (
                session.query(
                    ProductVariant.fk_product_id.label("product_id"),
                    func.count(ProductVariant.id).label("variant_count"),
                )
                .filter(ProductVariant.is_deleted.is_(False))
                .group_by(ProductVariant.fk_product_id)
                .subquery()
            )
            attribute_counts = (
                session.query(
                    ProductAttribute.fk_product_id.label("product_id"),
                    func.count(ProductAttribute.id).label("attribute_count"),
                )
                .filter(ProductAttribute.is_deleted.is_(False))
                .group_by(ProductAttribute.fk_product_id)
                .subquery()
            )

            query = (
                session.query(
                    Product,
                    ProductManufacturer,
                    ProductUnit,
                    Vat,
                    DepartmentMainGroup,
                    DepartmentSubGroup,
                    Warehouse,
                    barcode_counts.c.barcode_count,
                    variant_counts.c.variant_count,
                    attribute_counts.c.attribute_count,
                )
                .outerjoin(ProductManufacturer, ProductManufacturer.id == Product.fk_manufacturer_id)
                .outerjoin(ProductUnit, ProductUnit.id == Product.fk_product_unit_id)
                .outerjoin(Vat, Vat.id == Product.fk_vat_id)
                .outerjoin(
                    DepartmentMainGroup,
                    DepartmentMainGroup.id == Product.fk_department_main_group_id,
                )
                .outerjoin(
                    DepartmentSubGroup,
                    DepartmentSubGroup.id == Product.fk_department_sub_group_id,
                )
                .outerjoin(Warehouse, Warehouse.id == Product.fk_primary_warehouse_id)
                .outerjoin(barcode_counts, barcode_counts.c.product_id == Product.id)
                .outerjoin(variant_counts, variant_counts.c.product_id == Product.id)
                .outerjoin(attribute_counts, attribute_counts.c.product_id == Product.id)
                .filter(Product.is_deleted.is_(False))
                .order_by(asc(Product.code))
            )
            search_value = (search_text or "").strip()
            if search_value:
                pattern = f"%{search_value}%"
                query = query.filter(
                    Product.name.ilike(pattern)
                    | Product.code.ilike(pattern)
                    | Product.short_name.ilike(pattern)
                )

            rows = query.all()
            items: list[ProductView] = []
            for (
                product,
                manufacturer,
                unit,
                vat,
                department,
                sub_department,
                _warehouse,
                barcode_count,
                variant_count,
                attribute_count,
            ) in rows:
                items.append(
                    ProductView(
                        id=str(product.id),
                        code=product.code,
                        name=product.name,
                        short_name=product.short_name or "",
                        sale_price=Decimal(str(product.sale_price or 0)),
                        purchase_price=Decimal(str(product.purchase_price or 0)),
                        stock=int(product.stock or 0),
                        min_stock=int(product.min_stock or 0),
                        max_stock=int(product.max_stock or 0),
                        vat_no=int(product.vat_no or 1),
                        manufacturer_name=manufacturer.name if manufacturer else "-",
                        unit_name=unit.name if unit else "-",
                        vat_name=vat.name if vat else "-",
                        department_name=department.name if department else "-",
                        sub_department_name=sub_department.name if sub_department else "-",
                        barcode_count=int(barcode_count or 0),
                        variant_count=int(variant_count or 0),
                        attribute_count=int(attribute_count or 0),
                        fk_vat_id=str(product.fk_vat_id) if product.fk_vat_id else None,
                        fk_product_unit_id=(
                            str(product.fk_product_unit_id) if product.fk_product_unit_id else None
                        ),
                        fk_department_main_group_id=str(product.fk_department_main_group_id),
                        fk_department_sub_group_id=str(product.fk_department_sub_group_id),
                        fk_manufacturer_id=(
                            str(product.fk_manufacturer_id) if product.fk_manufacturer_id else None
                        ),
                        fk_primary_warehouse_id=(
                            str(product.fk_primary_warehouse_id)
                            if product.fk_primary_warehouse_id
                            else None
                        ),
                        old_code=product.old_code or "",
                        shelf_code=product.shelf_code or "",
                        description=product.description or "",
                        stock_unit=product.stock_unit or "",
                        stock_unit_no=int(product.stock_unit_no or 1),
                        is_scalable=bool(product.is_scalable),
                        is_allowed_discount=bool(product.is_allowed_discount),
                        discount_percent=int(product.discount_percent or 0),
                        is_allowed_negative_stock=bool(product.is_allowed_negative_stock),
                        is_allowed_return=bool(product.is_allowed_return),
                    )
                )
            return items

    def save_product(self, payload: dict[str, Any], product_id: str | None = None) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        code = str(payload.get("code", "")).strip()
        if not name or not code:
            return ServiceResult(False, "Product name and code are required.")

        department_main_group_id = str(payload.get("fk_department_main_group_id", "")).strip()
        department_sub_group_id = str(payload.get("fk_department_sub_group_id", "")).strip()
        if not department_main_group_id or not department_sub_group_id:
            return ServiceResult(False, "Department and sub department are required.")

        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(Product)
                    .filter(Product.code == code, Product.is_deleted.is_(False))
                    .first()
                )
                if existing and str(existing.id) != str(product_id):
                    return ServiceResult(False, f"Product code '{code}' is already in use.")

                if product_id:
                    product = (
                        session.query(Product)
                        .filter(Product.id == self._as_uuid(product_id), Product.is_deleted.is_(False))
                        .first()
                    )
                    if product is None:
                        return ServiceResult(False, "Product record not found.")
                else:
                    product = Product()
                    session.add(product)

                product.name = name
                product.short_name = str(payload.get("short_name", "")).strip() or None
                product.code = code
                product.old_code = str(payload.get("old_code", "")).strip() or None
                product.shelf_code = str(payload.get("shelf_code", "")).strip() or None
                product.description = str(payload.get("description", "")).strip() or None
                product.sale_price = Decimal(str(payload.get("sale_price", 0)))
                product.purchase_price = Decimal(str(payload.get("purchase_price", 0)))
                product.stock = int(payload.get("stock", 0))
                product.min_stock = int(payload.get("min_stock", 0))
                product.max_stock = int(payload.get("max_stock", 0))
                product.stock_unit = str(payload.get("stock_unit", "")).strip() or None
                product.stock_unit_no = int(payload.get("stock_unit_no", 1))
                product.is_scalable = bool(payload.get("is_scalable", False))
                product.is_allowed_discount = bool(payload.get("is_allowed_discount", True))
                product.discount_percent = int(payload.get("discount_percent", 0))
                product.is_allowed_negative_stock = bool(
                    payload.get("is_allowed_negative_stock", False)
                )
                product.is_allowed_return = bool(payload.get("is_allowed_return", True))
                product.fk_vat_id = self._as_uuid(payload.get("fk_vat_id"))
                product.fk_product_unit_id = self._as_uuid(payload.get("fk_product_unit_id"))
                product.fk_department_main_group_id = self._as_uuid(department_main_group_id)
                product.fk_department_sub_group_id = self._as_uuid(department_sub_group_id)
                product.fk_manufacturer_id = self._as_uuid(payload.get("fk_manufacturer_id"))
                product.fk_primary_warehouse_id = self._as_uuid(payload.get("fk_primary_warehouse_id"))
                product.fk_store_id = self._as_uuid(payload.get("fk_store_id")) or self._as_uuid(
                    self._resolve_store_id()
                )
                product.vat_no = int(payload.get("vat_no", 1))

                return ServiceResult(
                    True,
                    "Product updated successfully."
                    if product_id
                    else "Product created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(False, "Product save operation failed due to a database error.")

    def delete_product(self, product_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                product = (
                    session.query(Product)
                    .filter(Product.id == self._as_uuid(product_id), Product.is_deleted.is_(False))
                    .first()
                )
                if product is None:
                    return ServiceResult(False, "Product record not found.")
                product.is_deleted = True
                return ServiceResult(True, "Product deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Product delete operation failed due to a database error.")

    def list_manufacturers(self) -> list[ProductManufacturerView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(ProductManufacturer)
                .filter(ProductManufacturer.is_deleted.is_(False))
                .order_by(asc(ProductManufacturer.name))
                .all()
            )
            return [
                ProductManufacturerView(
                    id=str(row.id),
                    name=row.name,
                    description=row.description or "",
                )
                for row in rows
            ]

    def save_manufacturer(
        self,
        payload: dict[str, Any],
        manufacturer_id: str | None = None,
    ) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        if not name:
            return ServiceResult(False, "Manufacturer name is required.")
        description = str(payload.get("description", "")).strip()
        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(ProductManufacturer)
                    .filter(
                        ProductManufacturer.name == name,
                        ProductManufacturer.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing and str(existing.id) != str(manufacturer_id):
                    return ServiceResult(False, f"Manufacturer '{name}' already exists.")
                if manufacturer_id:
                    manufacturer = (
                        session.query(ProductManufacturer)
                        .filter(
                            ProductManufacturer.id == self._as_uuid(manufacturer_id),
                            ProductManufacturer.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if manufacturer is None:
                        return ServiceResult(False, "Manufacturer record not found.")
                else:
                    manufacturer = ProductManufacturer()
                    session.add(manufacturer)
                manufacturer.name = name
                manufacturer.description = description or None
                return ServiceResult(
                    True,
                    "Manufacturer updated successfully."
                    if manufacturer_id
                    else "Manufacturer created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Manufacturer save operation failed due to a database error.")

    def delete_manufacturer(self, manufacturer_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                manufacturer = (
                    session.query(ProductManufacturer)
                    .filter(
                        ProductManufacturer.id == self._as_uuid(manufacturer_id),
                        ProductManufacturer.is_deleted.is_(False),
                    )
                    .first()
                )
                if manufacturer is None:
                    return ServiceResult(False, "Manufacturer record not found.")
                manufacturer.is_deleted = True
                return ServiceResult(True, "Manufacturer deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Manufacturer delete operation failed due to a database error.")

    def list_product_units(self) -> list[ProductUnitView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(ProductUnit)
                .filter(ProductUnit.is_deleted.is_(False))
                .order_by(asc(ProductUnit.code))
                .all()
            )
            return [
                ProductUnitView(
                    id=str(row.id),
                    code=row.code,
                    name=row.name,
                    symbol=row.symbol or "",
                    base_amount=row.base_amount,
                    description=row.description or "",
                )
                for row in rows
            ]

    def save_product_unit(self, payload: dict[str, Any], unit_id: str | None = None) -> ServiceResult:
        code = str(payload.get("code", "")).strip()
        name = str(payload.get("name", "")).strip()
        if not code or not name:
            return ServiceResult(False, "Product unit code and name are required.")
        description = str(payload.get("description", "")).strip()
        symbol = str(payload.get("symbol", "")).strip()
        base_amount = payload.get("base_amount")
        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(ProductUnit)
                    .filter(ProductUnit.code == code, ProductUnit.is_deleted.is_(False))
                    .first()
                )
                if existing and str(existing.id) != str(unit_id):
                    return ServiceResult(False, f"Unit code '{code}' is already in use.")
                if unit_id:
                    unit = (
                        session.query(ProductUnit)
                        .filter(ProductUnit.id == self._as_uuid(unit_id), ProductUnit.is_deleted.is_(False))
                        .first()
                    )
                    if unit is None:
                        return ServiceResult(False, "Product unit record not found.")
                else:
                    unit = ProductUnit()
                    session.add(unit)
                unit.code = code
                unit.name = name
                unit.symbol = symbol or None
                unit.description = description or None
                unit.base_amount = float(base_amount) if base_amount is not None else None
                return ServiceResult(
                    True,
                    "Product unit updated successfully."
                    if unit_id
                    else "Product unit created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Product unit save operation failed due to a database error.")

    def delete_product_unit(self, unit_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                unit = (
                    session.query(ProductUnit)
                    .filter(ProductUnit.id == self._as_uuid(unit_id), ProductUnit.is_deleted.is_(False))
                    .first()
                )
                if unit is None:
                    return ServiceResult(False, "Product unit record not found.")
                unit.is_deleted = True
                return ServiceResult(True, "Product unit deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Product unit delete operation failed due to a database error.")

    def list_product_attributes(self, product_id: str | None = None) -> list[ProductAttributeView]:
        with self._engine.get_session() as session:
            query = (
                session.query(ProductAttribute, Product)
                .join(Product, Product.id == ProductAttribute.fk_product_id)
                .filter(ProductAttribute.is_deleted.is_(False), Product.is_deleted.is_(False))
                .order_by(asc(Product.code), asc(ProductAttribute.attribute_name))
            )
            if product_id:
                query = query.filter(ProductAttribute.fk_product_id == self._as_uuid(product_id))
            rows = query.all()
            return [
                ProductAttributeView(
                    id=str(attribute.id),
                    product_id=str(product.id),
                    product_name=f"{product.code} - {product.name}",
                    attribute_name=attribute.attribute_name,
                    attribute_value=attribute.attribute_value or "",
                    attribute_type=attribute.attribute_type or "text",
                    category=attribute.category or "",
                    unit=attribute.unit or "",
                    is_searchable=bool(attribute.is_searchable),
                    is_filterable=bool(attribute.is_filterable),
                    is_visible_on_product=bool(attribute.is_visible_on_product),
                )
                for attribute, product in rows
            ]

    def save_product_attribute(
        self,
        payload: dict[str, Any],
        attribute_id: str | None = None,
    ) -> ServiceResult:
        product_id = str(payload.get("product_id", "")).strip()
        attribute_name = str(payload.get("attribute_name", "")).strip()
        if not product_id or not attribute_name:
            return ServiceResult(False, "Product and attribute name are required.")
        try:
            with self._engine.get_session() as session:
                if attribute_id:
                    attribute = (
                        session.query(ProductAttribute)
                        .filter(
                            ProductAttribute.id == self._as_uuid(attribute_id),
                            ProductAttribute.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if attribute is None:
                        return ServiceResult(False, "Product attribute record not found.")
                else:
                    attribute = ProductAttribute()
                    session.add(attribute)
                attribute.fk_product_id = self._as_uuid(product_id)
                attribute.attribute_name = attribute_name
                attribute.attribute_value = str(payload.get("attribute_value", "")).strip() or None
                attribute.attribute_type = str(payload.get("attribute_type", "text")).strip() or "text"
                attribute.category = str(payload.get("category", "")).strip() or None
                attribute.unit = str(payload.get("unit", "")).strip() or None
                attribute.is_searchable = bool(payload.get("is_searchable", True))
                attribute.is_filterable = bool(payload.get("is_filterable", True))
                attribute.is_visible_on_product = bool(payload.get("is_visible_on_product", True))
                return ServiceResult(
                    True,
                    "Product attribute updated successfully."
                    if attribute_id
                    else "Product attribute created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Product attribute save operation failed due to a database error.",
            )

    def delete_product_attribute(self, attribute_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                attribute = (
                    session.query(ProductAttribute)
                    .filter(
                        ProductAttribute.id == self._as_uuid(attribute_id),
                        ProductAttribute.is_deleted.is_(False),
                    )
                    .first()
                )
                if attribute is None:
                    return ServiceResult(False, "Product attribute record not found.")
                attribute.is_deleted = True
                return ServiceResult(True, "Product attribute deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Product attribute delete operation failed due to a database error.",
            )

    def list_product_variants(self, product_id: str | None = None) -> list[ProductVariantView]:
        with self._engine.get_session() as session:
            query = (
                session.query(ProductVariant, Product)
                .join(Product, Product.id == ProductVariant.fk_product_id)
                .filter(ProductVariant.is_deleted.is_(False), Product.is_deleted.is_(False))
                .order_by(asc(Product.code), asc(ProductVariant.sort_order), asc(ProductVariant.variant_name))
            )
            if product_id:
                query = query.filter(ProductVariant.fk_product_id == self._as_uuid(product_id))
            rows = query.all()
            return [
                ProductVariantView(
                    id=str(variant.id),
                    product_id=str(product.id),
                    product_name=f"{product.code} - {product.name}",
                    variant_name=variant.variant_name,
                    variant_code=variant.variant_code,
                    color=variant.color or "",
                    size=variant.size or "",
                    sort_order=int(variant.sort_order or 0),
                    is_active=bool(variant.is_active),
                    is_default=bool(variant.is_default),
                )
                for variant, product in rows
            ]

    def save_product_variant(
        self,
        payload: dict[str, Any],
        variant_id: str | None = None,
    ) -> ServiceResult:
        product_id = str(payload.get("product_id", "")).strip()
        variant_name = str(payload.get("variant_name", "")).strip()
        variant_code = str(payload.get("variant_code", "")).strip()
        if not product_id or not variant_name or not variant_code:
            return ServiceResult(False, "Product, variant name, and variant code are required.")
        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(ProductVariant)
                    .filter(
                        ProductVariant.variant_code == variant_code,
                        ProductVariant.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing and str(existing.id) != str(variant_id):
                    return ServiceResult(False, f"Variant code '{variant_code}' is already in use.")
                if variant_id:
                    variant = (
                        session.query(ProductVariant)
                        .filter(
                            ProductVariant.id == self._as_uuid(variant_id),
                            ProductVariant.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if variant is None:
                        return ServiceResult(False, "Product variant record not found.")
                else:
                    variant = ProductVariant()
                    session.add(variant)
                variant.fk_product_id = self._as_uuid(product_id)
                variant.variant_name = variant_name
                variant.variant_code = variant_code
                variant.color = str(payload.get("color", "")).strip() or None
                variant.size = str(payload.get("size", "")).strip() or None
                variant.sort_order = int(payload.get("sort_order", 0))
                variant.is_active = bool(payload.get("is_active", True))
                variant.is_default = bool(payload.get("is_default", False))
                return ServiceResult(
                    True,
                    "Product variant updated successfully."
                    if variant_id
                    else "Product variant created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Product variant save operation failed due to a database error.",
            )

    def delete_product_variant(self, variant_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                variant = (
                    session.query(ProductVariant)
                    .filter(
                        ProductVariant.id == self._as_uuid(variant_id),
                        ProductVariant.is_deleted.is_(False),
                    )
                    .first()
                )
                if variant is None:
                    return ServiceResult(False, "Product variant record not found.")
                variant.is_deleted = True
                return ServiceResult(True, "Product variant deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Product variant delete operation failed due to a database error.",
            )

    def list_product_barcodes(self, product_id: str | None = None) -> list[ProductBarcodeView]:
        with self._engine.get_session() as session:
            query = (
                session.query(ProductBarcode, Product, ProductBarcodeMask)
                .join(Product, Product.id == ProductBarcode.fk_product_id)
                .outerjoin(ProductBarcodeMask, ProductBarcodeMask.id == ProductBarcode.fk_barcode_mask_id)
                .filter(ProductBarcode.is_deleted.is_(False), Product.is_deleted.is_(False))
                .order_by(asc(Product.code), asc(ProductBarcode.barcode))
            )
            if product_id:
                query = query.filter(ProductBarcode.fk_product_id == self._as_uuid(product_id))
            rows = query.all()
            return [
                ProductBarcodeView(
                    id=str(row.id),
                    product_id=str(product.id),
                    product_name=f"{product.code} - {product.name}",
                    barcode=row.barcode,
                    old_barcode=row.old_barcode or "",
                    purchase_price=Decimal(str(row.purchase_price or 0)),
                    sale_price=Decimal(str(row.sale_price or 0)),
                    fk_barcode_mask_id=str(mask.id) if mask else None,
                    mask_label=mask.description if mask and mask.description else "-",
                )
                for row, product, mask in rows
            ]

    def save_product_barcode(
        self,
        payload: dict[str, Any],
        barcode_id: str | None = None,
    ) -> ServiceResult:
        product_id = str(payload.get("product_id", "")).strip()
        barcode = str(payload.get("barcode", "")).strip()
        if not product_id or not barcode:
            return ServiceResult(False, "Product and barcode are required.")
        try:
            with self._engine.get_session() as session:
                existing = (
                    session.query(ProductBarcode)
                    .filter(ProductBarcode.barcode == barcode, ProductBarcode.is_deleted.is_(False))
                    .first()
                )
                if existing and str(existing.id) != str(barcode_id):
                    return ServiceResult(False, f"Barcode '{barcode}' is already in use.")
                if barcode_id:
                    barcode_row = (
                        session.query(ProductBarcode)
                        .filter(
                            ProductBarcode.id == self._as_uuid(barcode_id),
                            ProductBarcode.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if barcode_row is None:
                        return ServiceResult(False, "Product barcode record not found.")
                else:
                    barcode_row = ProductBarcode()
                    session.add(barcode_row)
                barcode_row.fk_product_id = self._as_uuid(product_id)
                barcode_row.barcode = barcode
                barcode_row.old_barcode = str(payload.get("old_barcode", "")).strip() or None
                barcode_row.purchase_price = Decimal(str(payload.get("purchase_price", 0)))
                barcode_row.sale_price = Decimal(str(payload.get("sale_price", 0)))
                barcode_row.fk_barcode_mask_id = self._as_uuid(payload.get("fk_barcode_mask_id"))
                return ServiceResult(
                    True,
                    "Product barcode updated successfully."
                    if barcode_id
                    else "Product barcode created successfully.",
                )
        except (SQLAlchemyError, ValueError, ArithmeticError):
            return ServiceResult(
                False,
                "Product barcode save operation failed due to a database error.",
            )

    def delete_product_barcode(self, barcode_id: str) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                barcode = (
                    session.query(ProductBarcode)
                    .filter(
                        ProductBarcode.id == self._as_uuid(barcode_id),
                        ProductBarcode.is_deleted.is_(False),
                    )
                    .first()
                )
                if barcode is None:
                    return ServiceResult(False, "Product barcode record not found.")
                barcode.is_deleted = True
                return ServiceResult(True, "Product barcode deleted successfully.")
        except (SQLAlchemyError, ValueError):
            return ServiceResult(
                False,
                "Product barcode delete operation failed due to a database error.",
            )

    def list_manufacturer_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=row.name)
            for row in self.list_manufacturers()
        ]

    def list_product_unit_lookups(self) -> list[LookupItem]:
        return [
            LookupItem(id=row.id, label=f"{row.code} - {row.name}")
            for row in self.list_product_units()
        ]

    def list_vat_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Vat)
                .filter(Vat.is_deleted.is_(False))
                .order_by(asc(Vat.no))
                .all()
            )
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.no} - {row.name} ({Decimal(str(row.rate or 0)):.2f}%)",
                )
                for row in rows
            ]

    def list_department_main_group_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(DepartmentMainGroup)
                .filter(DepartmentMainGroup.is_deleted.is_(False))
                .order_by(asc(DepartmentMainGroup.code))
                .all()
            )
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.code} - {row.name}",
                )
                for row in rows
            ]

    def list_department_sub_group_lookups(
        self,
        main_group_id: str | None = None,
    ) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(DepartmentSubGroup)
                .filter(DepartmentSubGroup.is_deleted.is_(False))
                .order_by(asc(DepartmentSubGroup.code))
            )
            if main_group_id:
                query = query.filter(DepartmentSubGroup.main_group_id == self._as_uuid(main_group_id))
            rows = query.all()
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.code} - {row.name}",
                )
                for row in rows
            ]

    def list_product_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Product)
                .filter(Product.is_deleted.is_(False))
                .order_by(asc(Product.code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.code} - {row.name}")
                for row in rows
            ]

    def list_barcode_mask_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(ProductBarcodeMask)
                .filter(ProductBarcodeMask.is_deleted.is_(False))
                .order_by(asc(ProductBarcodeMask.starting_digits))
                .all()
            )
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.starting_digits or '-'} / {row.description or 'Mask'}",
                )
                for row in rows
            ]

    def list_warehouse_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Warehouse)
                .filter(Warehouse.is_deleted.is_(False))
                .order_by(asc(Warehouse.code))
                .all()
            )
            return [
                LookupItem(id=str(row.id), label=f"{row.code} - {row.name}")
                for row in rows
            ]

    def _resolve_store_id(self) -> str | None:
        with self._engine.get_session() as session:
            store = (
                session.query(Store)
                .filter(Store.store_code == self._store_code, Store.is_deleted.is_(False))
                .first()
            )
            if store is None:
                store = (
                    session.query(Store)
                    .filter(Store.is_deleted.is_(False))
                    .order_by(asc(Store.store_code))
                    .first()
                )
            return str(store.id) if store else None

    @staticmethod
    def _as_uuid(value: str | UUID | None) -> UUID | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return value
        normalized = str(value).strip()
        if not normalized:
            return None
        return UUID(normalized)
