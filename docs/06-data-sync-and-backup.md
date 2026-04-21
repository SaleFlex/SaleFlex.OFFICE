# Data Sync and Backup

`SaleFlex.OFFICE` is a local operational backup node for store continuity.

## Core Principle

Because `SaleFlex.PyPOS` terminals continuously send operational data to Office, the Office database
naturally becomes a near-real-time backup source.

This means:

- internet outage does not stop local store visibility,
- historical operational records remain available in store LAN,
- data can be synchronized to GATE once connectivity is restored.

## Sync Directions

1. **POS -> Office (continuous)**
   - transactions, status, closure-related records
2. **Office -> GATE (periodic/retry)**
   - aggregated and queued data push
3. **GATE -> Office (periodic)**
   - updated catalog/policy definitions

## Outbox Pattern (Recommended)

For each external push operation:

1. write payload to local outbox table with `pending` state,
2. attempt delivery,
3. mark as `sent` on success,
4. keep retry metadata on failures,
5. move to `failed` after maximum retry threshold.

## Conflict and Consistency Guidelines

- Use immutable transaction identifiers from source system.
- Enforce idempotency on import/write endpoints.
- Use server-side `updated_at` + version fields for updates.
- Keep full audit trail for replay and diagnostics.

## Recovery Scenarios

- **Internet down**: POS and Office continue over local network.
- **POS device fails**: Office still has stored operations and can support analysis/export.
- **GATE unavailable**: Office keeps queueing and retries later.

## Backup Strategy

- Regular database snapshots on Office node
- Optional encrypted export archive for disaster recovery
- Retention policy by compliance needs (store/company policy)

---

[Back to index](README.md) | [Previous: Integration Contracts](05-integration-contracts.md) | [Next: Bulk Import](07-bulk-import.md)
