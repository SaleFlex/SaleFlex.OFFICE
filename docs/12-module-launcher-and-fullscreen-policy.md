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
5. Loyalty Management
6. POS Management
7. Form Management
8. Warehouse Management
9. Definitions Management
10. Transaction Management
11. Reports
12. Bulk Import
13. Data Sync and Backup
14. System Settings

Current button behavior:

- `Cashier Management` is connected and opens `CashierManagementForm`.
- `Product Management` is connected and opens `ProductManagementForm`.
- `Campaign Management` is connected and opens `CampaignManagementForm`.
- `Customer Management` is connected and opens `CustomerManagementForm`.
- `Loyalty Management` is connected and opens `LoyaltyManagementForm`.
- `POS Management` is connected and opens `PosManagementForm`.
- `Form Management` is connected and opens `FormManagementForm`.
- `Warehouse Management` is connected and opens `WarehouseManagementForm`.
- `Definitions Management` is connected and opens `DefinitionsManagementForm`.
- `Transaction Management` is connected and opens `TransactionManagementForm`.
- `Data Sync and Backup` is connected and opens `SyncManagementForm`.
- `System Settings` is connected and opens `SystemSettingsForm`.
- `Reports` and `Bulk Import` are placeholders (coming soon).

## Action Buttons

The bottom action bar of `ModuleLauncherForm` provides two buttons:

- **Logout** — closes all open module forms, hides the launcher, and returns the application to
  `LoginForm`. The embedded REST service continues running in its background thread; no restart
  is required.
- **Exit Application** — asks confirmation, closes all open module forms, and terminates the
  process (`QApplication.quit()`).

The `logout_requested` signal on `ModuleLauncherForm` is emitted when the user confirms logout.
`OfficeApplication._on_logout()` handles the signal by destroying the current launcher instance
and calling `_show_login_form()` to present a fresh login screen.

## Runtime Transition

Current high-level transition:

```
StartupForm -> LoginForm -> ModuleLauncherForm -> <any management form>
                  ^                |
                  |   logout       |
                  +----------------+
```

Logout returns to `LoginForm` without restarting the process. The REST API server keeps serving
PyPOS terminals throughout the session change.

Transition is coordinated in `office/manager/application.py`.

---

[Back to index](README.md) | [Previous: Startup and Login Flow](11-startup-and-login-flow.md) | [Next: Multi-POS Definition Data Model](13-multi-pos-definition-model.md)
