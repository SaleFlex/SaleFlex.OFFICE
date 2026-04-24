# POS Synchronisation API

This document describes the REST endpoints that `SaleFlex.OFFICE` exposes for **inbound**
data pushed by `SaleFlex.PyPOS` terminals.

---

## Overview

OFFICE acts as a central hub for one or more POS terminals.  When a PyPOS terminal
completes a transaction it serialises the full document tree and sends it to OFFICE via
HTTP.  OFFICE validates the terminal identity, persists the records, and updates the
per-POS sequence counters—all without any manual operator intervention.

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
| **2** | Rows with `pos_id IS NULL` (shared / store-wide defaults) | Factory defaults (e.g. `ReceiptNumber=1`) – used for a **brand-new terminal** |
| **3** | All active rows (legacy fallback) | Databases created before multi-POS support was introduced |

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

### `POST /api/v1/pos/sequences`

Update sequence counter values for a specific POS terminal.  Typically included inside
the `/api/v1/pos/transactions` request body, but can also be called independently.

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
registers with its own `terminal_code` and `pos_id`.  Incoming transactions are tagged with
`pos_id` in the `transaction_head` table, allowing the Transaction Management view to
display per-terminal tabs.

```
                          SaleFlex.OFFICE
                         ┌──────────────────────────────────┐
  POS-01 ── POST /tx ──→ │  POST /api/v1/pos/transactions   │
  POS-02 ── POST /tx ──→ │  validates terminal, persists    │
  POS-03 ── POST /tx ──→ │  transactions, updates sequences │
                         │                                  │
                         │  transaction_head (pos_id tagged)│
                         │  transaction_sequence (per POS)  │
                         └──────────────────────────────────┘
```

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
| `api/server.py` | Flask routes; `_upsert_transaction_batch()`, `_upsert_sequences()` |
| `data_layer/model/definition/transaction_sequence.py` | Per-POS `TransactionSequence` model |
| `data_layer/model/definition/pos_terminal.py` | Terminal registration/validation |
| `data_layer/db_manager.py` | Schema migrations for `transaction_sequence` new columns |
