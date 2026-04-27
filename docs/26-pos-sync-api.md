# POS Synchronisation API

This document describes the REST endpoints that `SaleFlex.OFFICE` exposes for **inbound**
data pushed by `SaleFlex.PyPOS` terminals.

---

## Overview

OFFICE acts as a central hub for one or more POS terminals.  When a PyPOS terminal
completes a transaction or end-of-day closure it serialises the full record tree and sends
it to OFFICE via HTTP.  OFFICE validates the terminal identity, persists the records, and
updates the per-POS sequence counters—all without any manual operator intervention.

---

## Endpoints

### `GET /api/v1/health`

Simple liveness check.  Returns `{"status": "ok"}`.  Used by PyPOS at startup and
before every push to confirm OFFICE is reachable.

---

### `GET /api/v1/pos/init`

Returns the full seed/reference data set required by a PyPOS terminal on first boot
(products, payment types, forms, sequences, …).

**Query parameters** (all required):

| Parameter | Description |
|-----------|-------------|
| `office_code` | OFFICE instance code (matches `[app].office_code` in OFFICE `settings.toml`) |
| `store_code` | Store this terminal belongs to |
| `terminal_code` | Terminal's unique code within the store |

#### Sequence counter resolution

The `transaction_sequences` list in the response is resolved per terminal using the
following priority order:

| Priority | Condition | Result |
|----------|-----------|--------|
| **1** | Rows in `transaction_sequence` with `terminal_code` matching this terminal | Terminal's last known counter values – POS **continues from where it left off** |
| **2** | Rows with `pos_id` matching the terminal's `pos_no_in_store` | Existing terminal rows where `terminal_code` was not populated |
| **3** | Rows with `pos_id IS NULL` (shared / store-wide defaults) | Factory defaults (e.g. `ReceiptNumber=1`) – used for a **brand-new terminal** |
| **4** | All active rows (legacy fallback) | Databases created before multi-POS support was introduced |

This means a POS terminal that was previously in use and has been **reinstalled**
(database wiped) will automatically resume from the correct `ReceiptNumber` and
`ClosureNumber` values stored in OFFICE rather than restarting from 1.

---

### `POST /api/v1/pos/transactions`

Accept and persist a **batch** of completed transaction records pushed by a PyPOS terminal.
Also updates per-POS sequence counters when the `sequences` array is provided.

**Request body** (JSON):

```json
{
  "office_code":   "OFFICE-001",
  "store_code":    "STORE-001",
  "terminal_code": "POS-01",
  "pos_id":        1,
  "transactions": [
    {
      "head": {
        "id": "<uuid>",
        "transaction_unique_id": "20260424-0001-000042",
        "pos_id": 1,
        "transaction_date_time": "2026-04-24T10:15:30",
        "document_type": "FISCAL_RECEIPT",
        "transaction_type": "SALE",
        "transaction_status": "COMPLETED",
        "receipt_number": 42,
        "closure_number": 1,
        "total_amount": "123.45",
        ...
      },
      "products":       [ { ... TransactionProduct fields ... } ],
      "payments":       [ { ... TransactionPayment fields ... } ],
      "discounts":      [ { ... } ],
      "departments":    [ { ... } ],
      "taxes":          [ { ... } ],
      "tips":           [ { ... } ],
      "surcharges":     [ { ... } ],
      "notes":          [ { ... } ],
      "loyalty":        [ { ... } ],
      "refunds":        [ { ... } ],
      "changes":        [ { ... } ],
      "deliveries":     [ { ... } ],
      "kitchen_orders": [ { ... } ],
      "fiscal":         { ... } or null
    }
  ],
  "sequences": [
    { "name": "ReceiptNumber", "value": 42 },
    { "name": "ClosureNumber", "value":  1 }
  ]
}
```

**Response** (success):

```json
{ "status": "ok", "accepted": 1, "rejected": 0 }
```

**Response** (error):

```json
{ "status": "error", "message": "Terminal 'POS-01' is not registered in store 'STORE-001'" }
```

**Deduplication**: transactions with a `transaction_unique_id` already present in the OFFICE
database are silently skipped (counted as `accepted`).

---

### `POST /api/v1/pos/closures`

Accept and persist completed end-of-day closure records pushed by a PyPOS terminal.
Also updates per-POS sequence counters when the `sequences` array is provided.

**Request body** (JSON):

