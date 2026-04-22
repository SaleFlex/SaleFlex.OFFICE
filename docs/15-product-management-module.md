# Product Management Module

This document describes the implemented product operations module in `SaleFlex.OFFICE`.

## Purpose

`ProductManagementForm` provides an Excel-like operational workspace for product lifecycle and all core product-related definition tables.
The module is launched from `ModuleLauncherForm` using the `Product Management` button.

## Implemented Tabs

The form is organized into eight tabs:

1. **Products**
   - Grid-based product listing with quick search.
   - New product creation.
   - Existing product update.
   - Soft delete for product records.
   - Product master fields for pricing, stock, discount policy, and product relation links.
2. **Product Catalog**
   - Read-only list for product-oriented operational review.
   - Searchable product list with manufacturer, unit, VAT, stock, barcode count, and attribute count columns.
3. **Manufacturers**
   - Create, update, and soft delete product manufacturer records.
4. **Product Units**
   - Create, update, and soft delete product unit definitions.
5. **Product Attributes**
   - Create, update, and soft delete product attribute records.
   - Optional product filter for focused attribute management.
6. **Product Variants**
   - Create, update, and soft delete product variant records.
   - Optional product filter for variant-specific editing.
7. **Product Barcodes**
   - Create, update, and soft delete barcode records linked to products.
   - Optional product filter and barcode mask relation support.
8. **Cashier Reference**
   - Read-only cashier list embedded in the module for office-side reference during product operations.

## Service Layer

Module logic is coordinated by `office/service/product_management_service.py`.

Service responsibilities:

- Validate product and related table CRUD inputs.
- Enforce uniqueness checks for product code, variant code, barcode, and unit code where required.
- Resolve store identifier fallback for new product ownership.
- Provide typed view models for product grids and related forms.
- Manage soft delete operations across product and product-related tables.

## Data Models Used

The module currently uses:

- `product`
- `product_manufacturer`
- `product_unit`
- `product_attribute`
- `product_variant`
- `product_barcode`
- `product_barcode_mask`
- `department_main_group`
- `department_sub_group`
- `vat`
- `warehouse`
- `store` (for store ownership fallback)
- `cashier` (reference listing tab)

## Notes and Current Limits

- Product module follows soft delete strategy for all managed tables.
- Product catalog tab is intentionally read-only in this phase.
- Advanced inventory workflows (warehouse movement, stock adjustment) remain out of this module scope and are planned for dedicated modules.

---

[Back to index](README.md) | [Previous: Cashier Management Module](14-cashier-management-module.md) | [Next: Campaign Management Module](16-campaign-management-module.md)
