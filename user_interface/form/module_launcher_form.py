"""
Fullscreen module launcher shown after successful login.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from settings.settings import Settings
from user_interface.form.campaign_management_form import CampaignManagementForm
from user_interface.form.cashier_management_form import CashierManagementForm
from user_interface.form.customer_management_form import CustomerManagementForm
from user_interface.form.definitions_management_form import DefinitionsManagementForm
from user_interface.form.form_management_form import FormManagementForm
from user_interface.form.loyalty_management_form import LoyaltyManagementForm
from user_interface.form.pos_management_form import PosManagementForm
from user_interface.form.product_management_form import ProductManagementForm
from user_interface.form.sync_management_form import SyncManagementForm
from user_interface.form.system_settings_form import SystemSettingsForm
from user_interface.form.warehouse_management_form import WarehouseManagementForm


class ModuleLauncherForm(QWidget):
    """Display available module buttons after login."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.setObjectName("moduleLauncherRoot")
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.setWindowTitle(f"{Settings().app_name} - Modules")
        self.setMinimumSize(1024, 640)
        self._cashier_management_form: CashierManagementForm | None = None
        self._product_management_form: ProductManagementForm | None = None
        self._campaign_management_form: CampaignManagementForm | None = None
        self._customer_management_form: CustomerManagementForm | None = None
        self._loyalty_management_form: LoyaltyManagementForm | None = None
        self._pos_management_form: PosManagementForm | None = None
        self._form_management_form: FormManagementForm | None = None
        self._warehouse_management_form: WarehouseManagementForm | None = None
        self._definitions_management_form: DefinitionsManagementForm | None = None
        self._sync_management_form: SyncManagementForm | None = None
        self._system_settings_form: SystemSettingsForm | None = None
        self._module_names = (
            "Cashier Management",
            "Product Management",
            "Campaign Management",
            "Customer Management",
            "Loyalty Management",
            "POS Management",
            "Form Management",
            "Warehouse Management",
            "Definitions Management",
            "Reports",
            "Bulk Import",
            "Data Sync and Backup",
            "System Settings",
        )

        title_label = QLabel("Module Launcher")
        title_label.setObjectName("launcherTitle")
        title_label.setAlignment(Qt.AlignHCenter)
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))

        subtitle_label = QLabel(
            f"User: {self.username}  |  Store: {bootstrap_context.store_code}  |  Office: {bootstrap_context.office_code}"
        )
        subtitle_label.setObjectName("launcherSubtitle")
        subtitle_label.setAlignment(Qt.AlignHCenter)

        card = QFrame()
        card.setObjectName("moduleLauncherCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMaximumWidth(1080)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(18)
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(14)
        grid_layout.setVerticalSpacing(14)

        for index, module_name in enumerate(self._module_names):
            button = QPushButton(module_name)
            button.setObjectName("moduleButton")
            button.setMinimumHeight(58)
            button.setMinimumWidth(280)
            button.setStyleSheet("font-size: 14px; font-weight: 600;")
            button.clicked.connect(
                lambda _checked=False, name=module_name: self._on_module_clicked(name)
            )
            row = index // 2
            column = index % 2
            grid_layout.addWidget(button, row, column)

        card_layout.addLayout(grid_layout)
        actions_layout = QHBoxLayout()
        actions_layout.addStretch(1)
        exit_button = QPushButton("Exit Application")
        exit_button.setObjectName("exitButton")
        exit_button.clicked.connect(self._on_exit_clicked)
        actions_layout.addWidget(exit_button)
        card_layout.addLayout(actions_layout)
        card.setLayout(card_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(48, 40, 48, 40)
        root_layout.addStretch(1)
        root_layout.addWidget(card, alignment=Qt.AlignHCenter)
        root_layout.addStretch(1)
        self.setLayout(root_layout)
        self._apply_styles()

    def _on_module_clicked(self, module_name: str) -> None:
        if module_name.startswith("Cashier Management"):
            self._open_cashier_management()
            return
        if module_name.startswith("Product Management"):
            self._open_product_management()
            return
        if module_name.startswith("Campaign Management"):
            self._open_campaign_management()
            return
        if module_name.startswith("Customer Management"):
            self._open_customer_management()
            return
        if module_name.startswith("Loyalty Management"):
            self._open_loyalty_management()
            return
        if module_name.startswith("POS Management"):
            self._open_pos_management()
            return
        if module_name.startswith("Form Management"):
            self._open_form_management()
            return
        if module_name.startswith("Warehouse Management"):
            self._open_warehouse_management()
            return
        if module_name.startswith("Definitions Management"):
            self._open_definitions_management()
            return
        if module_name.startswith("Data Sync and Backup"):
            self._open_sync_management()
            return
        if module_name.startswith("System Settings"):
            self._open_system_settings()
            return
        self.setWindowTitle(f"{Settings().app_name} - {module_name} (coming soon)")

    def _open_cashier_management(self) -> None:
        """Open cashier management form as module workflow."""
        if self._cashier_management_form is None:
            self._cashier_management_form = CashierManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._cashier_management_form.show()
        self._cashier_management_form.raise_()
        self._cashier_management_form.activateWindow()

    def _open_product_management(self) -> None:
        """Open product management form as module workflow."""
        if self._product_management_form is None:
            self._product_management_form = ProductManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._product_management_form.show()
        self._product_management_form.raise_()
        self._product_management_form.activateWindow()

    def _on_exit_clicked(self) -> None:
        """Ask confirmation and close the full application."""
        answer = QMessageBox.question(
            self,
            "Exit Application",
            "Do you want to close SaleFlex.OFFICE?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        if self._cashier_management_form is not None:
            self._cashier_management_form.close()
        if self._product_management_form is not None:
            self._product_management_form.close()
        if self._campaign_management_form is not None:
            self._campaign_management_form.close()
        if self._customer_management_form is not None:
            self._customer_management_form.close()
        if self._loyalty_management_form is not None:
            self._loyalty_management_form.close()
        if self._pos_management_form is not None:
            self._pos_management_form.close()
        if self._form_management_form is not None:
            self._form_management_form.close()
        if self._warehouse_management_form is not None:
            self._warehouse_management_form.close()
        if self._definitions_management_form is not None:
            self._definitions_management_form.close()
        if self._sync_management_form is not None:
            self._sync_management_form.close()
        if self._system_settings_form is not None:
            self._system_settings_form.close()
        QApplication.instance().quit()

    def _open_campaign_management(self) -> None:
        """Open campaign management form as module workflow."""
        if self._campaign_management_form is None:
            self._campaign_management_form = CampaignManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._campaign_management_form.show()
        self._campaign_management_form.raise_()
        self._campaign_management_form.activateWindow()

    def _open_customer_management(self) -> None:
        """Open customer management form as module workflow."""
        if self._customer_management_form is None:
            self._customer_management_form = CustomerManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._customer_management_form.show()
        self._customer_management_form.raise_()
        self._customer_management_form.activateWindow()

    def _open_loyalty_management(self) -> None:
        """Open loyalty management form as module workflow."""
        if self._loyalty_management_form is None:
            self._loyalty_management_form = LoyaltyManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._loyalty_management_form.show()
        self._loyalty_management_form.raise_()
        self._loyalty_management_form.activateWindow()

    def _open_pos_management(self) -> None:
        """Open POS management form as module workflow."""
        if self._pos_management_form is None:
            self._pos_management_form = PosManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._pos_management_form.show()
        self._pos_management_form.raise_()
        self._pos_management_form.activateWindow()

    def _open_form_management(self) -> None:
        """Open form management form as module workflow."""
        if self._form_management_form is None:
            self._form_management_form = FormManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._form_management_form.show()
        self._form_management_form.raise_()
        self._form_management_form.activateWindow()

    def _open_warehouse_management(self) -> None:
        """Open warehouse management form as module workflow."""
        if self._warehouse_management_form is None:
            self._warehouse_management_form = WarehouseManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._warehouse_management_form.show()
        self._warehouse_management_form.raise_()
        self._warehouse_management_form.activateWindow()

    def _open_definitions_management(self) -> None:
        """Open definitions management form as module workflow."""
        if self._definitions_management_form is None:
            self._definitions_management_form = DefinitionsManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._definitions_management_form.show()
        self._definitions_management_form.raise_()
        self._definitions_management_form.activateWindow()

    def _open_sync_management(self) -> None:
        """Open data sync and backup form as module workflow."""
        if self._sync_management_form is None:
            self._sync_management_form = SyncManagementForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._sync_management_form.show()
        self._sync_management_form.raise_()
        self._sync_management_form.activateWindow()

    def _open_system_settings(self) -> None:
        """Open system settings form as module workflow."""
        if self._system_settings_form is None:
            self._system_settings_form = SystemSettingsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._system_settings_form.show()
        self._system_settings_form.raise_()
        self._system_settings_form.activateWindow()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.showFullScreen()

    def _apply_styles(self) -> None:
        """Apply stable launcher styles to avoid theme visibility issues."""
        self.setStyleSheet(
            """
            QWidget#moduleLauncherRoot {
                background-color: #0f172a;
            }
            QFrame#moduleLauncherCard {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }
            QLabel#launcherTitle {
                color: #0f172a;
                background: transparent;
            }
            QLabel#launcherSubtitle {
                color: #475569;
                background: transparent;
                font-size: 12px;
            }
            QPushButton#moduleButton {
                color: #ffffff;
                background-color: #1d4ed8;
                border: 1px solid #1e40af;
                border-radius: 8px;
                padding: 8px 12px;
            }
            QPushButton#moduleButton:hover {
                background-color: #1e40af;
            }
            QPushButton#moduleButton:pressed {
                background-color: #1e3a8a;
            }
            QPushButton#exitButton {
                color: #ffffff;
                background-color: #b91c1c;
                border: 1px solid #991b1b;
                border-radius: 8px;
                padding: 8px 14px;
                min-width: 160px;
                font-weight: 600;
            }
            QPushButton#exitButton:hover {
                background-color: #991b1b;
            }
            QPushButton#exitButton:pressed {
                background-color: #7f1d1d;
            }
            """
        )
