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
4. `LoginForm` opens after bootstrap in fullscreen and accepts keyboard-based login input.
5. Successful login opens `ModuleLauncherForm`, which lists module buttons in fullscreen.
6. PyPOS-compatible definition models are available under `data_layer/model/definition`.
7. Model style is preserved as classic SQLAlchemy `Column` declarations (no `Mapped` pattern).
8. Multi-terminal store support is added with Office-specific terminal scope fields.

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

Current temporary login rule (MVP placeholder): `username == password` for default users (`admin`, `manager`).
This will be replaced by database-backed authentication in upcoming steps.

After successful login, users are redirected to the module launcher screen where module entry buttons
are listed for the next workflow step.

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

## License

This project is licensed under the MIT License. See `LICENSE` for details.
