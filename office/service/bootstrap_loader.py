"""
Startup bootstrap data loader for SaleFlex.OFFICE.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from data_layer.db_manager import initialize_database
from settings.settings import Settings


ProgressCallback = Callable[[str], None]


@dataclass(frozen=True)
class BootstrapContext:
    """Data loaded during startup and shared with the first UI forms."""

    app_mode: str
    store_code: str
    office_code: str
    available_roles: tuple[str, ...]


class BootstrapDataLoader:
    """Load startup data before the login form is shown."""

    def load(self, progress_callback: ProgressCallback) -> BootstrapContext:
        """Execute startup loading steps in sequence."""
        settings = Settings()

        progress_callback("Reading application configuration...")
        time.sleep(0.15)

        progress_callback("Preparing initial reference cache...")
        initialize_database()
        time.sleep(0.2)

        progress_callback("Validating runtime mode and environment...")
        if settings.app_mode not in {"standalone", "gate"}:
            raise ValueError(
                "Invalid app mode in settings.toml. Supported values: standalone, gate."
            )
        time.sleep(0.15)

        progress_callback("Starting REST API server for POS terminals...")
        from api.server import start_api_server
        start_api_server(
            host=settings.network_host,
            port=settings.network_port,
            access_log=settings.network_access_log,
        )
        time.sleep(0.1)

        progress_callback("Building startup context for login...")
        time.sleep(0.1)

        return BootstrapContext(
            app_mode=settings.app_mode,
            store_code=settings.app_store_code,
            office_code=settings.app_office_code,
            available_roles=("admin", "manager"),
        )
