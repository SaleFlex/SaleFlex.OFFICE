"""
Read-only listing form for controls of a selected dynamic form.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.pos_management_service import PosManagementService
from settings.settings import Settings


class FormControlsListForm(QWidget):
    """Display controls that belong only to one selected form."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        form_id: str,
        form_label: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.form_id = form_id
        self.form_label = form_label
        self.service = PosManagementService(store_code=bootstrap_context.store_code)
        self.setWindowTitle(f"{Settings().app_name} - Form Controls")
        self.setMinimumSize(1100, 640)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Form Controls")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"Form: {self.form_label}  |  User: {self.username}  |  Store: {self.bootstrap_context.store_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #334155;")

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(refresh_button)
        actions.addWidget(close_button)

        self._table = QTableWidget(0, 11)
        self._table.setHorizontalHeaderLabels(
            [
                "Control Name",
                "Type No",
                "Type",
                "Caption 1",
                "Caption 2",
                "Tab",
                "Width",
                "Height",
                "X",
                "Y",
                "Visible",
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(actions)
        root.addWidget(self._status_label)
        root.addWidget(self._table)
        self.setLayout(root)

    def refresh(self) -> None:
        rows = self.service.list_form_controls_for_form(self.form_id)
        self._status_label.setText(f"Loaded {len(rows)} controls for selected form.")
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row.name,
                str(row.type_no),
                row.type,
                row.caption1,
                row.caption2,
                row.tab_title or "-",
                str(row.width),
                str(row.height),
                str(row.location_x),
                str(row.location_y),
                "Yes" if row.is_visible else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._table.setItem(row_index, col, item)
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)
