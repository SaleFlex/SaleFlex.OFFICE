"""
Read-only listing form for form operation summaries.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
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
from user_interface.form.form_controls_list_form import FormControlsListForm


class FormOperationsForm(QWidget):
    """Display read-only form summary rows and open selected form controls."""

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.service = PosManagementService(store_code=bootstrap_context.store_code)
        self.setWindowTitle(f"{Settings().app_name} - Form Operations")
        self.setMinimumSize(1120, 700)
        self._controls_windows: list[FormControlsListForm] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        title = QLabel("Form Operations")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._form_filter = QComboBox()
        self._form_filter.currentIndexChanged.connect(self.refresh_operations)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        open_controls_button = QPushButton("Open Selected Form Controls")
        open_controls_button.clicked.connect(self._open_selected_form_controls)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("Form Filter"))
        action_layout.addWidget(self._form_filter)
        action_layout.addStretch(1)
        action_layout.addWidget(refresh_button)
        action_layout.addWidget(open_controls_button)
        action_layout.addWidget(close_button)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            [
                "Form No",
                "Form Name",
                "Display Mode",
                "Controls",
                "Visible Controls",
                "Hidden Controls",
                "Tab Pages",
                "Form Id",
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.itemDoubleClicked.connect(lambda _: self._open_selected_form_controls())

        root = QVBoxLayout()
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(action_layout)
        root.addWidget(self._table)
        self.setLayout(root)

    def refresh(self) -> None:
        self._reload_form_filter()
        self.refresh_operations()

    def refresh_operations(self) -> None:
        selected_form_id = self._form_filter.currentData()
        rows = self.service.list_pos_form_operations()
        if selected_form_id:
            rows = [row for row in rows if row.form_id == selected_form_id]
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                str(row.form_no),
                row.form_name,
                row.display_mode,
                str(row.control_count),
                str(row.visible_control_count),
                str(row.hidden_control_count),
                str(row.tab_page_count),
                row.form_id,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.form_id)
                self._table.setItem(row_index, col, item)
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _reload_form_filter(self) -> None:
        selected_id = self._form_filter.currentData()
        self._form_filter.blockSignals(True)
        self._form_filter.clear()
        self._form_filter.addItem("All Forms", None)
        for row in self.service.list_form_lookups():
            self._form_filter.addItem(row.label, row.id)
        if selected_id:
            index = self._form_filter.findData(selected_id, role=Qt.UserRole)
            if index >= 0:
                self._form_filter.setCurrentIndex(index)
        self._form_filter.blockSignals(False)

    def _open_selected_form_controls(self) -> None:
        selected_items = self._table.selectedItems()
        if not selected_items:
            return
        form_id = selected_items[0].data(Qt.UserRole)
        row = selected_items[0].row()
        form_no = self._table.item(row, 0).text() if self._table.item(row, 0) else "?"
        form_name = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
        window = FormControlsListForm(
            bootstrap_context=self.bootstrap_context,
            username=self.username,
            form_id=str(form_id),
            form_label=f"{form_no} - {form_name}",
        )
        window.show()
        window.raise_()
        window.activateWindow()
        self._controls_windows.append(window)
