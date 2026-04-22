# Cashier Management Module

This document describes the implemented cashier operations module in `SaleFlex.OFFICE`.

## Purpose

`CashierManagementForm` provides a spreadsheet-style operational workspace for cashier administration.
The module is launched from `ModuleLauncherForm` using the `Cashier Management` button.

## Implemented Tabs

The form is organized into three tabs:

1. **Cashier List**
   - Grid-based cashier listing.
   - New cashier creation.
   - Existing cashier update.
   - Soft delete for cashier records.
2. **Performance Targets**
   - Define cashier-level performance targets.
   - Maintain target period, amount, transaction count, achievement, status, and notes.
   - Soft delete for obsolete targets.
3. **Transaction Metrics**
   - Read-only list of cashier transaction metrics.
   - Optional cashier filter for focused analysis.
   - Row-level notes preview.

## Service Layer

Module logic is coordinated by `office/service/cashier_management_service.py`.

Service responsibilities:

- Validate cashier CRUD inputs.
- Enforce unique `cashier.no` and `cashier.user_name` among non-deleted rows.
- Resolve current store identifier for target records.
- Provide typed view models for form tables.
- Manage soft delete operations for cashier and performance target records.

## Data Models Used

The module currently uses:

- `cashier`
- `cashier_performance_target`
- `cashier_transaction_metrics`
- `store` (store resolution for target ownership)

## Notes and Current Limits

- Cashier passwords are still plain text in current baseline; hashing remains roadmap scope.
- Transaction metrics tab is intentionally read-only in this phase.
- Cashier performance targets are entered manually by office users.

---

[Back to index](README.md) | [Previous: Multi-POS Definition Data Model](13-multi-pos-definition-model.md) | [Next: Product Management Module](15-product-management-module.md)
