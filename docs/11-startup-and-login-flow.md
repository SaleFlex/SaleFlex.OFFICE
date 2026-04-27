# Startup and Login Flow

This document describes the first implemented runtime flow for `SaleFlex.OFFICE`.

## Implemented Sequence

`SaleFlex.OFFICE` now starts with the following order:

1. Run entry point: `saleflex.py`
2. Initialize `QApplication` and logger
3. Show `StartupForm` (about/splash-style screen)
4. Execute `BootstrapDataLoader` startup steps
5. Build `BootstrapContext` (mode, store, office, role defaults)
6. Dispose startup form and open `LoginForm` in fullscreen
7. After successful login, open `ModuleLauncherForm` in fullscreen
8. Logout from `ModuleLauncherForm` hides the launcher and re-presents `LoginForm`
   without restarting the process (REST service keeps running)

This sequence ensures that required startup data is loaded before login interaction begins.

During bootstrap, Office now also:

- creates database/tables on first startup when DB file is missing
- inserts full initial seed data pipeline from `data_layer/db_init_data`
- includes default users (`admin`, `jdoe`, `jpace`) and default terminal setup (`STORE-001`, `POS-001`)

## Runtime Components

- `office/manager/application.py`
  - Coordinates startup lifecycle.
  - Owns the transition from startup screen to login and then to module launcher.
- `office/service/bootstrap_loader.py`
  - Handles initial startup data loading.
  - Provides a progress callback for UI updates.
- `user_interface/form/startup_form.py`
  - Displays application title/version and progress message.
- `user_interface/form/login_form.py`
  - Keyboard-friendly static login form for desktop use in fullscreen mode.
- `user_interface/form/module_launcher_form.py`
  - Displays module entry buttons after successful login.

## Fullscreen and Keyboard-First UI Baseline

The current operational forms are intentionally non-touch-oriented and fullscreen:

- `StartupForm` is splash/about-style and does not use fullscreen.
- `LoginForm` opens in fullscreen with centered username/password inputs.
- `ModuleLauncherForm` opens in fullscreen and lists module buttons for navigation.
- Enter-key login support remains available via default button.

## Implemented Authentication Rule

`LoginForm` now delegates authentication to `AuthService`:

- user lookup by `cashier.user_name`
- password validation by `cashier.password`
- login allowed only when `cashier.is_active = true`
- soft-deleted users (`cashier.is_deleted = true`) are rejected

On successful login, `cashier.login_at` is updated and the module launcher transition continues.

## Logout Behavior

When the **Logout** button on `ModuleLauncherForm` is confirmed:

1. All open module forms are closed.
2. `ModuleLauncherForm` emits `logout_requested` and hides itself.
3. `OfficeApplication._on_logout()` destroys the launcher instance and calls
   `_show_login_form()` to display a fresh `LoginForm`.
4. The embedded Flask REST server (background daemon thread) is unaffected and continues
   to serve PyPOS terminals during the session change.

This allows a manager to hand off the workstation to another operator without
stopping store-level REST communication.

## Next Planned Steps

1. Replace plain-text password comparison with hashed password verification.
2. Add session state and role-based navigation guard.
3. Expand startup loader with reference caches and integration prechecks.

---

[Back to index](README.md) | [Previous: Development Roadmap](10-development-roadmap.md) | [Next: Fullscreen and Module Launcher Policy](12-module-launcher-and-fullscreen-policy.md)
