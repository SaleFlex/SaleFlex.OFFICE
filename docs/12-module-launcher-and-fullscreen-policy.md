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

The launcher currently provides a module button list as the first navigation shell:

1. Cashier Management
2. Product Management
3. Campaign Management
4. Customer Management
5. POS Management
6. Form Management
7. Warehouse Management
8. Reports
9. Bulk Import
10. Data Sync and Backup
11. System Settings

Current button behavior:

- `Cashier Management` is connected and opens `CashierManagementForm`.
- `Product Management` is connected and opens `ProductManagementForm`.
- `Campaign Management` is connected and opens `CampaignManagementForm`.
- `Customer Management` is connected and opens `CustomerManagementForm`.
- `POS Management` is connected and opens `PosManagementForm`.
- `Form Management` is connected and opens `FormManagementForm`.
- `Warehouse Management` is connected and opens `WarehouseManagementForm`.
- Remaining module buttons still behave as placeholders.

## Runtime Transition

Current high-level transition:

`StartupForm` -> `LoginForm` -> `ModuleLauncherForm` -> `CashierManagementForm` or `ProductManagementForm` or `CampaignManagementForm` or `CustomerManagementForm` or `PosManagementForm` or `FormManagementForm` or `WarehouseManagementForm`

Transition is coordinated in `office/manager/application.py`.

---

[Back to index](README.md) | [Previous: Startup and Login Flow](11-startup-and-login-flow.md) | [Next: Multi-POS Definition Data Model](13-multi-pos-definition-model.md)
