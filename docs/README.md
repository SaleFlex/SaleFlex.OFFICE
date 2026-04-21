# SaleFlex.OFFICE Documentation

This folder contains the initial project documentation for `SaleFlex.OFFICE`.
All documents are written in English to keep architecture, operations, and API contracts clear.

---

## Part 1 - Product and Architecture

| # | Document | Summary |
|---|---|---|
| 1 | `01-introduction.md` | Product purpose, use cases, and goals |
| 2 | `02-architecture.md` | System architecture and runtime components |
| 3 | `03-configuration.md` | `settings.toml` contract and mode behavior |
| 4 | `04-auth-and-roles.md` | Authentication and authorization model |
| 5 | `05-integration-contracts.md` | REST/JSON integration between Office, PyPOS, and GATE |

## Part 2 - Operations

| # | Document | Summary |
|---|---|---|
| 6 | `06-data-sync-and-backup.md` | Data synchronization and backup strategy |
| 7 | `07-bulk-import.md` | CSV/XML bulk import workflows |
| 8 | `08-reporting.md` | Dashboard and CSV/PDF reporting requirements |

## Part 3 - Engineering

| # | Document | Summary |
|---|---|---|
| 9 | `09-project-structure.md` | Suggested folder layout and module boundaries |
| 10 | `10-development-roadmap.md` | MVP plan and phased delivery |
| 11 | `11-startup-and-login-flow.md` | Implemented startup splash flow, fullscreen login, and post-login transition |
| 12 | `12-module-launcher-and-fullscreen-policy.md` | Fullscreen policy and module launcher baseline |
| 13 | `13-multi-pos-definition-model.md` | Multi-terminal data model for PyPOS definition ingestion |

---

## Related Projects

- `../README.md` - top-level overview for `SaleFlex.OFFICE`
- `../../SaleFlex.PyPOS/README.md` - POS product context
- `../../SaleFlex.PyPOS/docs/40-integration-layer.md` - current integration baseline

---

**Version:** 0.1.0-alpha  
**Last Updated:** 2026-04-21
