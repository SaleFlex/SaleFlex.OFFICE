> **Current status:** Foundation bootstrap implemented (startup + initial data load + login).

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

## Current Foundation Implementation

The first runnable desktop baseline is now available:

1. `saleflex.py` starts the app and prepares runtime context.
2. `StartupForm` (about/splash-style) opens first and displays bootstrap progress.
3. `BootstrapDataLoader` loads startup context and validates mode settings.
4. `LoginForm` opens after bootstrap in fullscreen and validates credentials against the `cashier` table.
5. Successful login opens `ModuleLauncherForm`, which lists module buttons in fullscreen.
6. `Cashier Management`, `Product Management`, `Campaign Management`, `Customer Management`, `POS Management`, `Form Management`, and `Warehouse Management` module buttons are now connected to dedicated operations forms.
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
13. PyPOS-compatible definition models are available under `data_layer/model/definition`.
14. Model style is preserved as classic SQLAlchemy `Column` declarations (no `Mapped` pattern).
15. Multi-terminal store support is added with Office-specific terminal scope fields.
16. `form` model now supports terminal targeting with `is_shared_across_pos`, `fk_pos_terminal_id`,
    and `Form.is_available_for_pos(...)` for runtime checks.
17. Dedicated loyalty management workflows are available via `LoyaltyManagementForm` and `LoyaltyOperationsForm`,
    including CRUD for loyalty definition tables (`loyalty_program`, `loyalty_tier`, `loyalty_earn_rule`,
    `loyalty_program_policy`, `loyalty_redemption_policy`) plus customer loyalty usage tables.
18. Dedicated warehouse management workflows are available via `WarehouseManagementForm` and `WarehouseOperationsForm`,
    including CRUD for warehouse definition tables (`warehouse`, `warehouse_location`) and warehouse operation tables
    (`warehouse_product_stock`, `warehouse_stock_movement`, `warehouse_stock_adjustment`) plus aggregated warehouse operations.

This baseline is intentionally simple and prepared for iterative expansion.

## UI Design Direction

- Desktop-first and keyboard-first interaction model.
- No touch-target-focused layout requirement.
- Predictable static forms for operational users (`admin`, `manager`).
- `StartupForm` remains splash/about-style and not fullscreen.
- All operational forms (starting with `LoginForm` and `ModuleLauncherForm`) run in fullscreen.

## Run (Development)

From `SaleFlex.OFFICE` directory:

```bash
pip install -r requirements.txt
python saleflex.py
```

Current login rule (implemented): credentials are validated against `cashier.user_name` and `cashier.password`
in the Office database. Only active users (`cashier.is_active = true`) can sign in.

Bootstrap now initializes database and seed data only for first startup (when DB file does not exist):

- Full `data_layer/db_init_data` seed pipeline (aligned with PyPOS model set)
- Default users: `admin`, `jdoe`, `jpace` (legacy `manager` is migrated to `jpace` when present)
- Default store: `STORE-001`
- Default POS terminal: `POS-001`
- Default POS settings bound to the terminal

After successful login, users are redirected to the module launcher screen where module entry buttons
are listed for the next workflow step. The cashier, product, campaign, customer, POS, form, and warehouse module buttons now open
operational workflow forms.

## Deployment Modes

`SaleFlex.OFFICE` supports two working modes configured by `settings.toml`:

- `standalone`: Office works as local store control center without `SaleFlex.GATE`.
- `gate`: Office is connected to `SaleFlex.GATE` and synchronizes upstream.

`SaleFlex.PyPOS` supports three modes (also via `settings.toml`):

- `standalone`
- `office`
- `gate`

This mode flag defines startup behavior and integration routing at launch.

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

## Documentation

Project documentation is available in `docs/`:

- `docs/README.md` - index and document map
- `docs/01-introduction.md`
- `docs/02-architecture.md`
- `docs/03-configuration.md`
- `docs/04-auth-and-roles.md`
- `docs/05-integration-contracts.md`
- `docs/06-data-sync-and-backup.md`
- `docs/07-bulk-import.md`
- `docs/08-reporting.md`
- `docs/09-project-structure.md`
- `docs/10-development-roadmap.md`
- `docs/11-startup-and-login-flow.md`
- `docs/12-module-launcher-and-fullscreen-policy.md`
- `docs/13-multi-pos-definition-model.md`
- `docs/14-cashier-management-module.md`
- `docs/15-product-management-module.md`
- `docs/16-campaign-management-module.md`
- `docs/17-customer-management-module.md`
- `docs/18-pos-management-module.md`
- `docs/19-form-management-module.md`
- `docs/20-loyalty-management-module.md`
- `docs/21-warehouse-management-module.md`

## License

This project is licensed under the MIT License. See `LICENSE` for details.