```json
{
  "office_code":   "OFFICE-001",
  "store_code":    "STORE-001",
  "terminal_code": "POS-01",
  "pos_id":        1,
  "closures": [
    {
      "closure":                 { "...": "Closure fields" },
      "vat_summaries":           [ { "...": "ClosureVATSummary fields" } ],
      "tip_summaries":           [ { "...": "ClosureTipSummary fields" } ],
      "discount_summaries":      [ { "...": "ClosureDiscountSummary fields" } ],
      "payment_type_summaries":  [ { "...": "ClosurePaymentTypeSummary fields" } ],
      "document_type_summaries": [ { "...": "ClosureDocumentTypeSummary fields" } ],
      "department_summaries":    [ { "...": "ClosureDepartmentSummary fields" } ],
      "currency_summaries":      [ { "...": "ClosureCurrency fields" } ],
      "cashier_summaries":       [ { "...": "ClosureCashierSummary fields" } ],
      "country_specific":        { "...": "ClosureCountrySpecific fields" } or null
    }
  ],
  "sequences": [
    { "name": "ReceiptNumber", "value": 1 },
    { "name": "ClosureNumber", "value":  4 }
  ]
}
```

**Response**:

```json
{ "status": "ok", "accepted": 1, "rejected": 0 }
```

**Deduplication**: closures with a `closure_unique_id` already present in the OFFICE
database are silently skipped (counted as `accepted`).

---

### `POST /api/v1/pos/sequences`

Update sequence counter values for a specific POS terminal.  Typically included inside
the `/api/v1/pos/transactions` and `/api/v1/pos/closures` request bodies, but can also
be called independently.

**Request body** (JSON):

```json
{
  "office_code":   "OFFICE-001",
  "store_code":    "STORE-001",
  "terminal_code": "POS-01",
  "pos_id":        1,
  "sequences": [
    { "name": "ReceiptNumber", "value": 42 },
    { "name": "ClosureNumber", "value":  1 }
  ]
}
```

**Response**:

```json
{ "status": "ok", "updated": 2 }
```

---

## Per-POS Sequence Tracking

The `transaction_sequence` table in OFFICE stores one row per `(name, pos_id)` pair:

| Column | Description |
|--------|-------------|
| `name` | Counter name, e.g. `ReceiptNumber`, `ClosureNumber` |
| `value` | Current counter value received from PyPOS |
| `pos_id` | Integer POS terminal number (`pos_no_in_store`) |
| `terminal_code` | Human-readable terminal code |
| `last_synced_at` | Timestamp of the most recent push from PyPOS |

Rows with `pos_id IS NULL` are treated as shared/store-wide defaults (legacy behaviour
from databases created before multi-POS support was introduced).

---

## Multi-POS Architecture

OFFICE is designed to manage **multiple POS terminals simultaneously**.  Each terminal
registers with its own `terminal_code` and `pos_id`.  Incoming transactions and closures
are tagged through their POS/store context so OFFICE can report per terminal.

```
                          SaleFlex.OFFICE
                         ┌──────────────────────────────────┐
  POS-01 ── POST /tx,/closure ──→ │  POST /api/v1/pos/transactions │
  POS-02 ── POST /tx,/closure ──→ │  POST /api/v1/pos/closures     │
  POS-03 ── POST /tx,/closure ──→ │  validates and persists data   │
                         │                                  │
                         │  transaction_head (pos_id tagged)│
                         │  transaction_sequence (per POS)  │
                         └──────────────────────────────────┘
```

---

## Post-Closure Master-Data Refresh

After every **successful** `POST /api/v1/pos/closures` response, the requesting PyPOS
terminal automatically calls `GET /api/v1/pos/init` to pull a fresh copy of all
master-data and upsert it into its local SQLite database.

This means that **changes made in OFFICE** — products, prices, cashiers, campaigns,
loyalty rules, sequences, etc. — are propagated to POS terminals at the start of each
new sales period without requiring a manual restart or re-bootstrap:

```
PyPOS (closure pushed successfully)
  └─ GET /api/v1/pos/init          → returns latest OFFICE master-data
       └─ reseed_from_office_data()  → INSERT OR REPLACE on all local tables
            └─ caches rebuilt       → pos_data, product_data, ActiveCampaignCache
```

OFFICE does not need to implement any additional endpoint for this behaviour — it reuses
the existing `/api/v1/pos/init` endpoint, which already returns terminal-specific sequence
counters via the priority-order resolution described above.

---

## Authentication & Security

Currently OFFICE validates every request against the registered `PosTerminal` table
(matching `office_code`, `store_code`, and `terminal_code`).  Terminals not registered
in OFFICE receive a `404` response.

> **Future enhancement**: API-key header authentication is planned for production deployments.

---

## File Map

| File | Role |
|------|------|
| `api/server.py` | Flask routes; `_upsert_transaction_batch()`, `_upsert_closure_batch()`, `_upsert_sequences()` |
| `data_layer/model/definition/transaction_sequence.py` | Per-POS `TransactionSequence` model |
| `data_layer/model/definition/pos_terminal.py` | Terminal registration/validation |
| `data_layer/db_manager.py` | Schema migrations for `transaction_sequence` new columns |
