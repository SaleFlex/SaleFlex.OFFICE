# Form Management Module

This document describes the implemented form metadata management module in `SaleFlex.OFFICE`.

## Purpose

`FormManagementForm` provides an Excel-like operational workspace for dynamic form metadata tables.
The module is launched from `ModuleLauncherForm` using the `Form Management` button.

## Implemented Tabs

The form is organized into four tabs:

1. **Forms**
   - Grid-based form listing with search.
   - New form creation.
   - Existing form update.
   - Soft delete for form records.
   - POS scope management:
     - `Available in All POS Terminals` option for shared forms.
     - POS terminal selector for terminal-specific forms.
     - Grid columns that show form scope and resolved terminal label.
2. **Form Controls**
   - Create, update, and soft delete form control records.
   - Supports form linkage, type metadata, captions, size, position, and target-form fields.
3. **Form Control Tabs**
   - Create, update, and soft delete form control tab page definitions.
   - Supports parent TABCONTROL linkage, tab order, title, and style fields.
4. **Form Operations**
   - Read-only operations summary for forms.
   - Displays per-form control count, visible/hidden control count, and tab-page count.
   - Supports opening selected-form controls in a dedicated window.

## Additional Operations Forms

Two additional forms are included:

- `FormOperationsForm`
  - Read-only operations list window for form metadata.
  - Includes form filtering and quick access to selected-form controls.
- `FormControlsListForm`
  - Dedicated detail window that lists controls only for one selected form.
  - Opened from both `FormManagementForm` and `FormOperationsForm`.

This flow satisfies the requirement where selecting a form opens another screen showing only controls of that form.

## Service Layer

Module logic is coordinated by `office/service/pos_management_service.py`.

Service responsibilities for this module:

- Validate form and form-related CRUD inputs.
- Enforce core uniqueness checks (for example form number).
- Enforce POS scope rules for forms (`all terminals` vs `single terminal`).
- Provide typed view models for form grids and operation summaries.
- Manage soft delete operations across form metadata tables.

## Data Models Used

The module currently uses:

- `form`
- `form_control`
- `form_control_tab`
- `pos_terminal` (lookup + terminal binding for scoped forms)

## Notes and Current Limits

- Form management workflows follow soft delete strategy.
- Form control tab lookup focuses on controls of type `TABCONTROL`.
- Operations windows are intentionally read-only in this phase.

---

[Back to index](README.md) | [Previous: POS Management Module](18-pos-management-module.md)
