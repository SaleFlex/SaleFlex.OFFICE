# Multi-POS Definition Model

This document describes the current model strategy for `SaleFlex.OFFICE`:

- The model files under `SaleFlex.PyPOS/data_layer/model/definition` are copied into
  `SaleFlex.OFFICE/data_layer/model/definition`.
- Model style stays the same as original PyPOS (`Column(...)`, `Model`, `CRUD`, mixins).
- No `Mapped[...]` or `mapped_column(...)` pattern is used.

## Why This Approach

You requested model parity with PyPOS and no generic mapping layer.
With this approach, Office can run with explicit model classes and remain compatible with existing
PyPOS model semantics.

## Multi-POS Additions in Office

While preserving original models, Office adds store-level terminal scope:

- New model: `PosTerminal` (`pos_terminal` table)
- Updated model: `PosSettings`
  - `fk_store_id`
  - `fk_pos_terminal_id`
- Updated model: `TransactionHead`
  - `fk_pos_terminal_id`
- Updated model: `TransactionHeadTemp`
  - `fk_pos_terminal_id`
- Updated model: `Closure`
  - `fk_pos_terminal_id`
- Updated model: `Store`
  - `store_code`
  - `office_code`
- Updated model: `Form`
  - `is_shared_across_pos`
  - `fk_pos_terminal_id`
  - `is_available_for_pos(pos_terminal_id)` helper for terminal-level form eligibility checks

These additions enable one store to manage and identify multiple POS applications cleanly, including
form metadata that can be either terminal-specific or shared across all terminals.

## Runtime Flow

1. Definitions are created/updated in `SaleFlex.OFFICE`.
2. Each connected POS terminal is registered in `PosTerminal`.
3. PyPOS terminals pull definition data from Office bootstrap endpoints.
4. Transactional data pushed back from PyPOS is associated with terminal/store scope.

---

[Back to index](README.md) | [Previous: Fullscreen and Module Launcher Policy](12-module-launcher-and-fullscreen-policy.md)

