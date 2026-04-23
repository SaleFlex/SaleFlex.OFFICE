# Configuration

`SaleFlex.OFFICE` stores all runtime settings in `settings.toml` located at the project root.
Settings can be changed through the **System Settings** module inside the application
(see [System Settings Module](24-system-settings-module.md)), or by editing the file directly.

## Configuration Goals

- Choose runtime mode: `standalone` (local-only) or `gate` (sync with SaleFlex.GATE)
- Identify the store and office context
- Configure the REST server endpoint that SaleFlex.PyPOS terminals connect to
- Configure SaleFlex.GATE integration parameters
- Configure database, logging, import, and reporting options

## Main File

- Path: `../settings.toml`
- Load time: at application startup, before full module initialization
- Runtime reload: `Settings.reload()` is called automatically after changes are saved
  through the System Settings form

---

## `[app]` — Application Identity and Mode

```toml
[app]
name = "SaleFlex.OFFICE"
version = "0.1.0-alpha"
mode = "standalone"    # standalone | gate
store_code = "STORE-001"
office_code = "OFFICE-001"
icon = "static_files\\images\\saleflex-office.ico"
```

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `standalone` | `standalone` = local-only; `gate` = sync with SaleFlex.GATE |
| `store_code` | `STORE-001` | Primary store code; must match `Store.store_code` in the OFFICE database and `[app].store_code` in all connected PyPOS instances |
| `office_code` | `OFFICE-001` | Unique code for this OFFICE instance; must match `[app].office_code` in all connected PyPOS instances |

### SaleFlex.OFFICE modes

| Mode | Behaviour |
|------|-----------|
| `standalone` | No GATE connection; OFFICE serves PyPOS terminals from its local database only |
| `gate` | Periodically pulls master-data from SaleFlex.GATE and pushes local POS data to it |

---

## `[network]` — POS Server Endpoint

SaleFlex.PyPOS terminals running in **office** mode connect to this endpoint to fetch
products, campaigns, customers, and loyalty data, and to submit transactions and closures.

```toml
[network]
host = "0.0.0.0"   # 0.0.0.0 = all interfaces; use a specific IP to restrict
port = 8710
api_prefix = "/api/v1"
request_timeout_seconds = 15
```

The matching PyPOS configuration is:

```toml
# SaleFlex.PyPOS settings.toml
[app]
mode          = "office"
terminal_code = "POS-001"    # registered in OFFICE under POS Management
store_code    = "STORE-001"  # must match OFFICE [app].store_code
office_code   = "OFFICE-001" # must match OFFICE [app].office_code

[office]
base_url    = "http://<office-ip>:9000"
api_key     = ""               # reserved for future use
api_prefix  = "/api/v1"
timeout_seconds = 10
```

**First-startup bootstrap:** when PyPOS starts in `office` mode without a local
database, it calls `GET /api/v1/pos/init` on this endpoint to pull all seed data.
OFFICE validates the `(office_code, store_code, terminal_code)` triplet against the
`store` and `pos_terminal` tables before responding.

---

## `[gate]` — SaleFlex.GATE Integration

Active only when `app.mode = "gate"`.

```toml
[gate]
base_url = ""        # e.g. http://192.168.1.100:8800
api_key = ""
terminal_id = ""
sync_interval_minutes = 15
retry_attempts = 3
timeout_seconds = 15
```

| Key | Default | Description |
|-----|---------|-------------|
| `base_url` | `""` | SaleFlex.GATE HTTP base URL |
| `api_key` | `""` | API key issued by the GATE instance |
| `terminal_id` | `""` | This OFFICE instance's terminal ID in GATE |
| `sync_interval_minutes` | `15` | How often OFFICE polls GATE for updates |
| `retry_attempts` | `3` | Max retries per push request before marking as failed |
| `timeout_seconds` | `15` | Per-request HTTP timeout |

---

## `[database]` — Storage Backend

```toml
[database]
engine = "sqlite"   # sqlite | postgresql | mysql | oracle | mssql
driver = ""
user_name = ""
password = ""
database_name = "office.sqlite3"
```

SQLite is the default for single-machine deployments.  For multi-user or
high-volume environments, switch to PostgreSQL or MySQL and provide the
connection parameters.

---

## `[security]`, `[logging]`, `[import]`, `[reporting]`

```toml
[logging]
level = "INFO"   # DEBUG | INFO | WARNING | ERROR | CRITICAL
console = true
file = true
log_dir = "logs"
log_file = "saleflex-office.log"

[security]
password_hash = "bcrypt"
jwt_access_minutes = 30
jwt_refresh_days = 7
session_idle_timeout_minutes = 30

[import]
csv_enabled = true
xml_enabled = true
max_file_mb = 50
staging_dir = "imports\\staging"
archive_dir = "imports\\archive"
error_dir = "imports\\errors"

[reporting]
dashboard_enabled = true
csv_export_enabled = true
pdf_export_enabled = true
default_timezone = "UTC"
currency_code = "USD"
```

---

## SaleFlex.PyPOS Mode Reference

`SaleFlex.PyPOS` has three operating modes configured in its own `settings.toml`:

| PyPOS Mode | Remote target | Description |
|------------|--------------|-------------|
| `standalone` | None | Fully offline; no synchronization |
| `office` | SaleFlex.OFFICE `[network]` endpoint | Sends requests to OFFICE; receives data from OFFICE's local DB |
| `gate` | SaleFlex.GATE `[gate]` endpoint | Connects directly to GATE |

When PyPOS is in `office` mode, OFFICE always responds with its **locally stored** data;
OFFICE does **not** forward the request to GATE in real time.

---

## Store Identity Fields

- `store_code`: primary store identifier shared by OFFICE and all its connected PyPOS
  terminals.  Stored in `Store.store_code` in the OFFICE database.
- `office_code`: identifies this OFFICE instance.  A single store may run multiple
  OFFICE instances (e.g. for different departments), each with its own `office_code`.

The combination `(office_code, store_code)` uniquely identifies a store–office pairing
across the entire SaleFlex ecosystem.  Adding `terminal_code` (from PyPOS `[app]`)
uniquely identifies a single POS terminal.

### Multi-office store support

A single store may have multiple OFFICE instances, each managing different sets of
POS terminals.  To enable this, create separate OFFICE deployments each with a unique
`office_code`.  POS terminals connect to their designated OFFICE by matching all three
fields: `office_code`, `store_code`, and `terminal_code`.

### Multi-store controller (future)

For regional controller deployments managing multiple stores, a `managed_store_codes`
list can be introduced.  For the current MVP, a single-store setup is recommended.

---

## Platform Note

`settings.toml` is platform-neutral.  Path separators (`\\` for Windows) in directory
settings should be adjusted when deploying on Linux.

---

[Back to index](README.md) | [Previous: Architecture](02-architecture.md) | [Next: Auth and Roles](04-auth-and-roles.md)
