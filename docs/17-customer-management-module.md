# Customer Management Module

This document describes the implemented customer operations module in `SaleFlex.OFFICE`.

## Purpose

`CustomerManagementForm` provides an Excel-like operational workspace for customer lifecycle management and all customer-related definition/operation tables.
The module is launched from `ModuleLauncherForm` using the `Customer Management` button.

## Implemented Tabs

The form is organized into six tabs:

1. **Customers**
   - Grid-based customer listing with search.
   - New customer creation.
   - Existing customer update.
   - Soft delete for customer records.
   - Customer contact, consent, profile, and address fields.
2. **Customer Segments**
   - Create, update, and soft delete customer segment definitions.
   - Segment metadata includes type, criteria JSON, display order, and visual fields.
3. **Segment Members**
   - Create, update, and soft delete customer-segment membership records.
   - Supports assignment date, assignment source, assignment reason, and active flag.
4. **Customer Loyalty**
   - Create, update, and soft delete customer loyalty records.
   - Supports loyalty program, tier, card number, points balances, purchase metrics, and participation dates.
5. **Loyalty Point Transactions**
   - Create, update, and soft delete loyalty point transaction records.
   - Includes customer loyalty linkage, transaction type, point amount, balance-after value, and reference fields.
6. **Customer Operations**
   - Read-only customer operations dashboard.
   - Displays segment counts, loyalty profile snapshot, available/lifetime points, and last loyalty transaction timestamp.

## Additional Operations Form

Additional dedicated forms are available from the customer module.

It provides:

- focused customer operations listing in a separate window,
- segment and status filters for operations staff,
- read-only monitoring view for customer and loyalty flow.

In addition, customer module now opens:

- `LoyaltyManagementForm` for loyalty definition and customer loyalty table management,
- `LoyaltyOperationsForm` for read-only loyalty usage and balance operations monitoring.

## Service Layer

Module logic is coordinated by `office/service/customer_management_service.py`.

Service responsibilities:

- Validate customer and customer-related table CRUD inputs.
- Enforce uniqueness checks for segment code, normalized phone, and loyalty card number.
- Enforce segment membership duplicate protection for the same customer-segment pair.
- Provide typed view models for customer, segment, loyalty, and operations grids.
- Manage soft delete operations across customer and customer-related tables.

## Data Models Used

The module currently uses:

- `customer`
- `customer_segment`
- `customer_segment_member`
- `customer_loyalty`
- `loyalty_point_transaction`
- `loyalty_program`
- `loyalty_tier`
- `cashier`
- `store`
- `transaction_head`

Loyalty-focused forms launched from customer module additionally use:

- `loyalty_earn_rule`
- `loyalty_program_policy`
- `loyalty_redemption_policy`

## Notes and Current Limits

- Customer module follows soft delete strategy for all managed tables.
- Customer operations tab and operations window are intentionally read-only in this phase.
- Date and time fields in form inputs are currently entered as fixed text formats (`YYYY-MM-DD` and `YYYY-MM-DD HH:MM`).

---

[Back to index](README.md) | [Previous: Campaign Management Module](16-campaign-management-module.md) | [Next: Loyalty Management Module](20-loyalty-management-module.md)
