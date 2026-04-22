# Warehouse Management Module

This document describes the dedicated warehouse management workflows implemented in `SaleFlex.OFFICE`.

## Purpose

`WarehouseManagementForm` centralizes warehouse definition tables and warehouse operation tables in one module-level workspace.
It is opened from `ModuleLauncherForm` by the `Warehouse Management` module button.

## Implemented Tabs

The form is organized into six tabs:

1. **Warehouses**
   - Create, update, and soft delete warehouse definitions.
   - Manage warehouse code/type, active flags, receiving/shipping flags, security and temperature metadata.
2. **Warehouse Locations**
   - Create, update, and soft delete location definitions linked to warehouses.
   - Manage parent location, location type/level, block state, and pick/replenishment settings.
3. **Warehouse Product Stock**
   - Create, update, and soft delete product stock rows linked to warehouse locations.
   - Manage quantity, available/reserved stock, min/max/reorder thresholds, lot and expiry fields, and block flags.
4. **Stock Movements**
   - Create, update, and soft delete warehouse stock movement rows.
   - Manage movement number/type/status, source-target locations, movement quantity/date, and approval metadata.
5. **Stock Adjustments**
   - Create, update, and soft delete stock adjustment rows.
   - Manage adjustment number/type/status, system-counted-difference quantities, count date, and approval metadata.
6. **Warehouse Operations**
   - Read-only warehouse operations listing inside the module.
   - Filters by warehouse and active status.

## Additional Operations Form

`WarehouseOperationsForm` is also available as a standalone read-only window.
It can be opened from `WarehouseManagementForm` via `Open Warehouse Operations Window`.

The window provides:

- warehouse-level operational summary rows,
- location and stock-row counts,
- total quantity, low-stock row count, pending movement/adjustment counts,
- last movement timestamp for operations teams.

## Service Layer

Warehouse workflows are coordinated by `office/service/warehouse_management_service.py`.

Service responsibilities:

- Typed view model generation for warehouse definition and operations tabs.
- CRUD validation and uniqueness checks for warehouse, location, movement, and adjustment identifiers.
- Soft delete lifecycle handling for all warehouse tables.
- Warehouse operations aggregation for operational monitoring.

## Data Models Used

The module currently uses:

- `warehouse`
- `warehouse_location`
- `warehouse_product_stock`
- `warehouse_stock_movement`
- `warehouse_stock_adjustment`
- `product`
- `store`
- `cashier`

## Notes

- Date fields are entered as `YYYY-MM-DD`.
- Datetime fields are entered as `YYYY-MM-DD HH:MM`.
- All delete operations in this module use soft delete strategy.

---

[Back to index](README.md) | [Previous: Loyalty Management Module](20-loyalty-management-module.md)
