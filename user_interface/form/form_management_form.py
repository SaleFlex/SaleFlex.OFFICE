"""
Form management module form with spreadsheet-style workflows.
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
    FormControlTabView,
    FormControlView,
    FormView,
    PosFormOperationView,
    PosManagementService,
)
from settings.settings import Settings
from user_interface.form.form_controls_list_form import FormControlsListForm
from user_interface.form.form_operations_form import FormOperationsForm


class FormManagementForm(QWidget):
    """Manage form, form control, and form control tab entities."""

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
        self.setWindowTitle(f"{Settings().app_name} - Form Management")
        self.setMinimumSize(1460, 920)

        self._forms: list[FormView] = []
        self._controls: list[FormControlView] = []
        self._tabs_rows: list[FormControlTabView] = []
        self._operations_rows: list[PosFormOperationView] = []

        self._selected_form_id: str | None = None
        self._selected_control_id: str | None = None
        self._selected_tab_id: str | None = None

        self._operations_window: FormOperationsForm | None = None
        self._controls_windows: list[FormControlsListForm] = []

        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        header = QLabel("Form Operations Center")
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
        self._tabs.addTab(self._build_forms_tab(), "Forms")
        self._tabs.addTab(self._build_controls_tab(), "Form Controls")
        self._tabs.addTab(self._build_control_tabs_tab(), "Form Control Tabs")
        self._tabs.addTab(self._build_operations_tab(), "Form Operations")

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(header_actions)
        root_layout.addWidget(self._status_label)
        root_layout.addWidget(self._tabs)
        self.setLayout(root_layout)

    def _build_forms_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self._form_search_input = QLineEdit()
        self._form_search_input.setPlaceholderText("Search form name, caption or function")
        self._form_search_input.returnPressed.connect(self.refresh_forms)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.refresh_forms)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_forms)
        search_layout.addWidget(self._form_search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)
        left_layout.addLayout(search_layout)

        self._form_table = QTableWidget(0, 11)
        self._form_table.setHorizontalHeaderLabels(
            [
                "Form No",
                "Name",
                "Function",
                "Caption",
                "Width",
                "Height",
                "Display Mode",
                "Scope",
                "POS Terminal",
                "Login",
                "Visible",
            ]
        )
        self._form_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._form_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._form_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._form_table.verticalHeader().setVisible(False)
        self._form_table.setAlternatingRowColors(True)
        self._form_table.itemSelectionChanged.connect(self._on_form_row_selected)
        left_layout.addWidget(self._form_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Form Editor")
        form = QFormLayout()
        self._form_no_input = QSpinBox()
        self._form_no_input.setRange(1, 999999)
        self._form_name_input = QLineEdit()
        self._form_function_input = QLineEdit()
        self._form_caption_input = QLineEdit()
        self._form_width_input = QLineEdit()
        self._form_height_input = QLineEdit()
        self._form_display_mode_combo = QComboBox()
        self._form_display_mode_combo.addItems(["MAIN", "CUSTOMER", "BOTH"])
        self._form_pos_scope_checkbox = QCheckBox("Available in All POS Terminals")
        self._form_pos_scope_checkbox.setChecked(True)
        self._form_pos_scope_checkbox.toggled.connect(self._on_form_scope_changed)
        self._form_pos_terminal_combo = QComboBox()
        self._form_pos_terminal_combo.currentIndexChanged.connect(self._update_form_pos_assignment_field)
        self._form_pos_assignment_input = QLineEdit()
        self._form_pos_assignment_input.setReadOnly(True)
        self._form_need_login_checkbox = QCheckBox("Need Login")
        self._form_need_auth_checkbox = QCheckBox("Need Auth")
        self._form_use_virtual_keyboard_checkbox = QCheckBox("Use Virtual Keyboard")
        self._form_visible_checkbox = QCheckBox("Visible")
        self._form_visible_checkbox.setChecked(True)
        self._form_startup_checkbox = QCheckBox("Startup Form")
        form.addRow("Form No", self._form_no_input)
        form.addRow("Name", self._form_name_input)
        form.addRow("Function", self._form_function_input)
        form.addRow("Caption", self._form_caption_input)
        form.addRow("Width", self._form_width_input)
        form.addRow("Height", self._form_height_input)
        form.addRow("Display Mode", self._form_display_mode_combo)
        form.addRow(self._form_pos_scope_checkbox)
        form.addRow("POS Terminal", self._form_pos_terminal_combo)
        form.addRow("Assigned POS", self._form_pos_assignment_input)
        form.addRow(self._form_need_login_checkbox)
        form.addRow(self._form_need_auth_checkbox)
        form.addRow(self._form_use_virtual_keyboard_checkbox)
        form.addRow(self._form_visible_checkbox)
        form.addRow(self._form_startup_checkbox)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        open_controls_button = QPushButton("Open Selected Form Controls")
        new_button.clicked.connect(self._clear_form_editor)
        save_button.clicked.connect(self._save_form)
        delete_button.clicked.connect(self._delete_form)
        open_controls_button.clicked.connect(self._open_controls_for_selected_form)
        actions.addWidget(new_button)
        actions.addWidget(save_button)
        actions.addWidget(delete_button)
        actions.addWidget(open_controls_button)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(form)
        editor_layout.addStretch(1)
        editor_layout.addLayout(actions)
        editor_box.setLayout(editor_layout)

        splitter.addWidget(left)
        splitter.addWidget(editor_box)
        splitter.setSizes([980, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_controls_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._control_form_filter_combo = QComboBox()
        self._control_form_filter_combo.currentIndexChanged.connect(self.refresh_form_controls)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_form_controls)
        filter_layout.addWidget(QLabel("Form"))
        filter_layout.addWidget(self._control_form_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._control_table = QTableWidget(0, 11)
        self._control_table.setHorizontalHeaderLabels(
            [
                "Form",
                "Name",
                "Type No",
                "Type",
                "Caption 1",
                "Caption 2",
                "Tab",
                "W",
                "H",
                "X",
                "Y",
            ]
        )
        self._control_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._control_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._control_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._control_table.verticalHeader().setVisible(False)
        self._control_table.setAlternatingRowColors(True)
        self._control_table.itemSelectionChanged.connect(self._on_control_row_selected)
        left_layout.addWidget(self._control_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Form Control Editor")
        form = QFormLayout()
        self._control_form_combo = QComboBox()
        self._control_name_input = QLineEdit()
        self._control_type_no_input = QSpinBox()
        self._control_type_no_input.setRange(0, 99999)
        self._control_type_input = QLineEdit()
        self._control_caption1_input = QLineEdit()
        self._control_caption2_input = QLineEdit()
        self._control_tab_combo = QComboBox()
        self._control_width_input = QSpinBox()
        self._control_width_input.setRange(0, 9999)
        self._control_height_input = QSpinBox()
        self._control_height_input.setRange(0, 9999)
        self._control_x_input = QSpinBox()
        self._control_x_input.setRange(-9999, 9999)
        self._control_y_input = QSpinBox()
        self._control_y_input.setRange(-9999, 9999)
        self._control_function1_input = QLineEdit()
        self._control_function2_input = QLineEdit()
        self._control_target_form_combo = QComboBox()
        self._control_visible_checkbox = QCheckBox("Visible")
        self._control_visible_checkbox.setChecked(True)
        form.addRow("Form", self._control_form_combo)
        form.addRow("Name", self._control_name_input)
        form.addRow("Type No", self._control_type_no_input)
        form.addRow("Type", self._control_type_input)
        form.addRow("Caption 1", self._control_caption1_input)
        form.addRow("Caption 2", self._control_caption2_input)
        form.addRow("Tab Page", self._control_tab_combo)
        form.addRow("Width", self._control_width_input)
        form.addRow("Height", self._control_height_input)
        form.addRow("Location X", self._control_x_input)
        form.addRow("Location Y", self._control_y_input)
        form.addRow("Function 1", self._control_function1_input)
        form.addRow("Function 2", self._control_function2_input)
        form.addRow("Target Form", self._control_target_form_combo)
        form.addRow(self._control_visible_checkbox)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        new_button.clicked.connect(self._clear_control_editor)
        save_button.clicked.connect(self._save_control)
        delete_button.clicked.connect(self._delete_control)
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
        splitter.setSizes([980, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_control_tabs_tab(self) -> QWidget:
        tab = QWidget()
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        self._tab_form_filter_combo = QComboBox()
        self._tab_form_filter_combo.currentIndexChanged.connect(self.refresh_form_control_tabs)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_form_control_tabs)
        filter_layout.addWidget(QLabel("Form"))
        filter_layout.addWidget(self._tab_form_filter_combo)
        filter_layout.addWidget(refresh_button)
        filter_layout.addStretch(1)
        left_layout.addLayout(filter_layout)

        self._tab_table = QTableWidget(0, 7)
        self._tab_table.setHorizontalHeaderLabels(
            ["Control Name", "Tab Index", "Tab Title", "Tooltip", "Back Color", "Fore Color", "Visible"]
        )
        self._tab_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tab_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tab_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tab_table.verticalHeader().setVisible(False)
        self._tab_table.setAlternatingRowColors(True)
        self._tab_table.itemSelectionChanged.connect(self._on_tab_row_selected)
        left_layout.addWidget(self._tab_table)
        left.setLayout(left_layout)

        editor_box = QGroupBox("Form Control Tab Editor")
        form = QFormLayout()
        self._tab_parent_control_combo = QComboBox()
        self._tab_index_input = QSpinBox()
        self._tab_index_input.setRange(0, 999)
        self._tab_title_input = QLineEdit()
        self._tab_tooltip_input = QLineEdit()
        self._tab_back_color_input = QLineEdit()
        self._tab_fore_color_input = QLineEdit()
        self._tab_visible_checkbox = QCheckBox("Visible")
        self._tab_visible_checkbox.setChecked(True)
        form.addRow("Parent Tab Control", self._tab_parent_control_combo)
        form.addRow("Tab Index", self._tab_index_input)
        form.addRow("Tab Title", self._tab_title_input)
        form.addRow("Tooltip", self._tab_tooltip_input)
        form.addRow("Back Color", self._tab_back_color_input)
        form.addRow("Fore Color", self._tab_fore_color_input)
        form.addRow(self._tab_visible_checkbox)

        actions = QHBoxLayout()
        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        new_button.clicked.connect(self._clear_tab_editor)
        save_button.clicked.connect(self._save_tab)
        delete_button.clicked.connect(self._delete_tab)
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
        splitter.setSizes([980, 420])
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        tab.setLayout(layout)
        return tab

    def _build_operations_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()

        actions = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_operations)
        open_controls_button = QPushButton("Open Selected Form Controls")
        open_controls_button.clicked.connect(self._open_controls_for_selected_operation_row)
        open_window_button = QPushButton("Open Form Operations Window")
        open_window_button.clicked.connect(self._open_operations_window)
        actions.addWidget(refresh_button)
        actions.addWidget(open_controls_button)
        actions.addStretch(1)
        actions.addWidget(open_window_button)
        layout.addLayout(actions)

        self._operations_table = QTableWidget(0, 7)
        self._operations_table.setHorizontalHeaderLabels(
            [
                "Form No",
                "Form Name",
                "Display Mode",
                "Control Count",
                "Visible",
                "Hidden",
                "Tab Page Count",
            ]
        )
        self._operations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._operations_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._operations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._operations_table.verticalHeader().setVisible(False)
        self._operations_table.setAlternatingRowColors(True)
        self._operations_table.itemDoubleClicked.connect(
            lambda _: self._open_controls_for_selected_operation_row()
        )
        layout.addWidget(self._operations_table)
        tab.setLayout(layout)
        return tab

    def refresh_all(self) -> None:
        self.refresh_forms()
        self.refresh_form_controls()
        self.refresh_form_control_tabs()
        self.refresh_operations()

    def refresh_forms(self) -> None:
        self._forms = self.service.list_forms(self._form_search_input.text().strip())
        self._reload_form_terminal_combo()
        self._form_table.setRowCount(len(self._forms))
        for row_index, row in enumerate(self._forms):
            values = [
                str(row.form_no),
                row.name,
                row.function,
                row.caption,
                str(row.width or ""),
                str(row.height or ""),
                row.display_mode,
                "ALL" if row.is_shared_across_pos else "TERMINAL",
                "ALL TERMINALS" if row.is_shared_across_pos else row.pos_terminal_label,
                "Yes" if row.need_login else "No",
                "Yes" if row.is_visible else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._form_table.setItem(row_index, col, item)
        self._form_table.resizeColumnsToContents()
        self._reload_form_combos()

    def refresh_form_controls(self) -> None:
        self._controls = self.service.list_form_controls(
            form_id=self._control_form_filter_combo.currentData()
        )
        self._control_table.setRowCount(len(self._controls))
        for row_index, row in enumerate(self._controls):
            values = [
                row.form_name,
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
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._control_table.setItem(row_index, col, item)
        self._control_table.resizeColumnsToContents()
        self._reload_tab_page_combos()

    def refresh_form_control_tabs(self) -> None:
        self._tabs_rows = self.service.list_form_control_tabs(form_id=self._tab_form_filter_combo.currentData())
        self._tab_table.setRowCount(len(self._tabs_rows))
        for row_index, row in enumerate(self._tabs_rows):
            values = [
                row.control_name,
                str(row.tab_index),
                row.tab_title,
                row.tab_tooltip,
                row.back_color,
                row.fore_color,
                "Yes" if row.is_visible else "No",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.id)
                self._tab_table.setItem(row_index, col, item)
        self._tab_table.resizeColumnsToContents()
        self._reload_tab_control_lookup_combo()

    def refresh_operations(self) -> None:
        self._operations_rows = self.service.list_pos_form_operations()
        self._operations_table.setRowCount(len(self._operations_rows))
        for row_index, row in enumerate(self._operations_rows):
            values = [
                str(row.form_no),
                row.form_name,
                row.display_mode,
                str(row.control_count),
                str(row.visible_control_count),
                str(row.hidden_control_count),
                str(row.tab_page_count),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, row.form_id)
                self._operations_table.setItem(row_index, col, item)
        self._operations_table.resizeColumnsToContents()
        self._operations_table.horizontalHeader().setStretchLastSection(True)

    def _on_form_row_selected(self) -> None:
        selected = self._selected_row_payload(self._form_table, self._forms)
        if selected is None:
            return
        self._selected_form_id = selected.id
        self._form_no_input.setValue(selected.form_no)
        self._form_name_input.setText(selected.name)
        self._form_function_input.setText(selected.function)
        self._form_caption_input.setText(selected.caption)
        self._form_width_input.setText(str(selected.width or ""))
        self._form_height_input.setText(str(selected.height or ""))
        self._form_display_mode_combo.setCurrentText(selected.display_mode or "MAIN")
        self._form_need_login_checkbox.setChecked(selected.need_login)
        self._form_need_auth_checkbox.setChecked(selected.need_auth)
        self._form_use_virtual_keyboard_checkbox.setChecked(selected.use_virtual_keyboard)
        self._form_visible_checkbox.setChecked(selected.is_visible)
        self._form_startup_checkbox.setChecked(selected.is_startup)
        self._form_pos_scope_checkbox.setChecked(selected.is_shared_across_pos)
        self._form_pos_terminal_combo.setCurrentIndex(
            self._form_pos_terminal_combo.findData(selected.fk_pos_terminal_id)
        )
        self._on_form_scope_changed()
        self._update_form_pos_assignment_field()

    def _on_control_row_selected(self) -> None:
        selected = self._selected_row_payload(self._control_table, self._controls)
        if selected is None:
            return
        self._selected_control_id = selected.id
        self._control_form_combo.setCurrentIndex(self._control_form_combo.findData(selected.fk_form_id))
        self._control_name_input.setText(selected.name)
        self._control_type_no_input.setValue(selected.type_no)
        self._control_type_input.setText(selected.type)
        self._control_caption1_input.setText(selected.caption1)
        self._control_caption2_input.setText(selected.caption2)
        self._control_tab_combo.setCurrentIndex(self._control_tab_combo.findData(selected.fk_tab_id))
        self._control_width_input.setValue(selected.width)
        self._control_height_input.setValue(selected.height)
        self._control_x_input.setValue(selected.location_x)
        self._control_y_input.setValue(selected.location_y)
        self._control_function1_input.setText(selected.form_control_function1)
        self._control_function2_input.setText(selected.form_control_function2)
        self._control_target_form_combo.setCurrentIndex(
            self._control_target_form_combo.findData(selected.fk_target_form_id)
        )
        self._control_visible_checkbox.setChecked(selected.is_visible)

    def _on_tab_row_selected(self) -> None:
        selected = self._selected_row_payload(self._tab_table, self._tabs_rows)
        if selected is None:
            return
        self._selected_tab_id = selected.id
        self._tab_parent_control_combo.setCurrentIndex(
            self._tab_parent_control_combo.findData(selected.fk_form_control_id)
        )
        self._tab_index_input.setValue(selected.tab_index)
        self._tab_title_input.setText(selected.tab_title)
        self._tab_tooltip_input.setText(selected.tab_tooltip)
        self._tab_back_color_input.setText(selected.back_color)
        self._tab_fore_color_input.setText(selected.fore_color)
        self._tab_visible_checkbox.setChecked(selected.is_visible)

    def _save_form(self) -> None:
        payload = {
            "form_no": self._form_no_input.value(),
            "name": self._form_name_input.text(),
            "function": self._form_function_input.text(),
            "caption": self._form_caption_input.text(),
            "width": self._form_width_input.text(),
            "height": self._form_height_input.text(),
            "display_mode": self._form_display_mode_combo.currentText(),
            "is_shared_across_pos": self._form_pos_scope_checkbox.isChecked(),
            "fk_pos_terminal_id": self._form_pos_terminal_combo.currentData(),
            "need_login": self._form_need_login_checkbox.isChecked(),
            "need_auth": self._form_need_auth_checkbox.isChecked(),
            "use_virtual_keyboard": self._form_use_virtual_keyboard_checkbox.isChecked(),
            "is_visible": self._form_visible_checkbox.isChecked(),
            "is_startup": self._form_startup_checkbox.isChecked(),
        }
        result = self.service.save_form(payload=payload, form_id=self._selected_form_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_forms()
            self._clear_form_editor()

    def _delete_form(self) -> None:
        if not self._selected_form_id:
            self._set_status(False, "Please select a form row to delete.")
            return
        if not self._confirm_delete("Delete Form", "Selected form row will be soft deleted. Continue?"):
            return
        result = self.service.delete_form(self._selected_form_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_all()
            self._clear_form_editor()

    def _save_control(self) -> None:
        payload = {
            "fk_form_id": self._control_form_combo.currentData(),
            "name": self._control_name_input.text(),
            "type_no": self._control_type_no_input.value(),
            "type": self._control_type_input.text(),
            "caption1": self._control_caption1_input.text(),
            "caption2": self._control_caption2_input.text(),
            "fk_tab_id": self._control_tab_combo.currentData(),
            "width": self._control_width_input.value(),
            "height": self._control_height_input.value(),
            "location_x": self._control_x_input.value(),
            "location_y": self._control_y_input.value(),
            "form_control_function1": self._control_function1_input.text(),
            "form_control_function2": self._control_function2_input.text(),
            "fk_target_form_id": self._control_target_form_combo.currentData(),
            "is_visible": self._control_visible_checkbox.isChecked(),
        }
        result = self.service.save_form_control(payload=payload, control_id=self._selected_control_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_form_controls()
            self._clear_control_editor()

    def _delete_control(self) -> None:
        if not self._selected_control_id:
            self._set_status(False, "Please select a form control row to delete.")
            return
        if not self._confirm_delete(
            "Delete Form Control",
            "Selected form control row will be soft deleted. Continue?",
        ):
            return
        result = self.service.delete_form_control(self._selected_control_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_form_controls()
            self._clear_control_editor()

    def _save_tab(self) -> None:
        payload = {
            "fk_form_control_id": self._tab_parent_control_combo.currentData(),
            "tab_index": self._tab_index_input.value(),
            "tab_title": self._tab_title_input.text(),
            "tab_tooltip": self._tab_tooltip_input.text(),
            "back_color": self._tab_back_color_input.text(),
            "fore_color": self._tab_fore_color_input.text(),
            "is_visible": self._tab_visible_checkbox.isChecked(),
        }
        result = self.service.save_form_control_tab(payload=payload, tab_id=self._selected_tab_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_form_control_tabs()
            self._clear_tab_editor()

    def _delete_tab(self) -> None:
        if not self._selected_tab_id:
            self._set_status(False, "Please select a form control tab row to delete.")
            return
        if not self._confirm_delete(
            "Delete Form Control Tab",
            "Selected form control tab row will be soft deleted. Continue?",
        ):
            return
        result = self.service.delete_form_control_tab(self._selected_tab_id)
        self._set_status(result.success, result.message)
        if result.success:
            self.refresh_form_control_tabs()
            self._clear_tab_editor()

    def _open_operations_window(self) -> None:
        if self._operations_window is None:
            self._operations_window = FormOperationsForm(
                bootstrap_context=self.bootstrap_context,
                username=self.username,
            )
        self._operations_window.show()
        self._operations_window.raise_()
        self._operations_window.activateWindow()

    def _open_controls_for_selected_form(self) -> None:
        if not self._selected_form_id:
            self._set_status(False, "Please select a form first.")
            return
        selected = next((row for row in self._forms if row.id == self._selected_form_id), None)
        if selected is None:
            self._set_status(False, "Selected form could not be resolved.")
            return
        self._open_controls_window_for_form(form_id=selected.id, label=f"{selected.form_no} - {selected.name}")

    def _open_controls_for_selected_operation_row(self) -> None:
        selected_items = self._operations_table.selectedItems()
        if not selected_items:
            self._set_status(False, "Please select an operations row first.")
            return
        form_id = selected_items[0].data(Qt.UserRole)
        row = selected_items[0].row()
        form_no = self._operations_table.item(row, 0).text() if self._operations_table.item(row, 0) else "?"
        form_name = self._operations_table.item(row, 1).text() if self._operations_table.item(row, 1) else ""
        self._open_controls_window_for_form(form_id=str(form_id), label=f"{form_no} - {form_name}")

    def _open_controls_window_for_form(self, form_id: str, label: str) -> None:
        window = FormControlsListForm(
            bootstrap_context=self.bootstrap_context,
            username=self.username,
            form_id=form_id,
            form_label=label,
        )
        window.show()
        window.raise_()
        window.activateWindow()
        self._controls_windows.append(window)

    def _reload_form_combos(self) -> None:
        items = [(row.id, row.label) for row in self.service.list_form_lookups()]
        self._reload_combo(self._control_form_filter_combo, items, include_empty=True, empty_label="All")
        self._reload_combo(self._control_form_combo, items, include_empty=False, empty_label="")
        self._reload_combo(self._control_target_form_combo, items, include_empty=True, empty_label="None")
        self._reload_combo(self._tab_form_filter_combo, items, include_empty=True, empty_label="All")

    def _reload_form_terminal_combo(self) -> None:
        items = [(row.id, row.label) for row in self.service.list_pos_terminal_lookups()]
        self._reload_combo(
            self._form_pos_terminal_combo,
            rows=items,
            include_empty=True,
            empty_label="Select POS terminal",
        )
        self._on_form_scope_changed()
        self._update_form_pos_assignment_field()

    def _reload_tab_page_combos(self) -> None:
        selected_form_id = self._control_form_combo.currentData()
        tabs = self.service.list_form_control_tabs(form_id=selected_form_id)
        tab_items = [(row.id, f"{row.control_name} / {row.tab_index} - {row.tab_title}") for row in tabs]
        self._reload_combo(self._control_tab_combo, tab_items, include_empty=True, empty_label="None")

    def _reload_tab_control_lookup_combo(self) -> None:
        selected_form_id = self._tab_form_filter_combo.currentData()
        items = [(row.id, row.label) for row in self.service.list_tab_control_lookups(form_id=selected_form_id)]
        self._reload_combo(
            self._tab_parent_control_combo,
            rows=items,
            include_empty=False,
            empty_label="",
        )

    def _clear_form_editor(self) -> None:
        self._selected_form_id = None
        self._form_table.clearSelection()
        self._form_no_input.setValue(1)
        self._form_name_input.clear()
        self._form_function_input.clear()
        self._form_caption_input.clear()
        self._form_width_input.clear()
        self._form_height_input.clear()
        self._form_display_mode_combo.setCurrentText("MAIN")
        self._form_pos_scope_checkbox.setChecked(True)
        self._form_pos_terminal_combo.setCurrentIndex(0)
        self._form_need_login_checkbox.setChecked(False)
        self._form_need_auth_checkbox.setChecked(False)
        self._form_use_virtual_keyboard_checkbox.setChecked(False)
        self._form_visible_checkbox.setChecked(True)
        self._form_startup_checkbox.setChecked(False)
        self._on_form_scope_changed()
        self._update_form_pos_assignment_field()

    def _on_form_scope_changed(self, _checked: bool | None = None) -> None:
        is_shared = self._form_pos_scope_checkbox.isChecked()
        self._form_pos_terminal_combo.setEnabled(not is_shared)
        if is_shared and self._form_pos_terminal_combo.count() > 0:
            self._form_pos_terminal_combo.setCurrentIndex(0)
        self._update_form_pos_assignment_field()

    def _update_form_pos_assignment_field(self, _index: int | None = None) -> None:
        if self._form_pos_scope_checkbox.isChecked():
            self._form_pos_assignment_input.setText("ALL TERMINALS")
            return
        label = self._form_pos_terminal_combo.currentText().strip()
        self._form_pos_assignment_input.setText(label or "NOT SELECTED")

    def _clear_control_editor(self) -> None:
        self._selected_control_id = None
        self._control_table.clearSelection()
        if self._control_form_combo.count() > 0:
            self._control_form_combo.setCurrentIndex(0)
        self._control_name_input.clear()
        self._control_type_no_input.setValue(0)
        self._control_type_input.clear()
        self._control_caption1_input.clear()
        self._control_caption2_input.clear()
        self._control_tab_combo.setCurrentIndex(0)
        self._control_width_input.setValue(0)
        self._control_height_input.setValue(0)
        self._control_x_input.setValue(0)
        self._control_y_input.setValue(0)
        self._control_function1_input.clear()
        self._control_function2_input.clear()
        self._control_target_form_combo.setCurrentIndex(0)
        self._control_visible_checkbox.setChecked(True)

    def _clear_tab_editor(self) -> None:
        self._selected_tab_id = None
        self._tab_table.clearSelection()
        if self._tab_parent_control_combo.count() > 0:
            self._tab_parent_control_combo.setCurrentIndex(0)
        self._tab_index_input.setValue(0)
        self._tab_title_input.clear()
        self._tab_tooltip_input.clear()
        self._tab_back_color_input.clear()
        self._tab_fore_color_input.clear()
        self._tab_visible_checkbox.setChecked(True)

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
