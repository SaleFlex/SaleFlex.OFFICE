"""
POS management module form with spreadsheet-style workflows.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from office.service.pos_management_service import (
    PosManagementService,
    PosSettingsView,
    PosTerminalView,
    PosVirtualKeyboardView,
)
from settings.settings import Settings


class PosManagementForm(QWidget):
    """Manage POS terminal, settings, and virtual keyboard entities."""

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
        self.setWindowTitle(f"{Settings().app_name} - POS Management")
        self.setMinimumSize(1360, 900)

        self._terminals: list[PosTerminalView] = []
        self._settings_rows: list[PosSettingsView] = []
        self._keyboards: list[PosVirtualKeyboardView] = []

        self._selected_terminal_id: str | None = None
        self._selected_settings_id: str | None = None
        self._selected_keyboard_id: str | None = None

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("POS Operations Center")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        subtitle = QLabel(
            f"User: {self.username}  |  Store: {self.bootstrap_context.store_code}  |  Office: {self.bootstrap_context.office_code}"
        )
        subtitle.setStyleSheet("color: #475569;")

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #0f172a;")
        self._status_label.setWordWrap(True)

        close_button = QPushButton("Close Module")
        close_button.clicked.connect(self.close)

        header_actions = QHBoxLayout()
        header_actions.addStretch(1)
        header_actions.addWidget(close_button)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_terminals_tab(), "POS Terminals")
        self._tabs.addTab(self._build_settings_tab(), "POS Settings")
        self._tabs.addTab(self._build_virtual_keyboard_tab(), "POS Virtual Keyboards")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_actions)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_terminals_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self._terminal_search_input = QLineEdit()
        self._terminal_search_input.setPlaceholderText("Search terminal code, name, serial, host or ip")
        self._terminal_search_input.returnPressed.connect(self.refresh_terminals)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_terminals)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_terminals)
        search_layout.addWidget(self._terminal_search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)
        left_layout.addLayout(search_layout)

        self._terminal_table = QTableWidget(0, 8)
        self._terminal_table.setHorizontalHeaderLabels(
            ["Code", "Name", "Serial", "Host", "IP", "Mode", "Online", "Active"]
        )
        self._terminal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._terminal_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._terminal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._terminal_table.verticalHeader().setVisible(False)
        self._terminal_table.setAlternatingRowColors(True)
        self._terminal_table.itemSelectionChanged.connect(self._on_terminal_row_selected)
        left_layout.addWidget(self._terminal_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("POS Terminal Editor")
        form = QFormLayout()
        self._terminal_code_input = QLineEdit()
        self._terminal_name_input = QLineEdit()
        self._terminal_serial_input = QLineEdit()
        self._terminal_host_input = QLineEdit()
        self._terminal_ip_input = QLineEdit()
        self._terminal_app_mode_input = QLineEdit()
        self._terminal_software_version_input = QLineEdit()
        self._terminal_pull_interval_input = QSpinBox()
        self._terminal_pull_interval_input.setRange(5, 3600)
        self._terminal_pull_interval_input.setValue(30)
        self._terminal_active_checkbox = QCheckBox("Active")
        self._terminal_active_checkbox.setChecked(True)
        self._terminal_online_checkbox = QCheckBox("Online")
        self._terminal_allowed_pull_checkbox = QCheckBox("Allowed Pull")
        self._terminal_allowed_pull_checkbox.setChecked(True)
        form.addRow("Terminal Code", self._terminal_code_input)
        form.addRow("Terminal Name", self._terminal_name_input)
        form.addRow("Serial Number", self._terminal_serial_input)
        form.addRow("Host Name", self._terminal_host_input)
        form.addRow("IP Address", self._terminal_ip_input)
        form.addRow("App Mode", self._terminal_app_mode_input)
        form.addRow("Software Version", self._terminal_software_version_input)
        form.addRow("Pull Interval (sec)", self._terminal_pull_interval_input)
        form.addRow(self._terminal_active_checkbox)
        form.addRow(self._terminal_online_checkbox)
        form.addRow(self._terminal_allowed_pull_checkbox)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        new_button.clicked.connect(self._clear_terminal_editor)
        save_button.clicked.connect(self._save_terminal)
        delete_button.clicked.connect(self._delete_terminal)
        actions.addWidget(new_button)
        actions.addWidget(save_button)
        actions.addWidget(delete_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addStretch(1)
        editor_layout.addLayout(actions)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([940, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._settings_terminal_filter_combo = QComboBox()
        self._settings_terminal_filter_combo.currentIndexChanged.connect(self.refresh_settings)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_settings)
        filter_layout.addWidget(QLabel("Terminal"))
        filter_layout.addWidget(self._settings_terminal_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._settings_table = QTableWidget(0, 9)
        self._settings_table.setHorizontalHeaderLabels(
            [
                "POS No",
                "Name",
                "Terminal",
                "Backend Type",
                "Backend IP1",
                "Backend Port1",
                "MAC Address",
                "Online Forced",
                "PLU Update No",
            ]
        )
        self._settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._settings_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._settings_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._settings_table.verticalHeader().setVisible(False)
        self._settings_table.setAlternatingRowColors(True)
        self._settings_table.itemSelectionChanged.connect(self._on_settings_row_selected)
        left_layout.addWidget(self._settings_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("POS Settings Editor")
        form = QFormLayout()
        self._settings_terminal_combo = QComboBox()
        self._settings_no_input = QSpinBox()
        self._settings_no_input.setRange(1, 99999)
        self._settings_name_input = QLineEdit()
        self._settings_owner_national_input = QLineEdit()
        self._settings_owner_tax_input = QLineEdit()
        self._settings_mac_input = QLineEdit()
        self._settings_backend_type_input = QLineEdit()
        self._settings_backend_type_input.setText("GATE")
        self._settings_backend_ip1_input = QLineEdit()
        self._settings_backend_port1_input = QLineEdit()
        self._settings_backend_ip2_input = QLineEdit()
        self._settings_backend_port2_input = QLineEdit()
        self._settings_force_online_checkbox = QCheckBox("Force To Work Online")
        self._settings_plu_update_no_input = QSpinBox()
        self._settings_plu_update_no_input.setRange(0, 999999)
        form.addRow("Terminal", self._settings_terminal_combo)
        form.addRow("POS No In Store", self._settings_no_input)
        form.addRow("Name", self._settings_name_input)
        form.addRow("Owner National Id", self._settings_owner_national_input)
        form.addRow("Owner Tax Id", self._settings_owner_tax_input)
        form.addRow("MAC Address", self._settings_mac_input)
        form.addRow("Backend Type", self._settings_backend_type_input)
        form.addRow("Backend IP1", self._settings_backend_ip1_input)
        form.addRow("Backend Port1", self._settings_backend_port1_input)
        form.addRow("Backend IP2", self._settings_backend_ip2_input)
        form.addRow("Backend Port2", self._settings_backend_port2_input)
        form.addRow(self._settings_force_online_checkbox)
        form.addRow("PLU Update No", self._settings_plu_update_no_input)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        new_button.clicked.connect(self._clear_settings_editor)
        save_button.clicked.connect(self._save_settings)
        delete_button.clicked.connect(self._delete_settings)
        actions.addWidget(new_button)
        actions.addWidget(save_button)
        actions.addWidget(delete_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addStretch(1)
        editor_layout.addLayout(actions)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([940, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_virtual_keyboard_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self._keyboard_search_input = QLineEdit()
        self._keyboard_search_input.setPlaceholderText("Search virtual keyboard name")
        self._keyboard_search_input.returnPressed.connect(self.refresh_virtual_keyboards)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_virtual_keyboards)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_virtual_keyboards)
        search_layout.addWidget(self._keyboard_search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)
        left_layout.addLayout(search_layout)

        self._keyboard_table = QTableWidget(0, 8)
        self._keyboard_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Width",
                "Height",
                "Font",
                "Font Size",
                "Button Size",
                "Control Width",
                "Active",
            ]
        )
        self._keyboard_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._keyboard_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._keyboard_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._keyboard_table.verticalHeader().setVisible(False)
        self._keyboard_table.setAlternatingRowColors(True)
        self._keyboard_table.itemSelectionChanged.connect(self._on_keyboard_row_selected)
        left_layout.addWidget(self._keyboard_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Virtual Keyboard Editor")
        form = QFormLayout()
        self._keyboard_name_input = QLineEdit()
        self._keyboard_width_input = QSpinBox()
        self._keyboard_width_input.setRange(100, 5000)
        self._keyboard_height_input = QSpinBox()
        self._keyboard_height_input.setRange(100, 3000)
        self._keyboard_x_input = QSpinBox()
        self._keyboard_x_input.setRange(-2000, 2000)
        self._keyboard_y_input = QSpinBox()
        self._keyboard_y_input.setRange(-2000, 2000)
        self._keyboard_font_family_input = QLineEdit()
        self._keyboard_font_size_input = QSpinBox()
        self._keyboard_font_size_input.setRange(6, 72)
        self._keyboard_button_width_input = QSpinBox()
        self._keyboard_button_width_input.setRange(20, 400)
        self._keyboard_button_height_input = QSpinBox()
        self._keyboard_button_height_input.setRange(20, 400)
        self._keyboard_button_bg_input = QLineEdit()
        self._keyboard_button_pressed_input = QLineEdit()
        self._keyboard_control_width_input = QSpinBox()
        self._keyboard_control_width_input.setRange(40, 400)
        self._keyboard_control_active_input = QLineEdit()
        self._keyboard_active_checkbox = QCheckBox("Active")
        self._keyboard_active_checkbox.setChecked(True)
        form.addRow("Name", self._keyboard_name_input)
        form.addRow("Keyboard Width", self._keyboard_width_input)
        form.addRow("Keyboard Height", self._keyboard_height_input)
        form.addRow("X Position", self._keyboard_x_input)
        form.addRow("Y Position", self._keyboard_y_input)
        form.addRow("Font Family", self._keyboard_font_family_input)
        form.addRow("Font Size", self._keyboard_font_size_input)
        form.addRow("Button Width", self._keyboard_button_width_input)
        form.addRow("Button Height", self._keyboard_button_height_input)
        form.addRow("Button Background", self._keyboard_button_bg_input)
        form.addRow("Button Pressed Color", self._keyboard_button_pressed_input)
        form.addRow("Control Button Width", self._keyboard_control_width_input)
        form.addRow("Control Active Color", self._keyboard_control_active_input)
        form.addRow(self._keyboard_active_checkbox)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        new_button.clicked.connect(self._clear_keyboard_editor)
        save_button.clicked.connect(self._save_keyboard)
        delete_button.clicked.connect(self._delete_keyboard)
        actions.addWidget(new_button)
        actions.addWidget(save_button)
        actions.addWidget(delete_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addStretch(1)
        editor_layout.addLayout(actions)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([940, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self.refresh_terminals()
        self.refresh_settings()
        self.refresh_virtual_keyboards()

    def refresh_terminals(self) -> None:
        self._terminals = self.service.list_pos_terminals(self._terminal_search_input.text().strip())
        self._terminal_table.setRowCount(len(self._terminals))
        for row_index, row in enumerate(self._terminals):
            values = [
                row.terminal_code,
                row.terminal_name,
                row.terminal_serial_no,
                row.host_name,
                row.ip_address,
                row.app_mode,
                "Yes" if row.is_online else "No",
                "Yes" if row.is_active else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._terminal_table.setItem(row_index, col, item)
        self._terminal_table.resizeColumnsToContents()
        self._reload_terminal_combos()

    def refresh_settings(self) -> None:
        self._settings_rows = self.service.list_pos_settings(
            terminal_id=self._settings_terminal_filter_combo.currentData()
        )
        self._settings_table.setRowCount(len(self._settings_rows))
        for row_index, row in enumerate(self._settings_rows):
            values = [
                str(row.pos_no_in_store),
                row.name,
                row.terminal_label,
                row.backend_type,
                row.backend_ip1,
                str(row.backend_port1 or ""),
                row.mac_address,
                "Yes" if row.force_to_work_online else "No",
                str(row.plu_update_no),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._settings_table.setItem(row_index, col, item)
        self._settings_table.resizeColumnsToContents()

    def refresh_virtual_keyboards(self) -> None:
        self._keyboards = self.service.list_pos_virtual_keyboards(self._keyboard_search_input.text().strip())
        self._keyboard_table.setRowCount(len(self._keyboards))
        for row_index, row in enumerate(self._keyboards):
            values = [
                row.name,
                str(row.keyboard_width),
                str(row.keyboard_height),
                row.font_family,
                str(row.font_size),
                f"{row.button_width}x{row.button_height}",
                str(row.control_button_width),
                "Yes" if row.is_active else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._keyboard_table.setItem(row_index, col, item)
        self._keyboard_table.resizeColumnsToContents()

    def _on_terminal_row_selected(self) -> None:
        selected = self._selected_row_payload(self._terminal_table, self._terminals)
        if selected is None:
            return
        self._selected_terminal_id = selected.id
        self._terminal_code_input.setText(selected.terminal_code)
        self._terminal_name_input.setText(selected.terminal_name)
        self._terminal_serial_input.setText(selected.terminal_serial_no)
        self._terminal_host_input.setText(selected.host_name)
        self._terminal_ip_input.setText(selected.ip_address)
        self._terminal_app_mode_input.setText(selected.app_mode)
        self._terminal_software_version_input.setText(selected.software_version)
        self._terminal_pull_interval_input.setValue(selected.pull_interval_seconds or 30)
        self._terminal_active_checkbox.setChecked(selected.is_active)
        self._terminal_online_checkbox.setChecked(selected.is_online)
        self._terminal_allowed_pull_checkbox.setChecked(selected.is_allowed_pull)

    def _on_settings_row_selected(self) -> None:
        selected = self._selected_row_payload(self._settings_table, self._settings_rows)
        if selected is None:
            return
        self._selected_settings_id = selected.id
        self._settings_terminal_combo.setCurrentIndex(
            self._settings_terminal_combo.findData(selected.fk_pos_terminal_id)
        )
        self._settings_no_input.setValue(selected.pos_no_in_store)
        self._settings_name_input.setText(selected.name)
        self._settings_owner_national_input.setText(selected.owner_national_id)
        self._settings_owner_tax_input.setText(selected.owner_tax_id)
        self._settings_mac_input.setText(selected.mac_address)
        self._settings_backend_type_input.setText(selected.backend_type)
        self._settings_backend_ip1_input.setText(selected.backend_ip1)
        self._settings_backend_port1_input.setText(str(selected.backend_port1 or ""))
        self._settings_backend_ip2_input.setText(selected.backend_ip2)
        self._settings_backend_port2_input.setText(str(selected.backend_port2 or ""))
        self._settings_force_online_checkbox.setChecked(selected.force_to_work_online)
        self._settings_plu_update_no_input.setValue(selected.plu_update_no)

    def _on_keyboard_row_selected(self) -> None:
        selected = self._selected_row_payload(self._keyboard_table, self._keyboards)
        if selected is None:
            return
        self._selected_keyboard_id = selected.id
        self._keyboard_name_input.setText(selected.name)
        self._keyboard_width_input.setValue(selected.keyboard_width)
        self._keyboard_height_input.setValue(selected.keyboard_height)
        self._keyboard_x_input.setValue(selected.x_position)
        self._keyboard_y_input.setValue(selected.y_position)
        self._keyboard_font_family_input.setText(selected.font_family)
        self._keyboard_font_size_input.setValue(selected.font_size)
        self._keyboard_button_width_input.setValue(selected.button_width)
        self._keyboard_button_height_input.setValue(selected.button_height)
        self._keyboard_button_bg_input.setText(selected.button_background_color)
        self._keyboard_button_pressed_input.setText(selected.button_pressed_color)
        self._keyboard_control_width_input.setValue(selected.control_button_width)
        self._keyboard_control_active_input.setText(selected.control_button_active_color)
        self._keyboard_active_checkbox.setChecked(selected.is_active)

    def _save_terminal(self) -> None:
        payload = {
            "terminal_code": self._terminal_code_input.text(),
            "terminal_name": self._terminal_name_input.text(),
            "terminal_serial_no": self._terminal_serial_input.text(),
            "host_name": self._terminal_host_input.text(),
            "ip_address": self._terminal_ip_input.text(),
            "app_mode": self._terminal_app_mode_input.text(),
            "software_version": self._terminal_software_version_input.text(),
            "pull_interval_seconds": self._terminal_pull_interval_input.value(),
            "is_active": self._terminal_active_checkbox.isChecked(),
            "is_online": self._terminal_online_checkbox.isChecked(),
            "is_allowed_pull": self._terminal_allowed_pull_checkbox.isChecked(),
        }
        result = self.service.save_pos_terminal(payload=payload, terminal_id=self._selected_terminal_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_terminals()
            self._clear_terminal_editor()

    def _delete_terminal(self) -> None:
        if not self._selected_terminal_id:
            self._set_status(False, "Please select a POS terminal to delete.")
            return
        if not self._confirm_delete("Delete POS Terminal", "Selected POS terminal will be soft deleted. Continue?"):
            return
        result = self.service.delete_pos_terminal(self._selected_terminal_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_terminal_editor()

    def _save_settings(self) -> None:
        payload = {
            "fk_pos_terminal_id": self._settings_terminal_combo.currentData(),
            "pos_no_in_store": self._settings_no_input.value(),
            "name": self._settings_name_input.text(),
            "owner_national_id": self._settings_owner_national_input.text(),
            "owner_tax_id": self._settings_owner_tax_input.text(),
            "mac_address": self._settings_mac_input.text(),
            "backend_type": self._settings_backend_type_input.text(),
            "backend_ip1": self._settings_backend_ip1_input.text(),
            "backend_port1": self._settings_backend_port1_input.text(),
            "backend_ip2": self._settings_backend_ip2_input.text(),
            "backend_port2": self._settings_backend_port2_input.text(),
            "force_to_work_online": self._settings_force_online_checkbox.isChecked(),
            "plu_update_no": self._settings_plu_update_no_input.value(),
        }
        result = self.service.save_pos_settings(payload=payload, settings_id=self._selected_settings_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_settings()
            self._clear_settings_editor()

    def _delete_settings(self) -> None:
        if not self._selected_settings_id:
            self._set_status(False, "Please select a POS settings row to delete.")
            return
        if not self._confirm_delete("Delete POS Settings", "Selected POS settings row will be soft deleted. Continue?"):
            return
        result = self.service.delete_pos_settings(self._selected_settings_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_settings()
            self._clear_settings_editor()

    def _save_keyboard(self) -> None:
        payload = {
            "name": self._keyboard_name_input.text(),
            "keyboard_width": self._keyboard_width_input.value(),
            "keyboard_height": self._keyboard_height_input.value(),
            "x_position": self._keyboard_x_input.value(),
            "y_position": self._keyboard_y_input.value(),
            "font_family": self._keyboard_font_family_input.text(),
            "font_size": self._keyboard_font_size_input.value(),
            "button_width": self._keyboard_button_width_input.value(),
            "button_height": self._keyboard_button_height_input.value(),
            "button_background_color": self._keyboard_button_bg_input.text(),
            "button_pressed_color": self._keyboard_button_pressed_input.text(),
            "control_button_width": self._keyboard_control_width_input.value(),
            "control_button_active_color": self._keyboard_control_active_input.text(),
            "is_active": self._keyboard_active_checkbox.isChecked(),
        }
        result = self.service.save_pos_virtual_keyboard(
            payload=payload,
            keyboard_id=self._selected_keyboard_id,
        )
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_virtual_keyboards()
            self._clear_keyboard_editor()

    def _delete_keyboard(self) -> None:
        if not self._selected_keyboard_id:
            self._set_status(False, "Please select a virtual keyboard row to delete.")
            return
        if not self._confirm_delete(
            "Delete Virtual Keyboard",
            "Selected virtual keyboard row will be soft deleted. Continue?",
        ):
            return
        result = self.service.delete_pos_virtual_keyboard(self._selected_keyboard_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_virtual_keyboards()
            self._clear_keyboard_editor()

    def _reload_terminal_combos(self) -> None:
        items = [(row.id, row.label) for row in self.service.list_pos_terminal_lookups()]
        self._reload_combo(
            self._settings_terminal_filter_combo,
            rows=items,
            include_empty=True,
            empty_label="All",
        )
        self._reload_combo(
            self._settings_terminal_combo,
            rows=items,
            include_empty=True,
            empty_label="None",
        )

    def _clear_terminal_editor(self) -> None:
        self._selected_terminal_id = None
        self._terminal_table.clearSelection()
        self._terminal_code_input.clear()
        self._terminal_name_input.clear()
        self._terminal_serial_input.clear()
        self._terminal_host_input.clear()
        self._terminal_ip_input.clear()
        self._terminal_app_mode_input.clear()
        self._terminal_software_version_input.clear()
        self._terminal_pull_interval_input.setValue(30)
        self._terminal_active_checkbox.setChecked(True)
        self._terminal_online_checkbox.setChecked(False)
        self._terminal_allowed_pull_checkbox.setChecked(True)

    def _clear_settings_editor(self) -> None:
        self._selected_settings_id = None
        self._settings_table.clearSelection()
        self._settings_terminal_combo.setCurrentIndex(0)
        self._settings_no_input.setValue(1)
        self._settings_name_input.clear()
        self._settings_owner_national_input.clear()
        self._settings_owner_tax_input.clear()
        self._settings_mac_input.clear()
        self._settings_backend_type_input.setText("GATE")
        self._settings_backend_ip1_input.clear()
        self._settings_backend_port1_input.clear()
        self._settings_backend_ip2_input.clear()
        self._settings_backend_port2_input.clear()
        self._settings_force_online_checkbox.setChecked(False)
        self._settings_plu_update_no_input.setValue(0)

    def _clear_keyboard_editor(self) -> None:
        self._selected_keyboard_id = None
        self._keyboard_table.clearSelection()
        self._keyboard_name_input.clear()
        self._keyboard_width_input.setValue(970)
        self._keyboard_height_input.setValue(315)
        self._keyboard_x_input.setValue(0)
        self._keyboard_y_input.setValue(0)
        self._keyboard_font_family_input.setText("Noto Sans CJK JP")
        self._keyboard_font_size_input.setValue(20)
        self._keyboard_button_width_input.setValue(80)
        self._keyboard_button_height_input.setValue(40)
        self._keyboard_button_bg_input.setText(
            "qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,stop: 0 #f6f7fa, stop: 1 #dadbde)"
        )
        self._keyboard_button_pressed_input.setText("rgb(29, 150, 255)")
        self._keyboard_control_width_input.setValue(120)
        self._keyboard_control_active_input.setText("rgb(29, 150, 255)")
        self._keyboard_active_checkbox.setChecked(True)

    def _set_status(self, success: bool, message: str) -> None:
        self._status_label.setStyleSheet("color: #166534;" if success else "color: #b91c1c;")
        self._status_label.setText(message)

    @staticmethod
    def _reload_combo(
        combo: QComboBox,
        rows: list[tuple[str, str]],
        include_empty: bool,
        empty_label: str,
    ) -> None:
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        if include_empty:
            combo.addItem(empty_label, None)
        for item_id, label in rows:
            combo.addItem(label, item_id)
        if selected is not None:
            index = combo.findData(selected)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    @staticmethod
    def _selected_row_payload(table: QTableWidget, rows: list) -> object | None:
        selected_items = table.selectedItems()
        if not selected_items:
            return None
        row_id = selected_items[0].data(Qt.UserRole)
        return next((item for item in rows if getattr(item, "id", None) == row_id), None)

    def _confirm_delete(self, title: str, text: str) -> bool:
        answer = QMessageBox.question(
            self,
            title,
            text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes
