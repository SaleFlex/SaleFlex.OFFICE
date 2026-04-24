# Definitions Management Module

This document describes the dedicated definitions management workflows implemented in `SaleFlex.OFFICE`.

## Purpose

`DefinitionsManagementForm` centralizes all core reference / master-data tables in one spreadsheet-style
tabbed workspace. It is opened from `ModuleLauncherForm` by the `Definitions Management` module button.

These tables drive address lookups, financial calculations, payment routing, and tax rules across the
entire SaleFlex ecosystem (`SaleFlex.OFFICE`, `SaleFlex.PyPOS`, `SaleFlex.GATE`).

## Implemented Tabs

The form is organized into nine tabs:

### 1. Countries
- Create, update, and hard-delete country records (`country` table).
- Fields: **Name**, **ISO Alpha-2** (required, 2-char, unique), **ISO Alpha-3** (optional),
  **ISO Numeric** (optional integer).
- Hard delete is blocked by the database engine when cities or regions reference the country.

### 2. Country Regions
- Create, update, and hard-delete sub-country region records (`country_region` table).
- Fields: **Country** (lookup combo), **ISO 3166-2** code, **Region Code** (required),
  **Name** (required), **Region Type** (e.g. state, province, free_zone),
  **Has Special Requirements** (checkbox), **Display Order**, **Description**.
- Filter combo restricts the grid to regions belonging to one country.
- Unique constraint: `(fk_country_id, region_code)` is enforced by the database.

### 3. Cities
- Create, update, and hard-delete city records (`city` table).
- Fields: **Name** (required), **Code** (required, unique), **Short Name**, **Numeric Code**,
  **Country** (lookup combo, required).
- Filter combo restricts the grid to cities of one country.

### 4. Districts
- Create, update, and hard-delete district records (`district` table).
- Fields: **Name** (required), **Code** (required, unique), **Short Name**, **Numeric Code**,
  **City** (lookup combo, required).
- Filter combo restricts the grid to districts of one city.

### 5. Currencies
- Create, update, and soft-delete (deactivate) currency records (`currency` table).
- Fields: **No** (required, unique integer), **Name** (required), **Currency Code** (ISO numeric),
  **Sign** (e.g. £, $, ₺), **Sign Direction** (LEFT / RIGHT combo), **Symbol** (text symbol),
  **Decimal Places** (0–4 spinner, default 2).
- Soft delete sets `is_deleted = true`; deactivated currencies are hidden from the grid.
- Currency combo-boxes in the Currency Rates tab are refreshed whenever a currency is added or updated.

### 6. Currency Rates
- Create, update, and soft-delete exchange rate records (`currency_table` table).
- Fields: **Base Currency** (lookup combo), **Target Currency** (lookup combo),
  **Rate** (4-decimal spinner: 1 base currency = rate target currency).
- Unique constraint `(fk_base_currency_id, fk_target_currency_id)` is enforced by the database.
- Soft delete sets `is_deleted = true`; deleted rates are hidden from the grid.

### 7. Payment Types
- Create, update, and soft-delete payment type records (`payment_type` table).
- Fields: **No** (required, unique integer), **Name** (required), **Description**, **Culture Info**
  (e.g. `en-GB`, default `en-GB`).
- Soft delete sets `is_deleted = true`; deactivated types are hidden from the grid.

### 8. VAT
- Create, update, and soft-delete VAT rate records (`vat` table).
- Fields: **No** (required integer), **Name** (required), **Rate** (% spinner, 2 decimal places),
  **Description**.
- Soft delete sets `is_deleted = true`; deactivated VAT rates are hidden from the grid.

### 9. Transaction Settings
A two-sub-tab panel containing transaction-related configuration tables.

#### 9a. Document Types
- Create, update, and hard-delete transaction document type records (`transaction_document_type` table).
- Fields: **No** (required integer, unique), **Name** (required), **Display Name** (optional),
  **Description** (optional).
- Document types classify the nature of a transaction document (e.g. `RECEIPT`, `INVOICE`, `REFUND`).

