# Introduction

`SaleFlex.OFFICE` is the back-office desktop application for managing store operations that feed
`SaleFlex.PyPOS` terminals and synchronize with `SaleFlex.GATE`.

It is built with:

- Python
- PySide6
- SQLAlchemy

## Why SaleFlex.OFFICE Exists

`SaleFlex.PyPOS` is optimized for cashier and checkout flows. `SaleFlex.OFFICE` is optimized for
manager and admin workflows with static forms and operational control.

Main objectives:

1. Maintain complete operational definitions required by POS terminals.
2. Keep local continuity even during internet interruptions.
3. Centralize store-level management and reporting.
4. Push and pull data with `SaleFlex.GATE` when online.

## Primary Use Cases

- Define and maintain products, prices, campaigns, and loyalty parameters.
- Provision operational data for one or many `SaleFlex.PyPOS` terminals.
- Receive transaction and status data from POS devices continuously.
- Produce reports for one terminal, selected terminals, or full store scope.
- Load bulk data by CSV/XML for fast go-live and periodic updates.

## Product Principles

- Static form-based UI (predictable and easy to train).
- API-first integration (REST + JSON).
- Offline-safe store operation.
- Clear role-based access for manager/admin-level users.
- Consistent user identity across the SaleFlex ecosystem.

## Deployment Profile

`SaleFlex.OFFICE` runs on local store infrastructure and can also connect to central services.
Because it uses PySide6, it is technically cross-platform (Windows and Linux), while production
packaging policy can be decided per customer rollout.

---

[Back to index](README.md) | [Next: Architecture](02-architecture.md)
