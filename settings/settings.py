"""
Application settings loader for SaleFlex.OFFICE.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib


@dataclass(frozen=True)
class SettingsData:
    """Typed container for all settings.toml values used at runtime."""

    app_name: str
    app_version: str
    app_mode: str
    app_store_code: str
    app_office_code: str
    app_icon: str
    logging_level: str
    logging_console: bool
    logging_file: bool
    logging_dir: str
    logging_file_name: str
    database_engine: str
    database_name: str
    network_host: str
    network_port: int
    network_api_prefix: str
    network_request_timeout_seconds: int
    network_access_log: bool
    gate_base_url: str
    gate_api_key: str
    gate_terminal_id: str
    gate_sync_interval_minutes: int
    gate_retry_attempts: int
    gate_timeout_seconds: int
    security_password_hash: str
    security_session_idle_timeout_minutes: int


class Settings:
    """Load and expose `settings.toml` values as typed properties."""

    _instance: "Settings | None" = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    # ------------------------------------------------------------------
    # Singleton control
    # ------------------------------------------------------------------

    @classmethod
    def reload(cls) -> "Settings":
        """Discard the cached singleton and reload settings from disk."""
        cls._instance = None
        return cls()

    def _load(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / "settings.toml"
        with config_path.open("rb") as file:
            data = tomllib.load(file)

        app = _as_dict(data.get("app"))
        logging_data = _as_dict(data.get("logging"))
        database = _as_dict(data.get("database"))
        network = _as_dict(data.get("network"))
        gate = _as_dict(data.get("gate"))
        security = _as_dict(data.get("security"))

        self._data = SettingsData(
            app_name=str(app.get("name", "SaleFlex.OFFICE")),
            app_version=str(app.get("version", "0.0.0")),
            app_mode=str(app.get("mode", "standalone")),
            app_store_code=str(app.get("store_code", "")),
            app_office_code=str(app.get("office_code", "")),
            app_icon=str(app.get("icon", "")),
            logging_level=str(logging_data.get("level", "INFO")),
            logging_console=bool(logging_data.get("console", True)),
            logging_file=bool(logging_data.get("file", True)),
            logging_dir=str(logging_data.get("log_dir", "logs")),
            logging_file_name=str(logging_data.get("log_file", "saleflex-office.log")),
            database_engine=str(database.get("engine", "sqlite")),
            database_name=str(database.get("database_name", "office.sqlite3")),
            network_host=str(network.get("host", "0.0.0.0")),
            network_port=int(network.get("port", 9000)),
            network_api_prefix=str(network.get("api_prefix", "/api/v1")),
            network_request_timeout_seconds=int(
                network.get("request_timeout_seconds", 15)
            ),
            network_access_log=bool(network.get("access_log", False)),
            gate_base_url=str(gate.get("base_url", "")),
            gate_api_key=str(gate.get("api_key", "")),
            gate_terminal_id=str(gate.get("terminal_id", "")),
            gate_sync_interval_minutes=int(gate.get("sync_interval_minutes", 15)),
            gate_retry_attempts=int(gate.get("retry_attempts", 3)),
            gate_timeout_seconds=int(gate.get("timeout_seconds", 15)),
            security_password_hash=str(security.get("password_hash", "bcrypt")),
            security_session_idle_timeout_minutes=int(
                security.get("session_idle_timeout_minutes", 30)
            ),
        )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------

    @property
    def app_name(self) -> str:
        return self._data.app_name

    @property
    def app_version(self) -> str:
        return self._data.app_version

    @property
    def app_mode(self) -> str:
        return self._data.app_mode

    @property
    def app_store_code(self) -> str:
        return self._data.app_store_code

    @property
    def app_office_code(self) -> str:
        return self._data.app_office_code

    @property
    def app_icon(self) -> str:
        return self._data.app_icon

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @property
    def logging_level(self) -> str:
        return self._data.logging_level

    @property
    def logging_console(self) -> bool:
        return self._data.logging_console

    @property
    def logging_file(self) -> bool:
        return self._data.logging_file

    @property
    def logging_dir(self) -> str:
        return self._data.logging_dir

    @property
    def logging_file_name(self) -> str:
        return self._data.logging_file_name

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    @property
    def database_engine(self) -> str:
        return self._data.database_engine

    @property
    def database_name(self) -> str:
        return self._data.database_name

    # ------------------------------------------------------------------
    # Network / POS Server
    # ------------------------------------------------------------------

    @property
    def network_host(self) -> str:
        """Bind address for the REST server that PyPOS terminals connect to."""
        return self._data.network_host

    @property
    def network_port(self) -> int:
        """TCP port for the REST server that PyPOS terminals connect to."""
        return self._data.network_port

    @property
    def network_api_prefix(self) -> str:
        return self._data.network_api_prefix

    @property
    def network_request_timeout_seconds(self) -> int:
        return self._data.network_request_timeout_seconds

    @property
    def network_access_log(self) -> bool:
        """
        When True, Werkzeug logs every incoming HTTP request.
        Controlled by ``[network].access_log`` in settings.toml.
        Default: False (quiet production mode).
        """
        return self._data.network_access_log

    # ------------------------------------------------------------------
    # GATE integration
    # ------------------------------------------------------------------

    @property
    def gate_base_url(self) -> str:
        """SaleFlex.GATE base URL; empty when mode != 'gate'."""
        return self._data.gate_base_url

    @property
    def gate_api_key(self) -> str:
        return self._data.gate_api_key

    @property
    def gate_terminal_id(self) -> str:
        return self._data.gate_terminal_id

    @property
    def gate_sync_interval_minutes(self) -> int:
        return self._data.gate_sync_interval_minutes

    @property
    def gate_retry_attempts(self) -> int:
        return self._data.gate_retry_attempts

    @property
    def gate_timeout_seconds(self) -> int:
        return self._data.gate_timeout_seconds

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    @property
    def security_password_hash(self) -> str:
        return self._data.security_password_hash

    @property
    def security_session_idle_timeout_minutes(self) -> int:
        return self._data.security_session_idle_timeout_minutes


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
