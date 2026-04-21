# Bulk Import (CSV/XML)

`SaleFlex.OFFICE` includes bulk data import capabilities for operational setup and maintenance.

## Import Goals

- Speed up first-time store setup
- Support periodic mass updates
- Reduce manual form entry for large catalogs

## Supported Formats (Initial)

- CSV
- XML

## Initial Import Domains

- Products and product attributes
- Campaign definitions
- Loyalty definitions and policy parameters

## Recommended Import Workflow

1. Upload file from Office UI.
2. Validate schema and mandatory fields.
3. Run business validation (duplicate checks, references, date ranges).
4. Show preview (accepted/rejected row counts).
5. Confirm import.
6. Persist accepted rows and write import audit log.
7. Export error report for rejected rows.

## File Management

Suggested directories:

- `imports/staging`
- `imports/archive`
- `imports/errors`

## Validation Rules (Baseline)

- Required columns/elements must exist.
- IDs/codes must be unique in effective scope.
- Date intervals must be valid.
- Numeric fields must pass type and range checks.
- Referential links (for example campaign-product relation) must resolve.

## Security and Audit

- Import operation requires manager/admin authorization.
- Every import writes:
  - actor user id
  - file metadata
  - execution timestamp
  - summary counters
  - error details artifact path

---

[Back to index](README.md) | [Previous: Data Sync and Backup](06-data-sync-and-backup.md) | [Next: Reporting](08-reporting.md)
