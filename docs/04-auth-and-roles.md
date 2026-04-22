# Authentication and Roles

This document defines role and access policy for `SaleFlex.OFFICE`.

## Access Scope

`SaleFlex.OFFICE` is intended for management-level users. Cashier-related maintenance is managed
by office users via administrative forms, not by cashier self-service sessions.

Primary Office roles:

- `admin`
- `manager`

Future enterprise roles can be added without breaking this model (for example,
`analyst` as report-only role).

## Cross-System Identity

Users are shared across the SaleFlex ecosystem. A user can log in to multiple SaleFlex applications
if they have explicit permission for each target system/terminal.

Examples:

- An `admin` can access both `SaleFlex.OFFICE` and `SaleFlex.PyPOS`.
- A `manager` can access Office and specific POS terminals if allowed by policy.
- A cashier-only user should not access Office screens.

## Permission Model (Initial)

- **Admin**
  - Full configuration rights
  - User and permission management
  - Import/export and advanced report access
  - Integration and sync settings
- **Manager**
  - Operational setup rights (catalog, campaigns, loyalty, reports)
  - Limited system administration
  - No global security-policy edits by default

## Authentication Requirements

- Secure password hashing (bcrypt recommended)
- Session timeout and idle expiration
- API token/JWT for REST calls
- Audit trail for login, logout, and sensitive operations

## Login UX Baseline (Implemented)

The current baseline login form is desktop/keyboard oriented:

- Username and password fields (non-touch-first form layout)
- Enter-key login trigger
- Inline login feedback message area

Authentication is now backed by persistent cashier records in the local Office database:

- Username is matched against `cashier.user_name`.
- Password is matched against `cashier.password`.
- Only active users (`cashier.is_active = true`) are allowed to log in.
- Soft-deleted users (`cashier.is_deleted = true`) are excluded from authentication.

This implementation is the first persistent login step. Password hashing and broader policy controls
remain part of the hardening roadmap.

## POS and Office Role Consistency

To avoid fragmented identity behavior:

1. Keep a single user authority model.
2. Attach permissions as capabilities, not app-specific hardcoded roles.
3. Evaluate app access (`PyPOS`, `OFFICE`, `GATE`) per user profile.

---

[Back to index](README.md) | [Previous: Configuration](03-configuration.md) | [Next: Integration Contracts](05-integration-contracts.md)
