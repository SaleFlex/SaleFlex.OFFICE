# Reporting

This document defines first-phase reporting requirements for `SaleFlex.OFFICE`.

## Output Channels

- On-screen dashboard views
- CSV export
- PDF export

Both dashboard and file exports are required in phase one.

## Reporting Scope

Reports must be available for:

- full store scope,
- selected POS terminals,
- single POS terminal detail.

## Initial Report Categories

- Sales summary (gross/net, discounts, taxes)
- Payment method distribution
- Product performance
- Campaign impact
- Loyalty activity
- Terminal operational status

## Time Filters

Required filters:

- date range
- shift/closure range
- terminal selection
- cashier/user selection (if authorized)

## Export Rules

- CSV for data-level analysis and spreadsheet workflows.
- PDF for printable and official management review output.
- Include report generation metadata (time, actor, filter set) in every export.

## Performance Expectations

- Dashboard interactions should be responsive for daily operations.
- Long-running exports should run asynchronously with progress feedback.
- Large reports should support background generation and download.

---

[Back to index](README.md) | [Previous: Bulk Import](07-bulk-import.md) | [Next: Project Structure](09-project-structure.md)
