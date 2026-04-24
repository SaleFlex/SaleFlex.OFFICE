# Project Structure

This document now reflects the implemented baseline structure and near-term expansion path.

## Implemented Baseline (Current)

```text
SaleFlex.OFFICE/
├── saleflex.py
├── settings.toml
├── requirements.txt
├── README.md
├── docs/
│   └── *.md
│
├── core/
│   ├── __init__.py
│   └── logger.py
│
├── settings/
│   ├── __init__.py
│   └── settings.py
│
├── data_layer/
│   ├── __init__.py
│   ├── engine.py
│   └── model/
│       ├── __init__.py
│       ├── crud_model.py
│       ├── mixins.py
│       └── definition/
│           ├── __init__.py
│           ├── *.py (PyPOS-aligned permanent model files)
│           ├── pos_terminal.py
│           └── ... (90+ models, no *_temp transaction tables)
│
├── office/
│   ├── __init__.py
│   ├── manager/
│   │   ├── __init__.py
│   │   └── application.py
│   └── service/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── bootstrap_loader.py
│       ├── campaign_management_service.py
│       ├── cashier_management_service.py
│       ├── customer_management_service.py
│       ├── definitions_management_service.py
│       ├── loyalty_management_service.py
│       ├── pos_management_service.py
│       ├── product_management_service.py
│       ├── sync_management_service.py
│       └── warehouse_management_service.py
│
└── user_interface/
    ├── __init__.py
    └── form/
        ├── __init__.py
        ├── startup_form.py
        ├── login_form.py
        ├── module_launcher_form.py
        ├── cashier_management_form.py
        ├── product_management_form.py
        ├── campaign_management_form.py
        ├── customer_management_form.py
        ├── loyalty_management_form.py
        ├── loyalty_operations_form.py
        ├── pos_management_form.py
        ├── form_management_form.py
        ├── warehouse_management_form.py
        ├── warehouse_operations_form.py
        ├── definitions_management_form.py
        └── sync_management_form.py
```

## Planned Expansion (Next Phases)

```text
SaleFlex.OFFICE/
├── data_layer/
│   ├── engine.py
│   ├── db_manager.py
│   ├── migration/
│   └── repository/
├── office/
│   ├── manager/
│   │   ├── auth_manager.py
│   │   ├── sync_manager.py
│   │   ├── import_manager.py
│   │   └── report_manager.py
│   ├── service/
│   │   ├── auth_service.py
│   │   ├── catalog_service.py
│   │   ├── campaign_service.py
│   │   └── reporting_service.py
│   ├── api/
│   └── integration/
└── user_interface/
    ├── controls/
    ├── navigation/
    └── form/
        ├── dashboard/
        ├── reports/
        └── system/
```

## Structure Rationale

- Keep startup, UI, and service responsibilities isolated from day one.
- Provide a clean bootstrap path (`StartupForm` -> preload -> `LoginForm` -> `ModuleLauncherForm`).
- Keep model compatibility with PyPOS by reusing original model style in Office.
- Extend only the fields required for store-level multi-terminal management.
- Keep each new functional module additive as implementation grows.
- Preserve static form philosophy while keeping keyboard-first desktop ergonomics.

## Transaction Model Policy

OFFICE shares the same **permanent** transaction ORM models as PyPOS
(`transaction_head`, `transaction_product`, `transaction_payment`, etc.) so it can
read the data written by terminals.

**Temporary (`*_temp`) transaction tables are intentionally absent from OFFICE.**
Those tables hold in-progress (draft) transaction state while a cashier is
building a sale on a POS terminal; they are purely PyPOS-internal and have no
meaning in a back-office context where every visible transaction is already
committed and closed.

---

[Back to index](README.md) | [Previous: Reporting](08-reporting.md) | [Next: Development Roadmap](10-development-roadmap.md)
