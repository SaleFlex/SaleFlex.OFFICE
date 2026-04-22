# Campaign Management Module

This document describes the implemented campaign operations module in `SaleFlex.OFFICE`.

## Purpose

`CampaignManagementForm` provides an Excel-like operational workspace for campaign lifecycle management and all campaign-related definition tables.
The module is launched from `ModuleLauncherForm` using the `Campaign Management` button.

## Implemented Tabs

The form is organized into six tabs:

1. **Campaigns**
   - Grid-based campaign listing with quick search.
   - New campaign creation.
   - Existing campaign update.
   - Soft delete for campaign records.
   - Campaign master fields for discount model, validity window, priority, targeting, and usage limits.
2. **Campaign Types**
   - Create, update, and soft delete campaign type definitions.
3. **Campaign Rules**
   - Create, update, and soft delete campaign rule records.
   - Rules can be scoped by product, department, payment type, and manufacturer.
4. **Campaign Products**
   - Create, update, and soft delete product links for campaigns.
   - Supports gift product flag, quantity limits, and product-level discount override fields.
5. **Campaign Usage**
   - Create, update, and soft delete campaign usage records.
   - Includes campaign, customer, cashier, store, transaction, discount amount, and usage timestamp fields.
6. **Campaign Operations**
   - Read-only operations dashboard with campaign-level usage totals.
   - Displays usage count, total discount amount, and last usage timestamp.

## Additional Operations Form

An additional dedicated form, `CampaignOperationsForm`, is available from the campaign module.

It provides:

- focused campaign operations listing in a separate window,
- optional campaign-level filter,
- read-only monitoring view for operations staff.

## Service Layer

Module logic is coordinated by `office/service/campaign_management_service.py`.

Service responsibilities:

- Validate campaign and campaign-related table CRUD inputs.
- Enforce uniqueness checks for campaign code and campaign type code.
- Enforce campaign-product duplicate protection for the same campaign-product pair.
- Resolve default store fallback for campaign and campaign usage records.
- Provide typed view models for campaign grids and operations views.
- Manage soft delete operations across campaign and campaign-related tables.

## Data Models Used

The module currently uses:

- `campaign`
- `campaign_type`
- `campaign_rule`
- `campaign_product`
- `campaign_usage`
- `product`
- `department_main_group`
- `payment_type`
- `product_manufacturer`
- `customer`
- `customer_segment`
- `cashier`
- `store`
- `transaction_head`

## Notes and Current Limits

- Campaign module follows soft delete strategy for all managed tables.
- Campaign operations tab and operations window are intentionally read-only in this phase.
- Date and time fields in the form are currently entered with fixed text formats (`YYYY-MM-DD HH:MM` and `HH:MM`).

---

[Back to index](README.md) | [Previous: Product Management Module](15-product-management-module.md)
