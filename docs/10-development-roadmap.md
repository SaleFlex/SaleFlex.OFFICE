# Development Roadmap

This roadmap defines a practical path from project bootstrap to production-ready Office operations.

## Phase 1 - Foundation (MVP Core)

- [x] Project bootstrap and package structure
- [x] `settings.toml` parser and mode routing
- [~] Database initialization and base models (PyPOS-compatible model set copied to Office)
- [~] Authentication and session basics (keyboard-first login UI + cashier-table credential validation active)
- [~] Static UI shell (startup splash + login implemented, dashboard pending)
- [ ] REST API skeleton with versioned routes

## Current Delivered Baseline (2026-04-21)

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

## Phase 2 - Operational Modules

- Product management static forms
- Campaign and loyalty definition static forms
- POS terminal registry and health monitor
- POS inbound data APIs (transactions/status/closures)
- Local backup persistence and audit logging

## Phase 3 - Integration and Sync

- GATE connector with retryable sync flows
- Outbox/inbox pattern implementation
- Conflict and idempotency handling
- Sync status monitoring screens

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
