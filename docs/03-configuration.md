# Configuration

`SaleFlex.OFFICE` uses `settings.toml` for startup-critical settings.

## Configuration Goals

- Decide runtime mode (`standalone` or `gate`)
- Identify the store context (`store_id`)
- Configure API server, database, sync, import, and reporting behavior

## Main File

- Path: `../settings.toml`
- Load time: at application startup before full module initialization

## Mode Settings

### SaleFlex.PyPOS mode (in its own `settings.toml`)

`SaleFlex.PyPOS` mode should be standardized as:

- `standalone`
- `office`
- `gate`

### SaleFlex.OFFICE mode

`SaleFlex.OFFICE` mode should be:

- `standalone`: no central GATE sync required
- `gate`: central sync enabled

## Store Identity Fields

- `store_id`: mandatory primary store identifier
- `office_id`: office terminal/service identifier inside that store

### About `managed_store_ids`

`managed_store_ids` is an optional list used only when one Office instance manages multiple stores
from a single deployment (regional controller pattern).

Examples:

- Single-store deployment: only `store_id` is enough.
- Multi-store controller deployment:
  - `store_id = "HQ-REGION-A"`
  - `managed_store_ids = ["STORE-001", "STORE-002", "STORE-003"]`

For current MVP, a single-store setup is recommended, so `managed_store_ids` is optional and can be
introduced later.

## Suggested Keys

```toml
[app]
mode = "standalone" # standalone | gate
store_id = "STORE-001"
office_id = "OFFICE-001"

[network]
host = "0.0.0.0"
port = 8710
api_prefix = "/api/v1"

[gate]
enabled = false
base_url = ""
api_key = ""
```

## Platform Note

PySide6 supports both Windows and Linux. The difference is usually not framework capability, but:

- packaging/distribution format,
- driver/peripheral dependencies,
- IT deployment policy in customer environments.

So configuration remains platform-neutral unless a deployment profile requires OS-specific overrides.

---

[Back to index](README.md) | [Previous: Architecture](02-architecture.md) | [Next: Auth and Roles](04-auth-and-roles.md)
