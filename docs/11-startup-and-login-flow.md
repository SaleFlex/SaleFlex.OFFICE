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

This sequence ensures that required startup data is loaded before login interaction begins.

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

## Placeholder Authentication Rule

Until database-backed authentication is connected:

- Allowed startup users: `admin`, `manager`
- Temporary rule: `username == password`

This is only a bootstrap placeholder and will be replaced by `AuthService` + persistent user data.

## Next Planned Steps

1. Replace placeholder auth with real hashed password verification.
2. Add session state and role-based navigation guard.
3. Wire module launcher buttons to real module shell/forms.
4. Expand startup loader with reference caches and integration prechecks.

---

[Back to index](README.md) | [Previous: Development Roadmap](10-development-roadmap.md) | [Next: Fullscreen and Module Launcher Policy](12-module-launcher-and-fullscreen-policy.md)
