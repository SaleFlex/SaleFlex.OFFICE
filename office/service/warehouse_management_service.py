"""
Service layer for warehouse management module workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Integer, and_, asc, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased

from data_layer.engine import Engine
from data_layer.model.definition.cashier import Cashier
from data_layer.model.definition.product import Product
from data_layer.model.definition.store import Store
from data_layer.model.definition.warehouse import Warehouse
from data_layer.model.definition.warehouse_location import WarehouseLocation
from data_layer.model.definition.warehouse_product_stock import WarehouseProductStock
from data_layer.model.definition.warehouse_stock_adjustment import WarehouseStockAdjustment
from data_layer.model.definition.warehouse_stock_movement import WarehouseStockMovement
from office.service.customer_management_service import LookupItem, ServiceResult


@dataclass(frozen=True)
class WarehouseView:
    id: str
    store_id: str | None
    store_label: str
    name: str
    code: str
    warehouse_type: str
    description: str
    address: str
    manager_name: str
    contact_phone: str
    contact_email: str
    is_active: bool
    is_receiving_enabled: bool
    is_shipping_enabled: bool
    is_cycle_count_enabled: bool
    temperature_controlled: bool
    min_temperature: float | None
    max_temperature: float | None
    requires_security_access: bool
    security_level: str


@dataclass(frozen=True)
class WarehouseLocationView:
    id: str
    warehouse_id: str
    warehouse_label: str
    parent_location_id: str | None
    parent_location_label: str
    name: str
    code: str
    location_type: str
    level: int
    is_active: bool
    is_blocked: bool
    block_reason: str
    is_pick_location: bool
    is_replenishment_location: bool
    pick_sequence: int | None
    replenishment_priority: int | None


@dataclass(frozen=True)
class WarehouseStockView:
    id: str
    product_id: str
    product_label: str
    location_id: str
    location_label: str
    quantity: int
    available_quantity: int
    reserved_quantity: int
    min_stock_level: int
    max_stock_level: int
    reorder_point: int
    reorder_quantity: int
    lot_number: str
    expiration_date: date | None
    low_stock_alert: bool
    overstock_alert: bool
    expiry_alert: bool
    is_active: bool
    is_discontinued: bool
    is_blocked: bool
    block_reason: str


@dataclass(frozen=True)
class WarehouseMovementView:
    id: str
    movement_number: str
    movement_type: str
    movement_subtype: str
    status: str
    warehouse_label: str
    product_id: str
    product_label: str
    from_location_id: str | None
    from_location_label: str
    to_location_id: str | None
    to_location_label: str
    quantity: int
    movement_date: datetime | None
    reference_document: str
    reason: str
    is_approved: bool
    approved_by_id: str | None
    approved_by_label: str


@dataclass(frozen=True)
class WarehouseAdjustmentView:
    id: str
    adjustment_number: str
    adjustment_type: str
    adjustment_reason: str
    status: str
    warehouse_label: str
    product_id: str
    product_label: str
    location_id: str
    location_label: str
    system_quantity: int
    counted_quantity: int
    quantity_difference: int
    count_date: datetime | None
    is_approved: bool
    approved_by_id: str | None
    approved_by_label: str


@dataclass(frozen=True)
class WarehouseOperationView:
    warehouse_id: str
    warehouse_name: str
    warehouse_code: str
    warehouse_type: str
    is_active: bool
    location_count: int
    stock_row_count: int
    total_quantity: int
    low_stock_count: int
    pending_movement_count: int
    pending_adjustment_count: int
    last_movement_date: datetime | None


class WarehouseManagementService:
    def __init__(self, store_code: str) -> None:
        self._engine = Engine()
        self._store_code = store_code

    def list_warehouses(self) -> list[WarehouseView]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Warehouse, Store)
                .outerjoin(Store, Store.id == Warehouse.fk_store_id)
                .filter(Warehouse.is_deleted.is_(False))
                .order_by(desc(Warehouse.is_active), asc(Warehouse.name))
                .all()
            )
            return [
                WarehouseView(
                    id=str(warehouse.id),
                    store_id=str(warehouse.fk_store_id) if warehouse.fk_store_id else None,
                    store_label=f"{store.store_code or ''} - {store.brand_name or store.company_name or ''}".strip(" -") if store else "",
                    name=warehouse.name or "",
                    code=warehouse.code or "",
                    warehouse_type=warehouse.warehouse_type or "",
                    description=warehouse.description or "",
                    address=warehouse.address or "",
                    manager_name=warehouse.manager_name or "",
                    contact_phone=warehouse.contact_phone or "",
                    contact_email=warehouse.contact_email or "",
                    is_active=bool(warehouse.is_active),
                    is_receiving_enabled=bool(warehouse.is_receiving_enabled),
                    is_shipping_enabled=bool(warehouse.is_shipping_enabled),
                    is_cycle_count_enabled=bool(warehouse.is_cycle_count_enabled),
                    temperature_controlled=bool(warehouse.temperature_controlled),
                    min_temperature=warehouse.min_temperature,
                    max_temperature=warehouse.max_temperature,
                    requires_security_access=bool(warehouse.requires_security_access),
                    security_level=warehouse.security_level or "",
                )
                for warehouse, store in rows
            ]

    def save_warehouse(
        self,
        payload: dict[str, Any],
        warehouse_id: str | None = None,
    ) -> ServiceResult:
        name = str(payload.get("name", "")).strip()
        code = str(payload.get("code", "")).strip().upper()
        warehouse_type = str(payload.get("warehouse_type", "")).strip().upper()
        if not name or not code or not warehouse_type:
            return ServiceResult(False, "Warehouse name, code, and type are required.")
        try:
            with self._engine.get_session() as session:
                existing_by_code = (
                    session.query(Warehouse)
                    .filter(Warehouse.code == code, Warehouse.is_deleted.is_(False))
                    .first()
                )
                if existing_by_code and str(existing_by_code.id) != str(warehouse_id):
                    return ServiceResult(False, "Warehouse code is already in use.")

                if warehouse_id:
                    row = (
                        session.query(Warehouse)
                        .filter(Warehouse.id == self._as_uuid(warehouse_id), Warehouse.is_deleted.is_(False))
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Warehouse record not found.")
                else:
                    row = Warehouse()
                    session.add(row)

                store_id = self._as_uuid(payload.get("store_id"))
                if store_id is None:
                    store_id = self._default_store_id(session)
                if store_id is None:
                    return ServiceResult(False, "A valid store is required for warehouse.")

                row.fk_store_id = store_id
                row.name = name
                row.code = code
                row.warehouse_type = warehouse_type
                row.description = str(payload.get("description", "")).strip()
                row.address = str(payload.get("address", "")).strip()
                row.manager_name = str(payload.get("manager_name", "")).strip()
                row.contact_phone = str(payload.get("contact_phone", "")).strip()
                row.contact_email = str(payload.get("contact_email", "")).strip()
                row.is_active = bool(payload.get("is_active", True))
                row.is_receiving_enabled = bool(payload.get("is_receiving_enabled", True))
                row.is_shipping_enabled = bool(payload.get("is_shipping_enabled", True))
                row.is_cycle_count_enabled = bool(payload.get("is_cycle_count_enabled", True))
                row.temperature_controlled = bool(payload.get("temperature_controlled", False))
                row.min_temperature = self._as_float(payload.get("min_temperature"))
                row.max_temperature = self._as_float(payload.get("max_temperature"))
                row.requires_security_access = bool(payload.get("requires_security_access", False))
                row.security_level = str(payload.get("security_level", "")).strip().upper()

                return ServiceResult(
                    True,
                    "Warehouse updated successfully."
                    if warehouse_id
                    else "Warehouse created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Warehouse save operation failed due to a database error.")

    def delete_warehouse(self, warehouse_id: str) -> ServiceResult:
        return self._soft_delete(
            model=Warehouse,
            record_id=warehouse_id,
            not_found_message="Warehouse record not found.",
            success_message="Warehouse deleted successfully.",
            fail_message="Warehouse delete operation failed due to a database error.",
        )

    def list_warehouse_locations(self, warehouse_id: str | None = None) -> list[WarehouseLocationView]:
        with self._engine.get_session() as session:
            parent_alias = aliased(WarehouseLocation)
            query = (
                session.query(WarehouseLocation, Warehouse, parent_alias)
                .join(Warehouse, Warehouse.id == WarehouseLocation.fk_warehouse_id)
                .outerjoin(parent_alias, parent_alias.id == WarehouseLocation.parent_location_id)
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    Warehouse.is_deleted.is_(False),
                )
                .order_by(asc(Warehouse.name), asc(WarehouseLocation.level), asc(WarehouseLocation.code))
            )
            if warehouse_id:
                query = query.filter(WarehouseLocation.fk_warehouse_id == self._as_uuid(warehouse_id))
            rows = query.all()
            return [
                WarehouseLocationView(
                    id=str(location.id),
                    warehouse_id=str(location.fk_warehouse_id),
                    warehouse_label=warehouse.name or "",
                    parent_location_id=str(location.parent_location_id) if location.parent_location_id else None,
                    parent_location_label=parent.name if parent and parent.name else "",
                    name=location.name or "",
                    code=location.code or "",
                    location_type=location.location_type or "",
                    level=int(location.level or 1),
                    is_active=bool(location.is_active),
                    is_blocked=bool(location.is_blocked),
                    block_reason=location.block_reason or "",
                    is_pick_location=bool(location.is_pick_location),
                    is_replenishment_location=bool(location.is_replenishment_location),
                    pick_sequence=location.pick_sequence,
                    replenishment_priority=location.replenishment_priority,
                )
                for location, warehouse, parent in rows
            ]

    def save_warehouse_location(
        self,
        payload: dict[str, Any],
        location_id: str | None = None,
    ) -> ServiceResult:
        warehouse_id = str(payload.get("warehouse_id", "")).strip()
        name = str(payload.get("name", "")).strip()
        code = str(payload.get("code", "")).strip().upper()
        location_type = str(payload.get("location_type", "")).strip().upper()
        if not warehouse_id or not name or not code or not location_type:
            return ServiceResult(False, "Warehouse, name, code, and location type are required.")
        try:
            with self._engine.get_session() as session:
                existing_by_code = (
                    session.query(WarehouseLocation)
                    .filter(WarehouseLocation.code == code, WarehouseLocation.is_deleted.is_(False))
                    .first()
                )
                if existing_by_code and str(existing_by_code.id) != str(location_id):
                    return ServiceResult(False, "Warehouse location code is already in use.")

                if location_id:
                    row = (
                        session.query(WarehouseLocation)
                        .filter(
                            WarehouseLocation.id == self._as_uuid(location_id),
                            WarehouseLocation.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Warehouse location record not found.")
                else:
                    row = WarehouseLocation()
                    session.add(row)

                row.fk_warehouse_id = self._as_uuid(warehouse_id)
                row.parent_location_id = self._as_uuid(payload.get("parent_location_id"))
                row.name = name
                row.code = code
                row.location_type = location_type
                row.level = int(payload.get("level", 1) or 1)
                row.description = str(payload.get("description", "")).strip()
                row.is_active = bool(payload.get("is_active", True))
                row.is_blocked = bool(payload.get("is_blocked", False))
                row.block_reason = str(payload.get("block_reason", "")).strip()
                row.is_pick_location = bool(payload.get("is_pick_location", True))
                row.is_replenishment_location = bool(payload.get("is_replenishment_location", True))
                row.pick_sequence = self._as_int(payload.get("pick_sequence"))
                row.replenishment_priority = self._as_int(payload.get("replenishment_priority"))

                return ServiceResult(
                    True,
                    "Warehouse location updated successfully."
                    if location_id
                    else "Warehouse location created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Warehouse location save operation failed due to a database error.")

    def delete_warehouse_location(self, location_id: str) -> ServiceResult:
        return self._soft_delete(
            model=WarehouseLocation,
            record_id=location_id,
            not_found_message="Warehouse location record not found.",
            success_message="Warehouse location deleted successfully.",
            fail_message="Warehouse location delete operation failed due to a database error.",
        )

    def list_warehouse_product_stocks(
        self,
        warehouse_id: str | None = None,
        location_id: str | None = None,
    ) -> list[WarehouseStockView]:
        with self._engine.get_session() as session:
            query = (
                session.query(WarehouseProductStock, Product, WarehouseLocation, Warehouse)
                .join(Product, Product.id == WarehouseProductStock.fk_product_id)
                .join(WarehouseLocation, WarehouseLocation.id == WarehouseProductStock.fk_warehouse_location_id)
                .join(Warehouse, Warehouse.id == WarehouseLocation.fk_warehouse_id)
                .filter(
                    WarehouseProductStock.is_deleted.is_(False),
                    Product.is_deleted.is_(False),
                    WarehouseLocation.is_deleted.is_(False),
                    Warehouse.is_deleted.is_(False),
                )
                .order_by(asc(Product.name), asc(WarehouseLocation.code))
            )
            if warehouse_id:
                query = query.filter(Warehouse.id == self._as_uuid(warehouse_id))
            if location_id:
                query = query.filter(WarehouseLocation.id == self._as_uuid(location_id))
            rows = query.all()
            return [
                WarehouseStockView(
                    id=str(stock.id),
                    product_id=str(stock.fk_product_id),
                    product_label=product.name or "",
                    location_id=str(stock.fk_warehouse_location_id),
                    location_label=f"{warehouse.name} / {location.code}",
                    quantity=int(stock.quantity or 0),
                    available_quantity=int(stock.available_quantity or 0),
                    reserved_quantity=int(stock.reserved_quantity or 0),
                    min_stock_level=int(stock.min_stock_level or 0),
                    max_stock_level=int(stock.max_stock_level or 0),
                    reorder_point=int(stock.reorder_point or 0),
                    reorder_quantity=int(stock.reorder_quantity or 0),
                    lot_number=stock.lot_number or "",
                    expiration_date=stock.expiration_date,
                    low_stock_alert=bool(stock.low_stock_alert),
                    overstock_alert=bool(stock.overstock_alert),
                    expiry_alert=bool(stock.expiry_alert),
                    is_active=bool(stock.is_active),
                    is_discontinued=bool(stock.is_discontinued),
                    is_blocked=bool(stock.is_blocked),
                    block_reason=stock.block_reason or "",
                )
                for stock, product, location, warehouse in rows
            ]

    def save_warehouse_product_stock(
        self,
        payload: dict[str, Any],
        stock_id: str | None = None,
    ) -> ServiceResult:
        product_id = str(payload.get("product_id", "")).strip()
        warehouse_location_id = str(payload.get("warehouse_location_id", "")).strip()
        if not product_id or not warehouse_location_id:
            return ServiceResult(False, "Product and warehouse location are required.")
        try:
            with self._engine.get_session() as session:
                if stock_id:
                    row = (
                        session.query(WarehouseProductStock)
                        .filter(
                            WarehouseProductStock.id == self._as_uuid(stock_id),
                            WarehouseProductStock.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Warehouse stock record not found.")
                else:
                    existing = (
                        session.query(WarehouseProductStock)
                        .filter(
                            WarehouseProductStock.fk_product_id == self._as_uuid(product_id),
                            WarehouseProductStock.fk_warehouse_location_id == self._as_uuid(warehouse_location_id),
                            WarehouseProductStock.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if existing:
                        return ServiceResult(
                            False,
                            "Stock row already exists for selected product and warehouse location.",
                        )
                    row = WarehouseProductStock()
                    session.add(row)

                row.fk_product_id = self._as_uuid(product_id)
                row.fk_warehouse_location_id = self._as_uuid(warehouse_location_id)
                row.quantity = int(payload.get("quantity", 0) or 0)
                row.available_quantity = int(payload.get("available_quantity", 0) or 0)
                row.reserved_quantity = int(payload.get("reserved_quantity", 0) or 0)
                row.min_stock_level = int(payload.get("min_stock_level", 0) or 0)
                row.max_stock_level = int(payload.get("max_stock_level", 0) or 0)
                row.reorder_point = int(payload.get("reorder_point", 0) or 0)
                row.reorder_quantity = int(payload.get("reorder_quantity", 0) or 0)
                row.lot_number = str(payload.get("lot_number", "")).strip()
                row.expiration_date = self._parse_date(payload.get("expiration_date"))
                row.low_stock_alert = bool(payload.get("low_stock_alert", False))
                row.overstock_alert = bool(payload.get("overstock_alert", False))
                row.expiry_alert = bool(payload.get("expiry_alert", False))
                row.is_active = bool(payload.get("is_active", True))
                row.is_discontinued = bool(payload.get("is_discontinued", False))
                row.is_blocked = bool(payload.get("is_blocked", False))
                row.block_reason = str(payload.get("block_reason", "")).strip()

                return ServiceResult(
                    True,
                    "Warehouse stock updated successfully."
                    if stock_id
                    else "Warehouse stock created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Warehouse stock save operation failed due to a database error.")

    def delete_warehouse_product_stock(self, stock_id: str) -> ServiceResult:
        return self._soft_delete(
            model=WarehouseProductStock,
            record_id=stock_id,
            not_found_message="Warehouse stock record not found.",
            success_message="Warehouse stock deleted successfully.",
            fail_message="Warehouse stock delete operation failed due to a database error.",
        )

    def list_warehouse_stock_movements(
        self,
        warehouse_id: str | None = None,
        status: str | None = None,
    ) -> list[WarehouseMovementView]:
        with self._engine.get_session() as session:
            from_location = aliased(WarehouseLocation)
            to_location = aliased(WarehouseLocation)
            approved_by = aliased(Cashier)
            query = (
                session.query(
                    WarehouseStockMovement,
                    Product,
                    from_location,
                    to_location,
                    approved_by,
                    Warehouse,
                )
                .join(Product, Product.id == WarehouseStockMovement.fk_product_id)
                .outerjoin(from_location, from_location.id == WarehouseStockMovement.fk_warehouse_location_from)
                .outerjoin(to_location, to_location.id == WarehouseStockMovement.fk_warehouse_location_to)
                .outerjoin(approved_by, approved_by.id == WarehouseStockMovement.approved_by)
                .outerjoin(
                    Warehouse,
                    and_(
                        Warehouse.id
                        == func.coalesce(
                            from_location.fk_warehouse_id,
                            to_location.fk_warehouse_id,
                        )
                    ),
                )
                .filter(
                    WarehouseStockMovement.is_deleted.is_(False),
                    Product.is_deleted.is_(False),
                )
                .order_by(desc(WarehouseStockMovement.movement_date), asc(WarehouseStockMovement.movement_number))
            )
            if warehouse_id:
                warehouse_uuid = self._as_uuid(warehouse_id)
                query = query.filter(
                    (from_location.fk_warehouse_id == warehouse_uuid)
                    | (to_location.fk_warehouse_id == warehouse_uuid)
                )
            status_text = str(status or "").strip().upper()
            if status_text:
                query = query.filter(WarehouseStockMovement.status == status_text)
            rows = query.all()
            return [
                WarehouseMovementView(
                    id=str(movement.id),
                    movement_number=movement.movement_number or "",
                    movement_type=movement.movement_type or "",
                    movement_subtype=movement.movement_subtype or "",
                    status=movement.status or "",
                    warehouse_label=warehouse.name if warehouse and warehouse.name else "",
                    product_id=str(movement.fk_product_id),
                    product_label=product.name or "",
                    from_location_id=str(movement.fk_warehouse_location_from)
                    if movement.fk_warehouse_location_from
                    else None,
                    from_location_label=from_loc.code if from_loc and from_loc.code else "",
                    to_location_id=str(movement.fk_warehouse_location_to)
                    if movement.fk_warehouse_location_to
                    else None,
                    to_location_label=to_loc.code if to_loc and to_loc.code else "",
                    quantity=int(movement.quantity or 0),
                    movement_date=movement.movement_date,
                    reference_document=movement.reference_document or "",
                    reason=movement.reason or "",
                    is_approved=bool(movement.is_approved),
                    approved_by_id=str(movement.approved_by) if movement.approved_by else None,
                    approved_by_label=approved.user_name if approved and approved.user_name else "",
                )
                for movement, product, from_loc, to_loc, approved, warehouse in rows
            ]

    def save_warehouse_stock_movement(
        self,
        payload: dict[str, Any],
        movement_id: str | None = None,
    ) -> ServiceResult:
        movement_number = str(payload.get("movement_number", "")).strip().upper()
        product_id = str(payload.get("product_id", "")).strip()
        movement_type = str(payload.get("movement_type", "")).strip().upper()
        quantity = int(payload.get("quantity", 0) or 0)
        if not movement_number or not product_id or not movement_type:
            return ServiceResult(False, "Movement number, product, and movement type are required.")
        if quantity == 0:
            return ServiceResult(False, "Movement quantity cannot be zero.")
        try:
            with self._engine.get_session() as session:
                existing_by_number = (
                    session.query(WarehouseStockMovement)
                    .filter(
                        WarehouseStockMovement.movement_number == movement_number,
                        WarehouseStockMovement.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_number and str(existing_by_number.id) != str(movement_id):
                    return ServiceResult(False, "Movement number is already in use.")

                if movement_id:
                    row = (
                        session.query(WarehouseStockMovement)
                        .filter(
                            WarehouseStockMovement.id == self._as_uuid(movement_id),
                            WarehouseStockMovement.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Warehouse movement record not found.")
                else:
                    row = WarehouseStockMovement()
                    session.add(row)

                row.movement_number = movement_number
                row.fk_product_id = self._as_uuid(product_id)
                row.fk_warehouse_location_from = self._as_uuid(payload.get("warehouse_location_from"))
                row.fk_warehouse_location_to = self._as_uuid(payload.get("warehouse_location_to"))
                row.movement_type = movement_type
                row.movement_subtype = str(payload.get("movement_subtype", "")).strip().upper()
                row.quantity = quantity
                row.status = str(payload.get("status", "PENDING")).strip().upper() or "PENDING"
                row.movement_date = self._parse_datetime(payload.get("movement_date")) or datetime.now()
                row.reference_document = str(payload.get("reference_document", "")).strip()
                row.reason = str(payload.get("reason", "")).strip()
                row.description = str(payload.get("description", "")).strip()
                row.is_approved = bool(payload.get("is_approved", False))
                row.approved_by = self._as_uuid(payload.get("approved_by"))
                row.approved_at = self._parse_datetime(payload.get("approved_at"))

                return ServiceResult(
                    True,
                    "Warehouse stock movement updated successfully."
                    if movement_id
                    else "Warehouse stock movement created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Warehouse stock movement save operation failed due to a database error.")

    def delete_warehouse_stock_movement(self, movement_id: str) -> ServiceResult:
        return self._soft_delete(
            model=WarehouseStockMovement,
            record_id=movement_id,
            not_found_message="Warehouse stock movement record not found.",
            success_message="Warehouse stock movement deleted successfully.",
            fail_message="Warehouse stock movement delete operation failed due to a database error.",
        )

    def list_warehouse_stock_adjustments(
        self,
        warehouse_id: str | None = None,
        status: str | None = None,
    ) -> list[WarehouseAdjustmentView]:
        with self._engine.get_session() as session:
            approved_by = aliased(Cashier)
            query = (
                session.query(
                    WarehouseStockAdjustment,
                    Product,
                    WarehouseLocation,
                    Warehouse,
                    approved_by,
                )
                .join(Product, Product.id == WarehouseStockAdjustment.fk_product_id)
                .join(WarehouseLocation, WarehouseLocation.id == WarehouseStockAdjustment.fk_warehouse_location_id)
                .join(Warehouse, Warehouse.id == WarehouseLocation.fk_warehouse_id)
                .outerjoin(approved_by, approved_by.id == WarehouseStockAdjustment.approved_by)
                .filter(
                    WarehouseStockAdjustment.is_deleted.is_(False),
                    Product.is_deleted.is_(False),
                    WarehouseLocation.is_deleted.is_(False),
                    Warehouse.is_deleted.is_(False),
                )
                .order_by(desc(WarehouseStockAdjustment.count_date), asc(WarehouseStockAdjustment.adjustment_number))
            )
            if warehouse_id:
                query = query.filter(Warehouse.id == self._as_uuid(warehouse_id))
            status_text = str(status or "").strip().upper()
            if status_text:
                query = query.filter(WarehouseStockAdjustment.status == status_text)
            rows = query.all()
            return [
                WarehouseAdjustmentView(
                    id=str(adjustment.id),
                    adjustment_number=adjustment.adjustment_number or "",
                    adjustment_type=adjustment.adjustment_type or "",
                    adjustment_reason=adjustment.adjustment_reason or "",
                    status=adjustment.status or "",
                    warehouse_label=warehouse.name or "",
                    product_id=str(adjustment.fk_product_id),
                    product_label=product.name or "",
                    location_id=str(adjustment.fk_warehouse_location_id),
                    location_label=location.code or "",
                    system_quantity=int(adjustment.system_quantity or 0),
                    counted_quantity=int(adjustment.counted_quantity or 0),
                    quantity_difference=int(adjustment.quantity_difference or 0),
                    count_date=adjustment.count_date,
                    is_approved=bool(adjustment.is_approved),
                    approved_by_id=str(adjustment.approved_by) if adjustment.approved_by else None,
                    approved_by_label=approved.user_name if approved and approved.user_name else "",
                )
                for adjustment, product, location, warehouse, approved in rows
            ]

    def save_warehouse_stock_adjustment(
        self,
        payload: dict[str, Any],
        adjustment_id: str | None = None,
    ) -> ServiceResult:
        adjustment_number = str(payload.get("adjustment_number", "")).strip().upper()
        product_id = str(payload.get("product_id", "")).strip()
        location_id = str(payload.get("warehouse_location_id", "")).strip()
        adjustment_type = str(payload.get("adjustment_type", "")).strip().upper()
        if not adjustment_number or not product_id or not location_id or not adjustment_type:
            return ServiceResult(
                False,
                "Adjustment number, product, location, and adjustment type are required.",
            )
        try:
            with self._engine.get_session() as session:
                existing_by_number = (
                    session.query(WarehouseStockAdjustment)
                    .filter(
                        WarehouseStockAdjustment.adjustment_number == adjustment_number,
                        WarehouseStockAdjustment.is_deleted.is_(False),
                    )
                    .first()
                )
                if existing_by_number and str(existing_by_number.id) != str(adjustment_id):
                    return ServiceResult(False, "Adjustment number is already in use.")

                if adjustment_id:
                    row = (
                        session.query(WarehouseStockAdjustment)
                        .filter(
                            WarehouseStockAdjustment.id == self._as_uuid(adjustment_id),
                            WarehouseStockAdjustment.is_deleted.is_(False),
                        )
                        .first()
                    )
                    if row is None:
                        return ServiceResult(False, "Warehouse adjustment record not found.")
                else:
                    row = WarehouseStockAdjustment()
                    session.add(row)

                system_quantity = int(payload.get("system_quantity", 0) or 0)
                counted_quantity = int(payload.get("counted_quantity", 0) or 0)
                quantity_difference = payload.get("quantity_difference")
                if quantity_difference in (None, ""):
                    quantity_difference = counted_quantity - system_quantity

                row.adjustment_number = adjustment_number
                row.fk_product_id = self._as_uuid(product_id)
                row.fk_warehouse_location_id = self._as_uuid(location_id)
                row.adjustment_type = adjustment_type
                row.adjustment_reason = str(payload.get("adjustment_reason", "")).strip().upper()
                row.system_quantity = system_quantity
                row.counted_quantity = counted_quantity
                row.quantity_difference = int(quantity_difference)
                row.status = str(payload.get("status", "PENDING")).strip().upper() or "PENDING"
                row.count_date = self._parse_datetime(payload.get("count_date")) or datetime.now()
                row.is_approved = bool(payload.get("is_approved", False))
                row.approved_by = self._as_uuid(payload.get("approved_by"))
                row.approved_at = self._parse_datetime(payload.get("approved_at"))
                row.counter_notes = str(payload.get("counter_notes", "")).strip()
                row.supervisor_notes = str(payload.get("supervisor_notes", "")).strip()

                return ServiceResult(
                    True,
                    "Warehouse stock adjustment updated successfully."
                    if adjustment_id
                    else "Warehouse stock adjustment created successfully.",
                )
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, "Warehouse stock adjustment save operation failed due to a database error.")

    def delete_warehouse_stock_adjustment(self, adjustment_id: str) -> ServiceResult:
        return self._soft_delete(
            model=WarehouseStockAdjustment,
            record_id=adjustment_id,
            not_found_message="Warehouse stock adjustment record not found.",
            success_message="Warehouse stock adjustment deleted successfully.",
            fail_message="Warehouse stock adjustment delete operation failed due to a database error.",
        )

    def list_warehouse_operations(
        self,
        warehouse_id: str | None = None,
        active_only: bool | None = None,
    ) -> list[WarehouseOperationView]:
        with self._engine.get_session() as session:
            query = (
                session.query(Warehouse)
                .filter(Warehouse.is_deleted.is_(False))
                .order_by(asc(Warehouse.name))
            )
            if warehouse_id:
                query = query.filter(Warehouse.id == self._as_uuid(warehouse_id))
            if active_only is True:
                query = query.filter(Warehouse.is_active.is_(True))
            if active_only is False:
                query = query.filter(Warehouse.is_active.is_(False))
            warehouses = query.all()
            if not warehouses:
                return []

            warehouse_ids = [item.id for item in warehouses]

            location_rows = (
                session.query(
                    WarehouseLocation.fk_warehouse_id,
                    func.count(WarehouseLocation.id),
                )
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    WarehouseLocation.fk_warehouse_id.in_(warehouse_ids),
                )
                .group_by(WarehouseLocation.fk_warehouse_id)
                .all()
            )
            location_count_map = {warehouse_key: int(count or 0) for warehouse_key, count in location_rows}

            stock_rows = (
                session.query(
                    WarehouseLocation.fk_warehouse_id,
                    func.count(WarehouseProductStock.id),
                    func.coalesce(func.sum(WarehouseProductStock.quantity), 0),
                    func.coalesce(
                        func.sum(
                            func.cast(
                                WarehouseProductStock.low_stock_alert,
                                Integer,
                            )
                        ),
                        0,
                    ),
                )
                .join(
                    WarehouseProductStock,
                    WarehouseProductStock.fk_warehouse_location_id == WarehouseLocation.id,
                )
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    WarehouseProductStock.is_deleted.is_(False),
                    WarehouseLocation.fk_warehouse_id.in_(warehouse_ids),
                )
                .group_by(WarehouseLocation.fk_warehouse_id)
                .all()
            )
            stock_map = {
                warehouse_key: (
                    int(row_count or 0),
                    int(total_quantity or 0),
                    int(low_stock_count or 0),
                )
                for warehouse_key, row_count, total_quantity, low_stock_count in stock_rows
            }

            movement_rows = (
                session.query(
                    WarehouseLocation.fk_warehouse_id,
                    func.count(WarehouseStockMovement.id),
                    func.max(WarehouseStockMovement.movement_date),
                )
                .join(
                    WarehouseStockMovement,
                    WarehouseStockMovement.fk_warehouse_location_from == WarehouseLocation.id,
                )
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    WarehouseStockMovement.is_deleted.is_(False),
                    WarehouseStockMovement.status == "PENDING",
                    WarehouseLocation.fk_warehouse_id.in_(warehouse_ids),
                )
                .group_by(WarehouseLocation.fk_warehouse_id)
                .all()
            )
            movement_map = {
                warehouse_key: (
                    int(pending_count or 0),
                    last_movement_at,
                )
                for warehouse_key, pending_count, last_movement_at in movement_rows
            }

            adjustment_rows = (
                session.query(
                    WarehouseLocation.fk_warehouse_id,
                    func.count(WarehouseStockAdjustment.id),
                )
                .join(
                    WarehouseStockAdjustment,
                    WarehouseStockAdjustment.fk_warehouse_location_id == WarehouseLocation.id,
                )
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    WarehouseStockAdjustment.is_deleted.is_(False),
                    WarehouseStockAdjustment.status == "PENDING",
                    WarehouseLocation.fk_warehouse_id.in_(warehouse_ids),
                )
                .group_by(WarehouseLocation.fk_warehouse_id)
                .all()
            )
            adjustment_map = {
                warehouse_key: int(pending_count or 0) for warehouse_key, pending_count in adjustment_rows
            }

            return [
                WarehouseOperationView(
                    warehouse_id=str(warehouse.id),
                    warehouse_name=warehouse.name or "",
                    warehouse_code=warehouse.code or "",
                    warehouse_type=warehouse.warehouse_type or "",
                    is_active=bool(warehouse.is_active),
                    location_count=location_count_map.get(warehouse.id, 0),
                    stock_row_count=stock_map.get(warehouse.id, (0, 0, 0))[0],
                    total_quantity=stock_map.get(warehouse.id, (0, 0, 0))[1],
                    low_stock_count=stock_map.get(warehouse.id, (0, 0, 0))[2],
                    pending_movement_count=movement_map.get(warehouse.id, (0, None))[0],
                    pending_adjustment_count=adjustment_map.get(warehouse.id, 0),
                    last_movement_date=movement_map.get(warehouse.id, (0, None))[1],
                )
                for warehouse in warehouses
            ]

    def list_store_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Store)
                .filter(Store.is_deleted.is_(False))
                .order_by(asc(Store.store_code))
                .all()
            )
            return [
                LookupItem(
                    id=str(row.id),
                    label=f"{row.store_code or ''} - {row.brand_name or row.company_name or ''}".strip(" -"),
                )
                for row in rows
            ]

    def list_warehouse_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Warehouse)
                .filter(Warehouse.is_deleted.is_(False))
                .order_by(desc(Warehouse.is_active), asc(Warehouse.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=f"{row.code} - {row.name}") for row in rows]

    def list_warehouse_location_lookups(self, warehouse_id: str | None = None) -> list[LookupItem]:
        with self._engine.get_session() as session:
            query = (
                session.query(WarehouseLocation, Warehouse)
                .join(Warehouse, Warehouse.id == WarehouseLocation.fk_warehouse_id)
                .filter(
                    WarehouseLocation.is_deleted.is_(False),
                    Warehouse.is_deleted.is_(False),
                )
                .order_by(asc(Warehouse.name), asc(WarehouseLocation.level), asc(WarehouseLocation.code))
            )
            if warehouse_id:
                query = query.filter(WarehouseLocation.fk_warehouse_id == self._as_uuid(warehouse_id))
            rows = query.all()
            return [
                LookupItem(
                    id=str(location.id),
                    label=f"{warehouse.code}/{location.code} - {location.name}",
                )
                for location, warehouse in rows
            ]

    def list_product_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Product)
                .filter(Product.is_deleted.is_(False))
                .order_by(asc(Product.name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.name or "") for row in rows]

    def list_cashier_lookups(self) -> list[LookupItem]:
        with self._engine.get_session() as session:
            rows = (
                session.query(Cashier)
                .filter(Cashier.is_deleted.is_(False))
                .order_by(asc(Cashier.user_name))
                .all()
            )
            return [LookupItem(id=str(row.id), label=row.user_name or "") for row in rows]

    def _default_store_id(self, session) -> UUID | None:
        row = (
            session.query(Store)
            .filter(Store.code == self._store_code, Store.is_deleted.is_(False))
            .first()
        )
        return row.id if row else None

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

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        return date.fromisoformat(raw)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        if "T" in raw:
            return datetime.fromisoformat(raw)
        if len(raw) == 16:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return datetime.fromisoformat(raw)

    @staticmethod
    def _as_int(value: Any) -> int | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        return int(raw)

    @staticmethod
    def _as_float(value: Any) -> float | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        return float(raw)

    def _soft_delete(
        self,
        model: Any,
        record_id: str,
        not_found_message: str,
        success_message: str,
        fail_message: str,
    ) -> ServiceResult:
        try:
            with self._engine.get_session() as session:
                row = (
                    session.query(model)
                    .filter(model.id == self._as_uuid(record_id), model.is_deleted.is_(False))
                    .first()
                )
                if row is None:
                    return ServiceResult(False, not_found_message)
                row.is_deleted = True
                return ServiceResult(True, success_message)
        except (SQLAlchemyError, ValueError):
            return ServiceResult(False, fail_message)
