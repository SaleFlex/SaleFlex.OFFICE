# Architecture

This document defines the initial architecture of `SaleFlex.OFFICE`.

## High-Level View

```text
+---------------------+          REST/JSON          +---------------------+
|   SaleFlex.PyPOS    | <-------------------------> |   SaleFlex.OFFICE   |
+---------------------+                             +---------------------+
          ^                                                  |
          |                     REST/JSON                    |
          +--------------------------------------------------v
                                            +---------------------+
                                            |    SaleFlex.GATE    |
                                            +---------------------+
```

## Layers

1. **UI Layer (PySide6 static forms)**
   - Manager/admin-oriented screens
   - No dynamic form interpreter
2. **Application Layer**
   - Workflow controllers, validation, permission checks
3. **Service Layer**
   - Business logic for configuration, sync, reporting, import
4. **API Layer**
   - REST endpoints for PyPOS and GATE communication
5. **Data Layer**
   - SQLAlchemy models and repositories
6. **Sync Layer**
   - Outbox/inbox jobs, retries, conflict handling

## Static Form Philosophy

Unlike `SaleFlex.PyPOS`, all `SaleFlex.OFFICE` screens are static forms. This reduces runtime UI
complexity and supports predictable management flows:

- User and role management
- Product and catalog management
- Campaign and loyalty configuration
- Import operations
- Reporting dashboards

## Core Runtime Components

- **OfficeApp**: main application bootstrap.
- **StartupForm**: splash/about-style startup UI with live progress messages.
- **BootstrapDataLoader**: startup data preload and runtime validation before login.
- **AuthManager**: login/session handling.
- **ApiServer**: embedded REST server for local POS traffic.
- **SyncManager**: synchronization with `SaleFlex.GATE`.
- **ImportManager**: CSV/XML ingestion pipeline.
- **ReportManager**: aggregation and export pipeline.
- **HealthMonitor**: terminal status tracking and heartbeat processing.

## Startup Flow (Current Baseline)

1. Entry point starts runtime and logger.
2. Startup form appears first.
3. Bootstrap loader prepares initial in-memory context.
4. Login form is shown after bootstrap completes.

This staged startup keeps future data-loading and environment checks in one predictable place.

## Reliability Goals

- Local-first write path for critical POS-originated events.
- Retryable sync for external connectivity failures.
- Operational continuity on LAN when internet is down.
- Recoverable state through local database and audit logs.

---

[Back to index](README.md) | [Previous: Introduction](01-introduction.md) | [Next: Configuration](03-configuration.md)
