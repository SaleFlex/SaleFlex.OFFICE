"""
Main application orchestration for SaleFlex.OFFICE.
"""

from __future__ import annotations

import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.logger import get_logger
from office.service.bootstrap_loader import BootstrapContext, BootstrapDataLoader
from settings.settings import Settings
from user_interface.form.login_form import LoginForm
from user_interface.form.module_launcher_form import ModuleLauncherForm
from user_interface.form.startup_form import StartupForm


logger = get_logger(__name__)


class OfficeApplication:
    """Coordinate startup flow and top-level forms."""

    def __init__(self) -> None:
        self.settings = Settings()
        self.app = QApplication([])
        self.app.setApplicationName(self.settings.app_name)

        icon_path = self.settings.app_icon
        if icon_path and os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        self.startup_form = StartupForm()
        self.bootstrap_loader = BootstrapDataLoader()
        self.login_form: LoginForm | None = None
        self.module_launcher_form: ModuleLauncherForm | None = None

    def run(self) -> int:
        """Run startup sequence and open login form."""
        context = self._run_bootstrap_sequence()
        self._show_login_form(context)
        return self.app.exec()

    def _run_bootstrap_sequence(self) -> BootstrapContext:
        self.startup_form.update_message("Starting SaleFlex.OFFICE...")
        self.startup_form.show()
        self.app.processEvents()

        context = self.bootstrap_loader.load(
            progress_callback=lambda message: self._on_bootstrap_progress(message)
        )

        self.startup_form.update_message("Initialization complete.")
        self.app.processEvents()
        self.startup_form.dispose()
        return context

    def _on_bootstrap_progress(self, message: str) -> None:
        logger.info("Startup step: %s", message)
        self.startup_form.update_message(message)
        self.app.processEvents()

    def _show_login_form(self, context: BootstrapContext) -> None:
        self.login_form = LoginForm(context)
        self.login_form.login_success.connect(
            lambda username: self._on_login_success(context=context, username=username)
        )
        self.login_form.show()

    def _on_login_success(self, context: BootstrapContext, username: str) -> None:
        logger.info("Login successful. Opening module launcher for user '%s'.", username)
        if self.login_form is not None:
            self.login_form.hide()

        self.module_launcher_form = ModuleLauncherForm(
            bootstrap_context=context,
            username=username,
        )
        self.module_launcher_form.logout_requested.connect(
            lambda: self._on_logout(context=context)
        )
        self.module_launcher_form.show()

    def _on_logout(self, context: BootstrapContext) -> None:
        """Destroy the current launcher and return to the login screen."""
        logger.info("User logged out. Returning to login screen.")
        if self.module_launcher_form is not None:
            self.module_launcher_form.deleteLater()
            self.module_launcher_form = None
        self._show_login_form(context)
