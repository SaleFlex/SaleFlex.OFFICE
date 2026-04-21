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
    """Typed container for startup-critical settings."""

    app_name: str
    app_version: str
    app_mode: str
    app_store_id: str
    app_office_id: str
    app_icon: str
    logging_level: str
    logging_console: bool
    logging_file: bool
    logging_dir: str
    logging_file_name: str
    security_password_hash: str
    security_session_idle_timeout_minutes: int


class Settings:
    """Load and expose `settings.toml` values."""

    _instance: "Settings | None" = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        config_path = Path(__file__).resolve().parent.parent / "settings.toml"
        with config_path.open("rb") as file:
            data = tomllib.load(file)

        app = _as_dict(data.get("app"))
        logging_data = _as_dict(data.get("logging"))
        security = _as_dict(data.get("security"))

        self._data = SettingsData(
            app_name=str(app.get("name", "SaleFlex.OFFICE")),
            app_version=str(app.get("version", "0.0.0")),
            app_mode=str(app.get("mode", "standalone")),
            app_store_id=str(app.get("store_id", "")),
            app_office_id=str(app.get("office_id", "")),
            app_icon=str(app.get("icon", "")),
            logging_level=str(logging_data.get("level", "INFO")),
            logging_console=bool(logging_data.get("console", True)),
            logging_file=bool(logging_data.get("file", True)),
            logging_dir=str(logging_data.get("log_dir", "logs")),
            logging_file_name=str(logging_data.get("log_file", "saleflex-office.log")),
            security_password_hash=str(security.get("password_hash", "bcrypt")),
            security_session_idle_timeout_minutes=int(
                security.get("session_idle_timeout_minutes", 30)
            ),
        )

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
    def app_store_id(self) -> str:
        return self._data.app_store_id

    @property
    def app_office_id(self) -> str:
        return self._data.app_office_id

    @property
    def app_icon(self) -> str:
        return self._data.app_icon

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
