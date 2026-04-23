# System Settings Module

The **System Settings** module provides a graphical interface for configuring
`SaleFlex.OFFICE` application settings without manually editing `settings.toml`.

---

## Overview

- **Access**: Module Launcher → System Settings button
- **Form file**: `user_interface/form/system_settings_form.py`
- **Settings file**: `settings.toml` (project root)
- **Persistence**: Changes are written to `settings.toml` immediately on save;
  the in-memory `Settings` singleton is reloaded automatically via `Settings.reload()`.

---

## Tabs

### General

Configures the application mode and store identity.

| Field | Description |
|-------|-------------|
| **Application Mode** | `Standalone` — local-only, no GATE sync; `Gate` — sync with SaleFlex.GATE |
| **Store ID** | Primary store identifier shared with connected PyPOS terminals |
| **Office ID** | Identifier for this OFFICE instance |

> **Note:** Changing the mode takes full effect after an application restart.
> The REST server for PyPOS terminals starts at boot time and reflects the
> saved configuration from the next launch.

---

### POS Server

Configures the REST server endpoint that **SaleFlex.PyPOS** terminals connect to
when they are operating in `office` mode.

| Field | Default | Description |
|-------|---------|-------------|
| **Bind Host** | `0.0.0.0` | Network interface to listen on; `0.0.0.0` = all interfaces |
| **Port** | `8710` | TCP port for incoming PyPOS REST requests |

The matching `settings.toml` section in the **PyPOS** terminal:

```toml
[app]
mode = "office"

[office]
base_url = "http://<office-host-ip>:8710"
api_key  = "<api-key-issued-by-office>"
```

When a PyPOS terminal is in `office` mode it sends all data requests to this
endpoint and OFFICE responds with data from its **local database**. OFFICE does
**not** forward these requests to GATE in real time.

---

### GATE Integration

Configures the connection to **SaleFlex.GATE**. These settings apply only when
Application Mode is set to **Gate**.

| Field | Description |
|-------|-------------|
| **Base URL** | Full HTTP/HTTPS URL of the GATE instance (e.g. `http://192.168.1.100:8800`) |
| **API Key** | Authentication key issued by the GATE instance |
| **Terminal ID** | This OFFICE instance's terminal ID as registered in GATE |
| **Sync Interval** | How often (in minutes) OFFICE polls GATE for new data |
| **Retry Attempts** | Maximum push retry count before marking a sync item as failed |
| **Timeout** | Per-request HTTP timeout in seconds |

---

## Data Flow

```
                 ┌─────────────────────────────────────────────┐
                 │              SaleFlex.OFFICE                  │
                 │                                               │
  PyPOS request  │  REST /api/v1/...                            │
  ──────────────►│  OfficeAPIServer (port 8710)                 │
                 │       │                                       │
                 │       ▼                                       │
                 │  Local SQLite DB  ──► PyPOS response         │
                 │                                               │
                 │  (if mode = "gate")                           │
                 │       │                                       │
                 │  SyncWorker (background)                      │
                 │       │                  ┌──────────────────┐ │
                 │       └──────────────────► SaleFlex.GATE    │ │
                 │         pull / push      └──────────────────┘ │
                 └─────────────────────────────────────────────┘
```

Key principle: **PyPOS never waits for GATE**. OFFICE always returns its locally
stored data to PyPOS immediately, regardless of whether GATE is reachable.

---

## Standalone vs Gate mode summary

| Aspect | Standalone | Gate |
|--------|-----------|------|
| PyPOS requests served | Yes (from local DB) | Yes (from local DB) |
| GATE polling | No | Yes, every `sync_interval_minutes` |
| GATE push (transactions, closures) | No | Yes (background SyncWorker) |
| Local DB always current | Manually maintained | Auto-updated via GATE pull |

---

## Implementation Notes

- Settings are written using a custom serialiser in `system_settings_form.py`
  (`_write_toml`) because the standard `tomllib` module is read-only.
- After saving, `Settings.reload()` invalidates the singleton so subsequent
  property reads reflect the new values.
- The REST server (port 8710) is a planned component — the network settings
  stored here will be consumed once the server is implemented in a future release.

---

[Back to index](README.md) | [Previous: Sync Management Module](23-sync-management-module.md)
