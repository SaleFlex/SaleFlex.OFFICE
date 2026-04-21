# Fullscreen and Module Launcher Policy

This document describes the implemented fullscreen behavior for Office forms and the new post-login module launcher baseline.

## Fullscreen Policy

`SaleFlex.OFFICE` uses a form-level fullscreen policy for operational workflows:

- `StartupForm` is considered splash/about style and stays non-fullscreen.
- `LoginForm` opens in fullscreen.
- `ModuleLauncherForm` opens in fullscreen.
- Future operational forms should follow fullscreen behavior unless explicitly marked as splash/about.

## Login Layout Baseline

The login screen now follows a centered-card layout inside a fullscreen window:

- Username and password fields stay in the middle area of the screen.
- Login action is keyboard-friendly with Enter-key default button behavior.
- Inline status message shows validation/authentication feedback.

## Post-Login Module Launcher

After successful authentication, the application opens `ModuleLauncherForm`.

The launcher currently provides a static module button list as the first navigation shell:

1. Product Management
2. Campaign Management
3. Customer Management
4. Reports
5. Bulk Import
6. Data Sync and Backup
7. System Settings
8. User and Role Management

The button actions are placeholders in the current baseline and will be connected to module forms in upcoming iterations.

## Runtime Transition

Current high-level transition:

`StartupForm` -> `LoginForm` -> `ModuleLauncherForm`

Transition is coordinated in `office/manager/application.py`.

---

[Back to index](README.md) | [Previous: Startup and Login Flow](11-startup-and-login-flow.md) | [Next: Multi-POS Definition Data Model](13-multi-pos-definition-model.md)