#### 9b. Discount Types
- Create, update, and hard-delete transaction discount type records (`transaction_discount_type` table).
- Fields: **Code** (required, unique, max 50 chars), **Name** (required), **Display Name** (optional),
  **Description** (optional).
- Discount types categorize discount reasons applied during a transaction (e.g. `LOYALTY`, `PROMO`, `MANUAL`).

## Service Layer

All database operations are handled by `DefinitionsManagementService`
(`office/service/definitions_management_service.py`).

The service exposes the following method groups:

| Entity | List | Add | Update | Delete |
|---|---|---|---|---|
| Country | `list_countries()` | `add_country()` | `update_country()` | `delete_country()` (hard) |
| Country Region | `list_country_regions(country_id?)` | `add_country_region()` | `update_country_region()` | `delete_country_region()` (hard) |
| City | `list_cities(country_id?)` | `add_city()` | `update_city()` | `delete_city()` (hard) |
| District | `list_districts(city_id?)` | `add_district()` | `update_district()` | `delete_district()` (hard) |
| Currency | `list_currencies()` | `add_currency()` | `update_currency()` | `soft_delete_currency()` |
| Currency Rate | `list_currency_rates()` | `add_currency_rate()` | `update_currency_rate()` | `soft_delete_currency_rate()` |
| Payment Type | `list_payment_types()` | `add_payment_type()` | `update_payment_type()` | `soft_delete_payment_type()` |
| VAT | `list_vats()` | `add_vat()` | `update_vat()` | `soft_delete_vat()` |
| Transaction Document Type | `list_transaction_document_types()` | `add_transaction_document_type()` | `update_transaction_document_type()` | `delete_transaction_document_type()` (hard) |
| Transaction Discount Type | `list_transaction_discount_types()` | `add_transaction_discount_type()` | `update_transaction_discount_type()` | `delete_transaction_discount_type()` (hard) |

Lookup helpers (`list_country_lookups()`, `list_city_lookups()`, `list_currency_lookups()`)
supply `id + label` pairs for combo-box population in the UI.

All methods return either a typed view dataclass list or a `ServiceResult(success, message)`.

## UI Layout

Each tab follows the same spreadsheet-style pattern used across other management modules:

```
┌──────────────────────────────────────────────┐
│  QSplitter (Qt.Vertical)                     │
│  ┌────────────────────────────────────────┐  │
│  │  Filter combo (where applicable)       │  │
│  │  QTableWidget  (read-only grid)        │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  QGroupBox – Detail form               │  │
│  │  QFormLayout with field widgets        │  │
│  │  [Add] [Update] [Delete/Deactivate]    │  │
│  │  ──────────────  [Clear] [Refresh]     │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

- Selecting a grid row populates the detail form.
- **Add** creates a new record; **Update** saves changes to the selected record;
  **Delete / Deactivate** removes or soft-deletes the selected record after a confirmation dialog.
- **Clear** resets the detail form and deselects the current record without changing the database.
- **Refresh** reloads the grid from the database.
- A status label at the bottom of the form shows success (green) or error (red) messages after each action.
- **Refresh All** (top-right toolbar) reloads all tabs simultaneously, including all filter combos.

## File Map

| File | Role |
|---|---|
| `office/service/definitions_management_service.py` | Service / data-access layer |
| `user_interface/form/definitions_management_form.py` | UI form with 9 tabs |
| `user_interface/form/module_launcher_form.py` | Entry point – `Definitions Management` button |
| `data_layer/model/definition/country.py` | `Country` ORM model |
| `data_layer/model/definition/country_region.py` | `CountryRegion` ORM model |
| `data_layer/model/definition/city.py` | `City` ORM model |
| `data_layer/model/definition/district.py` | `District` ORM model |
| `data_layer/model/definition/currency.py` | `Currency` ORM model |
| `data_layer/model/definition/currency_table.py` | `CurrencyTable` ORM model |
| `data_layer/model/definition/payment_type.py` | `PaymentType` ORM model |
| `data_layer/model/definition/vat.py` | `Vat` ORM model |
| `data_layer/model/definition/transaction_document_type.py` | `TransactionDocumentType` ORM model |
| `data_layer/model/definition/transaction_discount_type.py` | `TransactionDiscountType` ORM model |
