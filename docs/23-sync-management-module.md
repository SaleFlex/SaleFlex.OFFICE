# Data Sync and Backup Module

This document describes the Data Sync and Backup management workflows implemented in `SaleFlex.OFFICE`.

## Purpose

The sync management module makes the outgoing integration queue (`SyncQueueItem`) and the
incoming GATE notification inbox (`GateNotification`) visible to operators. It gives admins
a practical way to monitor integration health and intervene when automatic retries are exhausted.

This module is the UI surface for the **offline outbox pattern** that sits at the heart of the
`SaleFlex.OFFICE` integration architecture (see [docs/06-data-sync-and-backup.md](06-data-sync-and-backup.md)).

## Outbox Pattern Background

Every integration event (transaction push, closure, warehouse movement, etc.) that must reach
an external system is written to the `sync_queue_item` table with `status = "pending"`.

Status flow:

```
pending  →  sent        (success path)
pending  →  failed      (all retries exhausted)
failed   →  pending     (operator manual reset)
```

Connector types:
- `gate`           → SaleFlex.GATE (transactions, closures, warehouse events)
- `gate_erp`       → ERP relay via GATE
- `gate_payment`   → Payment gateway relay via GATE
- `erp`            → Direct third-party ERP connector
- `payment`        → Direct third-party payment gateway

Event types:
- `transaction`        → completed sale document
- `closure`            → end-of-day closure
- `warehouse_movement` → stock movement record
- `erp_sync`           → generic ERP payload
- `payment`            → payment request / confirmation

## Implemented Tabs

### 1. Pending Queue

- Read-only grid showing all items with `status = "pending"`.
- Ordered oldest-first so operators can see how far back the backlog goes.
- Fields: **Connector**, **Event Type**, **Status**, **Retries**, **Max Retries**,
  **Created At**, **Updated At**, **Sent At**, **Error**.
- Refresh button reloads the grid from the database.

### 2. Failed Items

- Grid showing all items with `status = "failed"` (all retries exhausted).
- Selecting a row shows the stored **error details** in a read-only text panel below.
- **Reset Selected to Pending**: resets one selected item back to `pending`
  and clears its retry counter and error message.
- **Delete Selected**: permanently hard-deletes the selected failed item
  (confirmation dialog required).
- **Reset All Failed to Pending**: batch-resets every failed item at once
  (confirmation dialog required).

### 3. Sent History

- Read-only grid showing all items with `status = "sent"` ordered newest-first.
- **Delete Selected**: permanently hard-deletes the selected sent item.
- **Clear All Sent History**: permanently removes every `sent` record as a
  maintenance operation (confirmation dialog required).

### 4. GATE Notifications

- Grid showing inbound notifications received from `SaleFlex.GATE`.
- Unread notifications are highlighted in bold blue.
- Selecting a row shows the notification **body** in a read-only text panel below.
- **Mark Selected as Read**: marks one notification as read.
- **Mark All as Read**: marks every unread notification as read.

## Summary Banner

A summary line at the top of the form always shows:

```
Pending: <n>  |  Failed: <n>  |  Sent: <n>  |  Unread Notifications: <n>
```

All counts are refreshed after each action and after each individual tab refresh.

## Service Layer

All database operations are handled by `SyncManagementService`
(`office/service/sync_management_service.py`).

| Method | Purpose |
|---|---|
| `get_summary()` | Returns `SyncSummaryView` with aggregate counts. |
| `list_pending(connector_type?)` | Returns pending items oldest-first. |
| `list_failed(connector_type?)` | Returns failed items newest-first. |
| `list_sent(connector_type?)` | Returns sent items newest-first. |
| `reset_to_pending(item_id)` | Resets one failed item to pending. |
| `reset_all_failed(connector_type?)` | Batch-resets all failed items. |
| `delete_item(item_id)` | Hard-deletes one sync queue item. |
| `clear_sent_history()` | Hard-deletes all sent records. |
| `list_notifications(unread_only?)` | Returns GATE notifications. |
| `mark_notification_read(id)` | Marks one notification as read. |
| `mark_all_notifications_read()` | Marks all notifications as read. |

All methods return either a typed view dataclass list or a `ServiceResult(success, message)`.

## Model Layer

| Model | Table | Purpose |
|---|---|---|
| `SyncQueueItem` | `sync_queue_item` | Outbox record with payload, status, retry tracking |
| `GateNotification` | `gate_notification` | Inbound notification from GATE |

`SyncQueueItem` convenience methods:

| Method | Description |
|---|---|
| `create_pending(connector_type, event_type, payload)` | Create and persist a new pending item. |
| `get_pending(connector_type?)` | Return all pending items (implemented). |
| `get_by_status(status, connector_type?)` | Return all items with given status. |
| `mark_sent()` | Update status to `sent` and record `sent_at`. |
| `increment_retry(error_message?)` | Increment retry counter; mark `failed` when limit reached. |
| `reset_to_pending()` | Reset a failed item for retry. |

## UI Layout

Each tab follows the same spreadsheet-style pattern:

```
┌──────────────────────────────────────────────────────────┐
│  Toolbar: [Refresh]  [Action buttons...]                 │
│  Info label                                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  QTableWidget (read-only grid)                     │  │
│  └────────────────────────────────────────────────────┘  │
│  Detail panel (error text / notification body)           │
└──────────────────────────────────────────────────────────┘
```

- Selecting a grid row populates the detail panel below the grid.
- A status label at the bottom of the form shows success (green) or error (red)
  messages after each action.
- **Refresh All** (top-right toolbar) reloads all four tabs simultaneously.
- A summary banner in the header shows live counts for pending, failed, sent, and
  unread notifications.

## File Map

| File | Role |
|---|---|
| `office/service/sync_management_service.py` | Service / data-access layer |
| `user_interface/form/sync_management_form.py` | UI form with 4 tabs |
| `user_interface/form/module_launcher_form.py` | Entry point – `Data Sync and Backup` button |
| `data_layer/model/definition/sync_queue_item.py` | `SyncQueueItem` ORM model (outbox) |
| `data_layer/model/definition/gate_notification.py` | `GateNotification` ORM model (inbox) |

---

[Back to index](README.md) | [Previous: Definitions Management](22-definitions-management-module.md)
