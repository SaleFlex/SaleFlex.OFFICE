> **Current status:** Alpha v0.1.0a2 - Active Development (The project is not production-ready yet.)
> 
> Core POS functionality operational.

![Python 3.13](https://img.shields.io/badge/python-%3E=_3.13-success.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.11.0-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.48-green.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.3-yellow.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.0a2-orange.svg)

[SaleFlex Ecosystem](https://github.com/SaleFlex) | [SaleFlex.PyPOS](https://github.com/SaleFlex/SaleFlex.PyPOS) | **[SaleFlex.OFFICE](https://github.com/SaleFlex/SaleFlex.OFFICE)** | [SaleFlex.GATE](https://github.com/SaleFlex/SaleFlex.GATE) | [SaleFlex.KITCHEN](https://github.com/SaleFlex/SaleFlex.KITCHEN) | [SaleFlex.POS](https://github.com/SaleFlex/SaleFlex.POS)

# SaleFlex.OFFICE

**SaleFlex.OFFICE** is a PySide6 desktop back-office application in the SaleFlex ecosystem.
It provides static manager/admin forms, local store operations, POS data backup, and integration
orchestration between store terminals and central systems.

Unlike `SaleFlex.PyPOS` (touch-first and dynamic-form heavy), `SaleFlex.OFFICE` is designed as
an operations console with static forms and workflow-driven modules.

## Vision

- Provide complete store master-data management for one or many POS terminals.
- Act as a reliable local coordination node when internet is unstable.
- Synchronize with `SaleFlex.GATE` via REST/JSON when available.
- Keep a full local copy of POS operational data for reporting and backup.
- Enable managers/admins to run analytics and exports without using POS screens.

## Core Scope

- **Technology stack**: Python + PySide6 + SQLAlchemy.
- **UI model**: Static forms (no dynamic form runtime like PyPOS).
- **Integration protocol**: REST API + JSON for all system-to-system communication.
- **Bulk data load**: CSV/XML import tools for products, campaigns, and loyalty definitions.
- **Reporting**: On-screen dashboards plus CSV/PDF export.

## Architecture Overview

SaleFlex.OFFICE sits between in-store PyPOS terminals and central SaleFlex.GATE: PyPOS and OFFICE exchange REST/JSON on the LAN; OFFICE syncs with GATE when `gate` mode is enabled.

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

**Layers**

1. **UI** — PySide6 static forms (manager/admin workflows; no dynamic form interpreter).
2. **Application** — `office/manager` orchestration, validation, permissions.
3. **Service** — `office/service/*` business logic per module (products, sync, auth, and so on).
4. **API** — Flask app in `api/server.py` (versioned REST for PyPOS bootstrap and health).
5. **Data** — SQLAlchemy models under `data_layer/model` (PyPOS-compatible `Column` style).
6. **Sync** — Outbox/inbox models and UI (`SyncQueueItem`, `GateNotification`, Sync Management module).

**Core runtime pieces** (baseline): entry via `saleflex.py`, `StartupForm` → `BootstrapDataLoader` → `LoginForm` → `ModuleLauncherForm`; embedded REST server starts in a background thread at boot. Reliability goals are local-first writes for POS-originated data, retryable outbound sync, and continuity when WAN is down while LAN still works.

Full detail: [docs/02-architecture.md](docs/02-architecture.md).

## Project Structure

Implemented layout (high level):

```text
SaleFlex.OFFICE/
├── saleflex.py                 # Application entry
├── settings.toml               # Runtime configuration
├── requirements.txt
├── api/
│   ├── __init__.py
│   └── server.py               # Flask REST (/api/v1/...), daemon thread at startup
├── core/
│   └── logger.py
├── settings/
│   └── settings.py             # Settings singleton + reload after UI edits
├── data_layer/
│   ├── engine.py
│   └── model/
│       ├── crud_model.py, mixins.py
│       └── definition/         # PyPOS-aligned model files (100+)
├── office/
│   ├── manager/
│   │   └── application.py
│   └── service/                # Per-domain services (auth, bootstrap, product, …)
└── user_interface/form/        # Static PySide6 forms (login, launcher, modules, …)
```

Near-term expansion (migrations, repositories, dedicated managers for sync/import/report) is described in [docs/09-project-structure.md](docs/09-project-structure.md).

## Current Foundation Implementation

The first runnable desktop baseline is now available:

1. `saleflex.py` starts the app and prepares runtime context.
2. `StartupForm` (about/splash-style) opens first and displays bootstrap progress.
3. `BootstrapDataLoader` loads startup context and validates mode settings.
4. `LoginForm` opens after bootstrap in fullscreen and validates credentials against the `cashier` table.
5. Successful login opens `ModuleLauncherForm`, which lists module buttons in fullscreen.
6. `Cashier Management`, `Product Management`, `Campaign Management`, `Customer Management`, `Loyalty Management`, `POS Management`, `Form Management`, and `Warehouse Management` module buttons are now connected to dedicated operations forms.
7. Cashier module provides spreadsheet-style grids for:
   - cashier list and cashier CRUD operations (add, update, soft delete),
   - cashier performance target definition and lifecycle updates,
   - cashier transaction metrics listing with cashier-based filtering.
8. Product module provides spreadsheet-style workspaces for:
   - product list and product CRUD operations (add, update, soft delete),
   - product catalog listing with fast search and relational counters,
   - manufacturer CRUD, product unit CRUD, and product attribute CRUD,
   - product variant CRUD and product barcode CRUD,
   - cashier reference listing for office operators inside product workflow.
9. Campaign module provides spreadsheet-style workspaces for:
   - campaign list and campaign CRUD operations (add, update, soft delete),
   - campaign type CRUD, campaign rule CRUD, and campaign product CRUD,
   - campaign usage CRUD for office-side campaign event tracking,
   - campaign operations listing tab and a dedicated campaign operations window.
10. Customer module provides spreadsheet-style workspaces for:
   - customer list and customer CRUD operations (add, update, soft delete),
   - customer segment CRUD and segment member CRUD,
   - customer loyalty CRUD and loyalty point transaction CRUD,
   - customer operations listing tab and a dedicated customer operations window,
   - loyalty-focused launch actions for dedicated loyalty management and loyalty operations forms.
11. POS module provides spreadsheet-style workspaces for:
   - POS terminal list and POS terminal CRUD operations (add, update, soft delete),
   - POS settings CRUD and terminal-based filtering,
   - POS virtual keyboard definition CRUD.
12. Form module provides spreadsheet-style workspaces for:
   - form CRUD, form control CRUD, and form control tab CRUD,
   - form operations listing tab and dedicated operations windows,
   - selected-form control listing window and new form creation flow,
   - POS-scoped form assignment (single terminal or all terminals).
13. PyPOS-compatible permanent definition models are available under `data_layer/model/definition`.
    Temporary (`*_temp`) transaction models are intentionally excluded from OFFICE: those tables
    hold in-progress POS sale state and have no meaning in a back-office context where all visible
    transactions are already committed.
14. Model style is preserved as classic SQLAlchemy `Column` declarations (no `Mapped` pattern).
15. Multi-terminal store support is added with Office-specific terminal scope fields.
16. `form` model now supports terminal targeting with `is_shared_across_pos`, `fk_pos_terminal_id`,
    and `Form.is_available_for_pos(...)` for runtime checks.
17. Dedicated loyalty management workflows are available via `LoyaltyManagementForm` and `LoyaltyOperationsForm`,
    including CRUD for loyalty definition tables (`loyalty_program`, `loyalty_tier`, `loyalty_earn_rule`,
    `loyalty_program_policy`, `loyalty_redemption_policy`) plus customer loyalty usage tables.
    The `Loyalty Management` button is now directly accessible from the Module Launcher.
    Two additional read-only tabs display customer-assigned coupons (`Customer Coupons`) and coupon
    redemption history (`Coupon Usage History`) sourced from `coupon` and `coupon_usage` tables.
18. Dedicated warehouse management workflows are available via `WarehouseManagementForm` and `WarehouseOperationsForm`,
    including CRUD for warehouse definition tables (`warehouse`, `warehouse_location`) and warehouse operation tables
    (`warehouse_product_stock`, `warehouse_stock_movement`, `warehouse_stock_adjustment`) plus aggregated warehouse operations.
19. Dedicated definitions management workflow is available via `DefinitionsManagementForm`, providing spreadsheet-style
    tabbed workspaces for all core reference/master-data tables:
    - **Countries** tab: CRUD for `country` (name, ISO alpha-2/3, ISO numeric code).
    - **Country Regions** tab: CRUD for `country_region` (ISO 3166-2, region code, type, special requirements flag),
      with country filter combo.
    - **Cities** tab: CRUD for `city` (name, code, short name, numeric code, country link),
      with country filter combo.
    - **Districts** tab: CRUD for `district` (name, code, short name, numeric code, city link),
      with city filter combo.
    - **Currencies** tab: CRUD for `currency` (no, name, currency code, sign, sign direction, symbol, decimal places).
    - **Currency Rates** tab: CRUD for `currency_table` exchange rate pairs (base currency, target currency, rate).
    - **Payment Types** tab: CRUD for `payment_type` (no, name, description, culture info).
    - **VAT** tab: CRUD for `vat` (no, name, rate, description).
    The `Definitions Management` button is now accessible from the Module Launcher.
    - **Transaction Settings** tab has been added to `DefinitionsManagementForm`, providing two sub-tabs:
      - **Document Types**: CRUD for `transaction_document_type` (no, name, display name, description).
      - **Discount Types**: CRUD for `transaction_discount_type` (code, name, display name, description).
20. **Transaction Management** module is now available via `TransactionManagementForm`, providing a fully
    read-only, spreadsheet-style viewer for POS transaction data:
    - **All POS** tab: combined view of every transaction across all terminals.
    - **Per-POS tabs**: one tab per distinct `pos_id` found in `transaction_head`, labeled with terminal info.
    - Each POS tab contains a vertical splitter:
      - Upper panel: read-only `transaction_head` grid (receipt no, closure no, date/time, type, status,
        totals, currency, order source, cancelled flag). Color-coded status (green = completed, red = cancelled/refunded).
      - Lower panel with three detail sub-tabs loaded on transaction row selection:
        - **Products**: read-only `transaction_product` grid (line, code, name, qty, unit price, discount,
          total, VAT, VAT %, UOM, voided flag).
        - **Payments**: read-only `transaction_payment` grid (line, type, amount, currency, status, provider,
          card type/mask, authorization code). Color-coded payment status.
        - **Discounts**: read-only `transaction_discount` grid (line, discount type name, amount, rate, code).
    - All grids support column sorting, alternating row colors, and auto-resize to content.
    - No add / edit / delete operations are exposed; the module is strictly read-only.
    - The `Transaction Management` button is now connected in the Module Launcher.
21. Dedicated Data Sync and Backup module is available via `SyncManagementForm`, implementing the offline outbox
    monitoring UI:
    - **Pending Queue** tab: read-only grid of all outbox items waiting to be dispatched, oldest-first.
    - **Failed Items** tab: grid of items that exhausted all retries, with error detail panel, individual
      reset-to-pending, individual delete, and batch reset-all-failed actions.
    - **Sent History** tab: grid of successfully delivered records, individual delete and clear-all actions.
    - **GATE Notifications** tab: inbound notification inbox from `SaleFlex.GATE`, with body detail panel,
      mark-one-read, and mark-all-read actions. Unread items are highlighted in blue.
    - Summary header banner shows live counts for pending, failed, sent, and unread notifications.
    The `Data Sync and Backup` button is now connected in the Module Launcher.
22. `SyncQueueItem` model (`data_layer/model/definition/sync_queue_item.py`) and `GateNotification` model
    are now registered in the model package and fully implemented (including `get_pending()`, `get_by_status()`,
    and `reset_to_pending()` methods).
23. `pipos_bootstrap_service.py` has been removed. The service was a placeholder that was never connected
    to any UI or runtime workflow. The topic registry it contained will be re-introduced as part of the
    REST API layer in Phase 3.
24. **System Settings** module is now available via `SystemSettingsForm`. It provides three tabs:
    - **General**: switch between `standalone` and `gate` mode, set Store Code and Office Code.
    - **POS Server**: configure bind host and port (default `0.0.0.0:9000`) that SaleFlex.PyPOS
      terminals connect to when running in `office` mode.
    - **GATE Integration**: configure SaleFlex.GATE base URL, API key, terminal ID, sync interval,
      retry attempts, and request timeout.
    Settings are written back to `settings.toml` and the in-memory `Settings` singleton is reloaded
    immediately. The `System Settings` button is now connected in the Module Launcher.
25. **REST API server** (`api/server.py`) now starts automatically in a background daemon thread
    during application boot. Provides:
    - `GET /api/v1/health` — liveness probe (always returns `{"status":"ok"}`).
    - `GET  /api/v1/pos/init?office_code=&store_code=&terminal_code=` — returns the complete
      initialization data set for a requesting POS terminal after validating its identity triplet.
    - `POST /api/v1/pos/transactions` — accepts a batch of completed transaction records pushed by
      a PyPOS terminal, including the full document tree (head, products, payments, discounts, etc.)
      and current sequence counter values. Validates the terminal identity, persists all records, and
      updates per-POS `transaction_sequence` rows.
    - `POST /api/v1/pos/closures` — accepts completed end-of-day closure records and all summary
      tables (VAT, payment type, department, discount, cashier, currency, country-specific data),
      then updates the same per-POS sequence counters.
    - `POST /api/v1/pos/sequences` — standalone endpoint to update per-POS sequence counters.
    The server uses Flask and listens on the `[network] host:port` configured in `settings.toml`.
26a. **Multi-POS transaction management**: OFFICE now supports receiving transactions from multiple
    POS terminals simultaneously. Each terminal is identified by `(terminal_code, pos_id)`.
    The `transaction_sequence` table stores per-POS counters independently using `(name, pos_id)`
    as the unique key, so `ReceiptNumber` and `ClosureNumber` from different terminals never collide.
26. Identity fields renamed from `store_id`/`office_id` to `store_code`/`office_code` throughout:
    - `settings.toml`, `Settings` class, `BootstrapContext`, and all UI forms updated.
    - The `(office_code, store_code, terminal_code)` triplet now uniquely identifies any POS
      terminal in the ecosystem, supporting multiple OFFICE instances per store.
27. **Logout support** added to `ModuleLauncherForm`:
    - A **Logout** button sits beside the existing **Exit Application** button in the action bar.
    - Confirming logout closes all open module forms, hides the launcher, and returns the UI to
      `LoginForm` without restarting the process.
    - The embedded Flask REST server keeps running in its background daemon thread throughout the
      session change, so PyPOS terminals remain served without interruption.
    - `ModuleLauncherForm` exposes a `logout_requested` PySide6 `Signal`; `OfficeApplication`
      handles it in `_on_logout()` by destroying the old launcher and opening a fresh login screen.

This baseline is intentionally simple and prepared for iterative expansion.

## UI Design Direction

- Desktop-first and keyboard-first interaction model.
- No touch-target-focused layout requirement.
- Predictable static forms for operational users (`admin`, `manager`).
- `StartupForm` remains splash/about-style and not fullscreen.
- All operational forms (starting with `LoginForm` and `ModuleLauncherForm`) run in fullscreen.

## Installation & Setup

**Prerequisites**

- Python **3.13+** (see badges above)
- Git checkout of this repo; work inside the `SaleFlex.OFFICE` directory

**Install dependencies**

```bash
cd SaleFlex.OFFICE
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

**Configuration**

- All runtime settings live in [`settings.toml`](settings.toml) at the project root (`[app]`, `[network]`, `[gate]`, `[database]`, `[logging]`, and so on).
- After login, **System Settings** can edit mode, store/office codes, POS server bind address, and GATE integration; saving reloads the in-memory `Settings` singleton.
- PyPOS terminals in **office** mode must use the same `store_code` and `office_code` as OFFICE, and a `terminal_code` registered in OFFICE. Match PyPOS `[office].base_url` to OFFICE `[network]` host and port.

See [docs/03-configuration.md](docs/03-configuration.md) for field-by-field reference.

**Run (development)**

```bash
python saleflex.py
```

**Login and first run**

- Credentials are checked against `cashier.user_name` / `cashier.password` in the Office database; only `cashier.is_active = true` users can sign in.
- On **first** startup (when the database file does not exist), bootstrap runs the full `data_layer/db_init_data` seed pipeline: default users `admin`, `jdoe`, `jpace` (legacy `manager` maps to `jpace` when present), default store `STORE-001`, terminal `POS-001`, and POS settings bound to that terminal.
- After login, **Module Launcher** lists operational modules (cashier, product, campaign, customer, loyalty, POS, form, warehouse, definitions, sync, system settings, and related operations forms).

## Deployment Modes

`SaleFlex.OFFICE` supports two working modes configured via `settings.toml`
(or the **System Settings** module in the application):

| OFFICE mode | Behaviour |
|-------------|-----------|
| `standalone` | Local-only; serves PyPOS terminals from local DB; no GATE sync |
| `gate` | Periodically pulls master-data from SaleFlex.GATE and pushes POS data back |

`SaleFlex.PyPOS` supports three modes configured in its own `settings.toml`:

| PyPOS mode | Connects to | Description |
|------------|------------|-------------|
| `standalone` | Nobody | Fully offline |
| `office` | SaleFlex.OFFICE (`[network]` host:port) | Requests served from OFFICE local DB |
| `gate` | SaleFlex.GATE (`[gate]` base_url) | Direct GATE integration |

Key rule: when PyPOS is in `office` mode, OFFICE **always responds with its locally stored data**.
OFFICE never forwards a PyPOS request to GATE in real time; data flows from GATE to OFFICE
in the background on a schedule.

**Post-closure master-data refresh:** after every successful closure push (`POST /api/v1/pos/closures`),
PyPOS automatically calls `GET /api/v1/pos/init` again and upserts the returned data into
its local SQLite database.  Any product, price, cashier, campaign, or loyalty-rule changes
made in OFFICE are thus reflected on the POS terminal at the start of each new sales period
without requiring a manual restart or re-bootstrap.  All in-memory caches on PyPOS
(`pos_data`, `product_data`, `ActiveCampaignCache`) are rebuilt immediately after the upsert
completes.

## User and Access Model

`SaleFlex.OFFICE` login is limited to non-cashier business roles:

- `admin`
- `manager`
- future enterprise roles (for example analytics/reporting roles)

Users are global across the SaleFlex ecosystem. A user with proper permission can log in to
`SaleFlex.PyPOS`, `SaleFlex.OFFICE`, and other authorized SaleFlex terminals.

## High-Level Data Flow

1. Managers define products, campaigns, loyalty rules, and payment settings in `SaleFlex.OFFICE`.
2. `SaleFlex.PyPOS` terminals pull required bootstrap definitions from `SaleFlex.OFFICE` over REST/JSON.
3. `SaleFlex.PyPOS` pushes operational events/transactions to `SaleFlex.OFFICE` over REST/JSON.
4. `SaleFlex.OFFICE` stores data locally and keeps backup continuity for store operations.
5. When internet is available, `SaleFlex.OFFICE` syncs required data to/from `SaleFlex.GATE`.
6. Managers run reports for one POS, selected POS terminals, or the full store.

Because POS terminals continuously transmit their work to `SaleFlex.OFFICE`, the Office database
also acts as a practical in-store backup source during internet outages or terminal hardware issues.

## Development Roadmap

Phased plan from bootstrap to production-ready operations (see [docs/10-development-roadmap.md](docs/10-development-roadmap.md)).

| Phase | Focus | Status (summary) |
|-------|--------|------------------|
| **1 — Foundation** | Package layout, `settings.toml`, DB + PyPOS-compatible models, static UI shell, REST skeleton (`/api/v1/health`, `/api/v1/pos/init`) | Largely delivered; auth/session polish and dashboard still evolving |
| **2 — Operational modules** | Product/campaign/POS/loyalty static forms, POS inbound APIs, backup/audit | Many management UIs shipped; POS transaction/closure APIs and health monitor still open |
| **3 — Integration & sync** | GATE connector, background worker, idempotency, POST endpoints for PyPOS | Outbox/inbox models, sync UI, system settings, `pos/init` delivered; GATE worker and ingestion endpoints pending |
| **4 — Bulk import & reporting** | CSV/XML wizard, dashboards, CSV/PDF export | Planned |
| **5 — Hardening** | Security, performance, packaging, runbooks | Planned |

**MVP target:** static Office UI for admin/manager roles, REST for PyPOS bootstrap and event ingestion, local-first persistence, basic GATE sync in `gate` mode, starter reporting (dashboard + CSV/PDF).

## Documentation

Project documentation is available in `docs/`:

- [docs/README.md](docs/README.md) - index and document map
- [docs/01-introduction.md](docs/01-introduction.md)
- [docs/02-architecture.md](docs/02-architecture.md)
- [docs/03-configuration.md](docs/03-configuration.md)
- [docs/04-auth-and-roles.md](docs/04-auth-and-roles.md)
- [docs/05-integration-contracts.md](docs/05-integration-contracts.md)
- [docs/06-data-sync-and-backup.md](docs/06-data-sync-and-backup.md)
- [docs/07-bulk-import.md](docs/07-bulk-import.md)
- [docs/08-reporting.md](docs/08-reporting.md)
- [docs/09-project-structure.md](docs/09-project-structure.md)
- [docs/10-development-roadmap.md](docs/10-development-roadmap.md)
- [docs/11-startup-and-login-flow.md](docs/11-startup-and-login-flow.md)
- [docs/12-module-launcher-and-fullscreen-policy.md](docs/12-module-launcher-and-fullscreen-policy.md)
- [docs/13-multi-pos-definition-model.md](docs/13-multi-pos-definition-model.md)
- [docs/14-cashier-management-module.md](docs/14-cashier-management-module.md)
- [docs/15-product-management-module.md](docs/15-product-management-module.md)
- [docs/16-campaign-management-module.md](docs/16-campaign-management-module.md)
- [docs/17-customer-management-module.md](docs/17-customer-management-module.md)
- [docs/18-pos-management-module.md](docs/18-pos-management-module.md)
- [docs/19-form-management-module.md](docs/19-form-management-module.md)
- [docs/20-loyalty-management-module.md](docs/20-loyalty-management-module.md)
- [docs/21-warehouse-management-module.md](docs/21-warehouse-management-module.md)
- [docs/22-definitions-management-module.md](docs/22-definitions-management-module.md)
- [docs/23-sync-management-module.md](docs/23-sync-management-module.md)
- [docs/24-system-settings-module.md](docs/24-system-settings-module.md)

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Contributors

<table>
<tr>
    <td align="center">
        <a href="https://github.com/ferhat-mousavi">
            <img src="https://avatars.githubusercontent.com/u/5930760?v=4" width="100;" alt="Ferhat Mousavi"/>
            <br />
            <sub><b>Ferhat Mousavi</b></sub>
        </a>
    </td>
</tr>
</table>

## Donation and Support

If you like the project and want to support it or if you want to contribute to the development of new modules, you can donate to the following crypto addresses.

- USDT: `0xa5a87a939bfcd492f056c26e4febe102ea599b5b`
- BUSD: `0xa5a87a939bfcd492f056c26e4febe102ea599b5b`
- BTC: `15qyZpi6HjYyVhKKBsCbZSXU4bLdVJ8Phe`
- ETH: `0xa5a87a939bfcd492f056c26e4febe102ea599b5b`
- SOL: `Gt3bDczPcJvfBeg9TTBrBJGSHLJVkvnSSTov8W3QMpQf`
