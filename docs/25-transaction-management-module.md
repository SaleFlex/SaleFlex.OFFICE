# Transaction Management Module

This document describes the read-only Transaction Management module implemented in `SaleFlex.OFFICE`.

## Purpose

`TransactionManagementForm` provides office operators and managers with a full, read-only view of all
POS transaction data that has been recorded in the local database. Transactions originate from
`SaleFlex.PyPOS` terminals and are stored in `transaction_head` (and related detail tables) once
a sale or operation is completed.

The module is **strictly read-only** – no add, edit, or delete operations are possible. This ensures
the integrity of the audit trail while giving back-office users visibility into every transaction
across all POS terminals.

The module is accessed from `ModuleLauncherForm` via the **Transaction Management** button.

## Layout

The form uses a top-level `QTabWidget` organized by POS terminal:

```
┌──────────────────────────────────────────────────────────┐
│  All POS  │  POS 1  │  POS 2  │  …                       │
├──────────────────────────────────────────────────────────┤
│  QSplitter (Qt.Vertical)                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Transaction Header Grid (read-only)             │    │
│  │  Columns: Receipt No, Closure No, Date/Time,     │    │
│  │  POS, Document Type, Tx Type, Status, Total,     │    │
│  │  VAT, Discount, Payment, Change, Currency,       │    │
│  │  Order Source, Cancelled                         │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Detail Tabs (populated on row selection)        │    │
│  │  ┌────────────┬────────────┬────────────┐        │    │
│  │  │  Products  │  Payments  │  Discounts │        │    │
│  │  └────────────┴────────────┴────────────┘        │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Top-Level Tabs

| Tab | Content |
|---|---|
| **All POS** | All `transaction_head` rows across every terminal, ordered most-recent first |
| **POS {n}** | Filtered to a single `pos_id` value; one tab per distinct `pos_id` found in the database |

Tab labels include the terminal name when a matching `pos_terminal` record exists
(e.g. `Checkout Till (POS 1)`).

### Transaction Header Grid (upper panel)

Columns displayed for each `transaction_head` row:

| Column | Source field |
|---|---|
| Receipt No | `receipt_number` |
| Closure No | `closure_number` |
| Date / Time | `transaction_date_time` |
| POS | `pos_id` |
| Document Type | `document_type` |
| Tx Type | `transaction_type` |
| Status | `transaction_status` (color-coded: green = completed, red = cancelled/refunded) |
| Total | `total_amount` |
| VAT | `total_vat_amount` |
| Discount | `total_discount_amount` |
| Payment | `total_payment_amount` |
| Change | `total_change_amount` |
| Currency | `base_currency` |
| Order Source | `order_source` |
| Cancelled | `is_cancel` (Yes/No) |

### Detail Sub-Tabs (lower panel)

Populated when a transaction row is selected in the upper panel.

#### Products (`transaction_product`)

| Column | Source field |
|---|---|
| Line | `line_no` |
| Code | `product_code` |
| Product Name | `product_name` |
| Qty | `quantity` |
| Unit Price | `unit_price` |
| Discount | `unit_discount` |
| Total | `total_price` |
| VAT | `total_vat` |
| VAT % | `vat_rate` |
| UOM | `unit_of_measure` |
| Voided | `is_voided` (Yes/No) |

#### Payments (`transaction_payment`)

| Column | Source field |
|---|---|
| Line | `line_no` |
| Payment Type | `payment_type` |
| Amount | `payment_total` |
| Currency | `currency_code` |
| Curr. Total | `currency_total` |
| Status | `payment_status` (color-coded: green = approved, red = declined/failed) |
| Provider | `payment_provider` |
| Card Type | `card_type` |
| Card (masked) | `card_number_masked` |
| Auth Code | `authorization_code` |

#### Discounts (`transaction_discount`)

| Column | Source field |
|---|---|
| Line | `line_no` |
| Discount Type | `transaction_discount_type.name` (joined) |
| Amount | `discount_amount` |
| Rate (%) | `discount_rate` |
| Code | `discount_code` |

## Read-Only Guarantee

- All `QTableWidget` instances set `QAbstractItemView.NoEditTriggers`.
- No `QPushButton` widgets for Add, Update, or Delete are rendered.
- The service layer (`TransactionManagementService`) only provides `SELECT` queries via
  SQLAlchemy; no write methods exist.

## How Transactions Reach OFFICE

OFFICE **receives** completed transaction data pushed by `SaleFlex.PyPOS` terminals via the
REST API.  No polling or manual import is required.

### Push Flow (PyPOS → OFFICE)

1. When a cashier closes a document (sale / cancellation / return) the `DocumentManager`
   immediately enqueues the transaction and spawns a background daemon thread.
2. The daemon calls `OfficePushService.flush_pending()`, which serialises all pending
   transactions into a single HTTP `POST /api/v1/pos/transactions` request.
3. The request body includes the full transaction tree (head + all line items) **plus** the
   current sequence counter values (`ReceiptNumber`, `ClosureNumber`, …).
4. OFFICE validates the terminal identity, persists the records, and updates the
   per-terminal `TransactionSequence` rows.
5. If OFFICE is unreachable the queue item is marked `failed` and a background
   `OfficePushWorker` QThread retries every hour (configurable via
   `[office].sync_interval_minutes` in `settings.toml`).

### REST Endpoints (OFFICE side)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/pos/transactions` | Accept and persist a batch of completed transactions |
| `POST` | `/api/v1/pos/sequences` | Update per-POS sequence counter values |

