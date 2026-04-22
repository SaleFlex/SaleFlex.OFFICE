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
    store_id: str
    office_id: str
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

        progress_callback("Building startup context for login...")
        time.sleep(0.1)

        return BootstrapContext(
            app_mode=settings.app_mode,
            store_id=settings.app_store_id,
            office_id=settings.app_office_id,
            available_roles=("admin", "manager"),
        )
