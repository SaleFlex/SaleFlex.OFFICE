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
| 13 | `13-multi-pos-definition-model.md` | Multi-terminal data model and POS-scoped form targeting |
| 14 | `14-cashier-management-module.md` | Cashier module UI, CRUD, performance targets, and transaction metrics |
| 15 | `15-product-management-module.md` | Product module UI, product CRUD, catalog listing, and related product tables |
| 16 | `16-campaign-management-module.md` | Campaign module UI, campaign CRUD, and campaign-related operation tables |
| 17 | `17-customer-management-module.md` | Customer module UI, customer/segment/loyalty CRUD, and customer operations listing |
| 18 | `18-pos-management-module.md` | POS module UI and POS terminal/settings/virtual keyboard CRUD workflows |
| 19 | `19-form-management-module.md` | Form module UI with form/form-control/tab CRUD and POS scope assignment |
| 20 | `20-loyalty-management-module.md` | Dedicated loyalty definition module with loyalty CRUD and loyalty operations listing |
| 21 | `21-warehouse-management-module.md` | Dedicated warehouse module with warehouse/location/stock movement and adjustment CRUD workflows |

---

## Related Projects

- `../README.md` - top-level overview for `SaleFlex.OFFICE`
- `../../SaleFlex.PyPOS/README.md` - POS product context
- `../../SaleFlex.PyPOS/docs/40-integration-layer.md` - current integration baseline

---

**Version:** 0.1.0-alpha  
**Last Updated:** 2026-04-22
