# Integration Contracts

This document defines the required integration style across SaleFlex applications.

## Protocol Standard

All system-to-system communication is REST API + JSON:

- `SaleFlex.PyPOS` <-> `SaleFlex.OFFICE`
- `SaleFlex.PyPOS` <-> `SaleFlex.GATE`
- `SaleFlex.OFFICE` <-> `SaleFlex.GATE`

## Integration Responsibilities

### PyPOS -> Office

- Pull required operational definitions:
  - products
  - prices
  - campaigns
  - loyalty rules
  - cashier/user authorization scope
- Push operational data:
  - transactions
  - payments
  - status/heartbeat
  - closure summaries (or closure events)

#### Office-Owned Definition Strategy (Implemented Baseline)

`SaleFlex.OFFICE` keeps dedicated definition tables (product, payment type, campaign, loyalty, etc.)
and acts as source of truth for connected terminals.

Managers create definitions directly in Office. PyPOS terminals then pull this data via REST.

### Office -> GATE

- Push consolidated local store data upstream.
- Pull central updates and policy changes.
- Keep sync status and retry queues for outages.

### PyPOS -> GATE (direct mode)

When PyPOS mode is `gate`, terminal communicates directly with GATE REST APIs.

## Initial Endpoint Groups (Proposed)

### Office APIs for PyPOS clients

- `GET /api/v1/bootstrap`
- `GET /api/v1/products`
- `GET /api/v1/campaigns`
- `GET /api/v1/loyalty/policies`
- `GET /api/v1/bootstrap/topics`
- `GET /api/v1/bootstrap/{topic_name}`
- `POST /api/v1/transactions`
- `POST /api/v1/terminal-status`
- `POST /api/v1/closures`

### Office APIs for GATE sync

- `POST /api/v1/sync/outbox/push`
- `POST /api/v1/sync/inbox/pull`
- `GET /api/v1/sync/state`

## Contract Requirements

- Versioned path prefix (`/api/v1`)
- Auth required for every endpoint except health checks
- Correlation IDs for traceability
- Idempotency keys for critical write endpoints
- Timestamp fields in UTC
- Explicit schema version field in payloads

## Error Contract

Suggested error response shape:

```json
{
  "success": false,
  "error_code": "VALIDATION_ERROR",
  "message": "store_id is required",
  "details": {},
  "correlation_id": "c7f8f8e9-..."
}
```

---

[Back to index](README.md) | [Previous: Auth and Roles](04-auth-and-roles.md) | [Next: Data Sync and Backup](06-data-sync-and-backup.md)
