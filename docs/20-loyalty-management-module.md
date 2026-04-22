# Loyalty Management Module

This document describes the dedicated loyalty management workflows added under the `Customer Management` module in `SaleFlex.OFFICE`.

## Purpose

`LoyaltyManagementForm` centralizes loyalty definition tables and customer loyalty operation tables in one module-level workspace.
It is opened from `CustomerManagementForm` by the `Open Loyalty Management` action.

## Implemented Tabs

The form is organized into eight tabs:

1. **Loyalty Programs**
   - Create, update, and soft delete loyalty program definitions.
   - Manage earning ratio, redemption ratio, expiry settings, bonus points, and terms/settings JSON.
2. **Loyalty Tiers**
   - Create, update, and soft delete tier definitions linked to loyalty programs.
   - Manage tier levels, multiplier, discount percentage, and display metadata.
3. **Loyalty Earn Rules**
   - Create, update, and soft delete earn-rule definitions.
   - Supports rule code, type, priority, and config JSON.
4. **Program Policies**
   - Create, update, and soft delete one policy row per loyalty program.
   - Includes customer identifier type, enrollment phone requirement, void behavior, and integration settings.
5. **Redemption Policies**
   - Create, update, and soft delete redemption policy rows per loyalty program.
   - Supports basket share cap, minimum redeem points, redemption step, and partial redemption flag.
6. **Customer Loyalty**
   - Create, update, and soft delete customer loyalty profile rows.
   - Covers card number, points balances, tier assignment, enrollment/activity timestamps, and spending metrics.
7. **Point Transactions**
   - Create, update, and soft delete loyalty point movement rows.
   - Covers transaction type, points delta, balance-after, linked cashier/store/transaction references.
8. **Loyalty Operations**
   - Read-only loyalty usage listing inside the module.
   - Filters by loyalty program, customer, and active status.

## Additional Operations Form

`LoyaltyOperationsForm` is also available as a standalone read-only window.
It can be opened:

- from `CustomerManagementForm` via `Open Loyalty Operations`,
- from `LoyaltyManagementForm` via `Open Loyalty Operations Window`.

The window provides:

- customer/program/tier based loyalty status listing,
- transaction count and earned/redeemed point totals,
- latest transaction timestamp and current balance visibility for operations teams.

## Service Layer

Loyalty definition workflows are coordinated by `office/service/loyalty_management_service.py`.

Service responsibilities:

- Typed view model generation for loyalty definition and operations tabs.
- CRUD validation and uniqueness checks for loyalty programs, tiers, rules, and policy tables.
- Soft delete lifecycle handling for all loyalty definition tables.
- Loyalty operations aggregation (program/customer filters, points and transaction summary fields).

## Data Models Used

The module currently uses:

- `loyalty_program`
- `loyalty_tier`
- `loyalty_earn_rule`
- `loyalty_program_policy`
- `loyalty_redemption_policy`
- `customer_loyalty`
- `loyalty_point_transaction`
- `customer`
- `store`
- `cashier`
- `transaction_head`

## Notes

- Date and datetime fields are entered as text (`YYYY-MM-DD` and `YYYY-MM-DD HH:MM`).
- All delete operations in this module use soft delete strategy.

---

[Back to index](README.md) | [Previous: Form Management Module](19-form-management-module.md) | [Next: Warehouse Management Module](21-warehouse-management-module.md)