### Multi-POS Support

OFFICE manages multiple POS terminals simultaneously.  Each terminal is identified by its
`terminal_code` and `pos_id` (integer `pos_no_in_store`).  The `transaction_sequence` table
stores one row per `(name, pos_id)` pair so counters from different terminals never collide.

The Transaction Management view organises transactions into per-POS tabs:

- **All POS** – every `transaction_head` row across all terminals.
- **POS {n}** – one tab per distinct `pos_id`, labelled with the terminal name when available.

## Temporary Transaction Tables

OFFICE does **not** include any `*_temp` transaction ORM models
(`transaction_head_temp`, `transaction_product_temp`, etc.).  Those tables are
used exclusively by `SaleFlex.PyPOS` to hold an in-progress sale while the
cashier is building it.  By the time a transaction is visible in OFFICE it has
been committed and stored in the permanent tables, so the draft tables serve no
purpose here and have been deliberately excluded from the data layer.

## Service Layer

`TransactionManagementService` (`office/service/transaction_management_service.py`) provides:

| Method | Description |
|---|---|
| `list_pos_terminals()` | All registered `pos_terminal` records, ordered by `terminal_code` |
| `list_distinct_pos_ids()` | Distinct `pos_id` integer values present in `transaction_head` |
| `list_transactions(pos_id?)` | `transaction_head` rows, most-recent first; optionally filtered by `pos_id` |
| `list_transaction_products(tx_id)` | `transaction_product` rows for the given `transaction_head.id` |
| `list_transaction_payments(tx_id)` | `transaction_payment` rows for the given `transaction_head.id` |
| `list_transaction_discounts(tx_id)` | `transaction_discount` rows joined to `transaction_discount_type` |

All return typed frozen dataclasses; no raw ORM objects leave the service boundary.

## Grid Features

- **Sortable columns**: all grids have `setSortingEnabled(True)`.
- **Alternating row colors**: `setAlternatingRowColors(True)`.
- **Auto-fit**: `resizeColumnsToContents()` called after each data load.
- **Right-aligned numerics**: monetary and quantity values use `Qt.AlignRight | Qt.AlignVCenter`.
- **Color-coded status**: transaction status and payment status cells use `setForeground()` to
  distinguish completed/approved (dark green) from cancelled/failed (dark red).

## File Map

| File | Role |
|---|---|
| `office/service/transaction_management_service.py` | Read-only service / data-access layer |
| `user_interface/form/transaction_management_form.py` | UI form with POS tabs and detail sub-tabs |
| `user_interface/form/module_launcher_form.py` | Entry point – `Transaction Management` button |
| `data_layer/model/definition/transaction_head.py` | `TransactionHead` ORM model |
| `data_layer/model/definition/transaction_product.py` | `TransactionProduct` ORM model |
| `data_layer/model/definition/transaction_payment.py` | `TransactionPayment` ORM model |
| `data_layer/model/definition/transaction_discount.py` | `TransactionDiscount` ORM model |
| `data_layer/model/definition/transaction_discount_type.py` | `TransactionDiscountType` ORM model |
| `data_layer/model/definition/pos_terminal.py` | `PosTerminal` ORM model (for tab labels) |
