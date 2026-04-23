# Development Roadmap

This roadmap defines a practical path from project bootstrap to production-ready Office operations.

## Phase 1 - Foundation (MVP Core)

- [x] Project bootstrap and package structure
- [x] `settings.toml` parser and mode routing
- [x] Database initialization and base models (PyPOS-compatible model set copied to Office)
- [~] Authentication and session basics (keyboard-first login UI + cashier-table credential validation active)
- [~] Static UI shell (startup splash + login implemented, dashboard pending)
- [x] REST API skeleton with versioned routes (`/api/v1/health`, `/api/v1/pos/init`)

## Current Delivered Baseline (2026-04-23)

- Entry point and logger wiring (`saleflex.py`)
- Startup splash/about-style form with progress messages
- Startup preload service (`BootstrapDataLoader`) for initial required data
- Login form opened after preload completion
- Desktop/keyboard-first login UX baseline for Office users
- Data-layer baseline for Office + PyPOS compatibility:
  - 100+ definition models copied from `SaleFlex.PyPOS/data_layer/model/definition`
  - Original `Column`-based model style retained (`Model`, `CRUD`, mixins)
  - `PosTerminal` model added for multi-terminal store scope
  - Store/transaction/closure/pos settings models extended with terminal-scoped fields where needed
- REST API server (`api/server.py`) started as daemon thread on application startup:
  - `GET /api/v1/health` — liveness check
  - `GET /api/v1/pos/init?office_code=&store_code=&terminal_code=` — full init data for a POS terminal
- Identity fields renamed from `store_id`/`office_id` to `store_code`/`office_code` throughout
  (`settings.toml`, `Settings` class, `BootstrapContext`, all UI forms)

## Phase 2 - Operational Modules

- Product management static forms
- Campaign and loyalty definition static forms
- POS terminal registry and health monitor
- POS inbound data APIs (transactions/status/closures)
- Local backup persistence and audit logging

## Phase 3 - Integration and Sync

- [x] Outbox model (`SyncQueueItem`) with status tracking, retry counting, and reset methods
- [x] Inbox model (`GateNotification`) for inbound GATE notifications
- [x] `SyncManagementService` — queue listing, retry, delete, clear, and notification helpers
- [x] `SyncManagementForm` — four-tab UI: Pending Queue, Failed Items, Sent History, GATE Notifications
- [x] `SystemSettingsForm` — three-tab settings UI (General, POS Server, GATE Integration); writes to `settings.toml` and reloads `Settings` singleton
- [x] `settings.toml` extended: `[network]` (POS Server endpoint) and `[gate]` (GATE integration) sections exposed in `Settings` singleton
- [x] `Settings.reload()` classmethod added for in-process settings refresh
- [x] REST API server started at application boot (`api/server.py`, Flask daemon thread)
- [x] `GET /api/v1/pos/init` — validates terminal credentials and returns full init data set
- [ ] GATE connector with retryable sync flows (background SyncWorker)
- [ ] Conflict and idempotency handling in inbound API
- [ ] POST endpoints for PyPOS transaction and closure ingestion

## Phase 4 - Bulk Import and Reporting

- CSV/XML import wizard with validation
- Error reporting and import audit
- Dashboard analytics pages
- CSV and PDF export pipelines

## Phase 5 - Hardening

- Security hardening (tokens, policies, audit)
- Performance tuning for large datasets
- Deployment packaging for target OS profiles
- Backup/restore procedures and operational runbook

## MVP Definition

MVP should include:

1. Static Office UI with admin/manager access.
2. REST API for PyPOS bootstrap and event ingestion.
3. Local-first persistence for backup continuity.
4. Basic GATE sync in `gate` mode.
5. Starter reporting with dashboard + CSV/PDF export.

---

[Back to index](README.md) | [Previous: Project Structure](09-project-structure.md)
