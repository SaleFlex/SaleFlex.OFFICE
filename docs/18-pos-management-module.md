# POS Management Module

This document describes the implemented POS infrastructure management module in `SaleFlex.OFFICE`.

## Purpose

`PosManagementForm` provides an Excel-like operational workspace for POS infrastructure entities.
The module is launched from `ModuleLauncherForm` using the `POS Management` button.

## Implemented Tabs

The form is organized into three tabs:

1. **POS Terminals**
   - Grid-based POS terminal listing with search.
   - New terminal creation.
   - Existing terminal update.
   - Soft delete for terminal records.
2. **POS Settings**
   - Create, update, and soft delete POS settings records.
   - Terminal-based filtering support.
   - Backend endpoint and online-mode configuration fields.
3. **POS Virtual Keyboards**
   - Create, update, and soft delete virtual keyboard definitions.
   - Keyboard geometry, typography, and color configuration fields.
Dynamic form metadata workflows were moved under the dedicated `Form Management` module.

## Service Layer

Module logic is coordinated by `office/service/pos_management_service.py`.

Service responsibilities:

- Validate POS infrastructure CRUD inputs.
- Enforce uniqueness checks where required.
- Provide typed view models for POS grids.
- Manage soft delete operations.

## Data Models Used

The module currently uses:

- `pos_terminal`
- `pos_settings`
- `pos_virtual_keyboard`
- `store`

## Notes and Current Limits

- POS module workflows follow soft delete strategy.
- Form-related workflows are documented in `19-form-management-module.md`.

---

[Back to index](README.md) | [Previous: Customer Management Module](17-customer-management-module.md) | [Next: Form Management Module](19-form-management-module.md)
