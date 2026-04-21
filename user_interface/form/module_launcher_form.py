"""
Fullscreen module launcher shown after successful login.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from settings.settings import Settings


class ModuleLauncherForm(QWidget):
    """Display available module buttons after login."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.setWindowTitle(f"{Settings().app_name} - Modules")
        self.setMinimumSize(1024, 640)
        self._module_names = (
            "Product Management",
            "Campaign Management",
            "Customer Management",
            "Reports",
            "Bulk Import",
            "Data Sync and Backup",
            "System Settings",
            "User and Role Management",
        )

        title_label = QLabel("Module Launcher")
        title_label.setAlignment(Qt.AlignHCenter)
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))

        subtitle_label = QLabel(
            f"User: {self.username}  |  Store: {bootstrap_context.store_id}  |  Office: {bootstrap_context.office_id}"
        )
        subtitle_label.setAlignment(Qt.AlignHCenter)
        subtitle_label.setStyleSheet("color: #475569;")

        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(
            "QFrame {"
            "background-color: #ffffff;"
            "border: 1px solid #cbd5e1;"
            "border-radius: 12px;"
            "}"
        )
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
            button.setMinimumHeight(58)
            button.setStyleSheet("font-size: 14px;")
            button.clicked.connect(
                lambda _checked=False, name=module_name: self._on_module_clicked(name)
            )
            row = index // 2
            column = index % 2
            grid_layout.addWidget(button, row, column)

        card_layout.addLayout(grid_layout)
        card.setLayout(card_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(48, 40, 48, 40)
        root_layout.addWidget(card)
        self.setLayout(root_layout)

    def _on_module_clicked(self, module_name: str) -> None:
        self.setWindowTitle(f"{Settings().app_name} - {module_name} (coming soon)")

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.showFullScreen()
