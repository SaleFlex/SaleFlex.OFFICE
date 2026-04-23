"""
System Settings form for SaleFlex.OFFICE.

All settings are displayed on a single scrollable page, organised into
clearly labelled sections:

  1. Application Mode  — standalone vs gate
  2. Store Identity    — store_code, office_code
  3. POS Server        — host:port that SaleFlex.PyPOS terminals connect to
  4. GATE Integration  — GATE base URL, API key, sync parameters

Settings are persisted directly to settings.toml on save, and the in-memory
Settings singleton is reloaded via Settings.reload() immediately afterwards.
"""

from __future__ import annotations

from pathlib import Path

import tomllib
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from office.service.bootstrap_loader import BootstrapContext
from settings.settings import Settings

_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "settings.toml"

# ─────────────────────────────────────────────────────────────────────────────
# TOML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_raw() -> dict:
    """Return the full settings.toml content as a plain dict."""
    with _SETTINGS_PATH.open("rb") as fh:
        return tomllib.load(fh)


def _bool_toml(value: bool) -> str:
    return "true" if value else "false"


def _write_toml(data: dict) -> None:
    """Serialise *data* back to settings.toml, preserving all known sections."""
    app = data.get("app", {})
    log = data.get("logging", {})
    db  = data.get("database", {})
    net = data.get("network", {})
    gate = data.get("gate", {})
    sec  = data.get("security", {})
    imp  = data.get("import", {})
    rep  = data.get("reporting", {})

    icon_escaped    = str(app.get("icon", r"static_files\images\saleflex-office.ico")).replace("\\", "\\\\")
    staging_escaped = str(imp.get("staging_dir", r"imports\staging")).replace("\\", "\\\\")
    archive_escaped = str(imp.get("archive_dir", r"imports\archive")).replace("\\", "\\\\")
    error_escaped   = str(imp.get("error_dir",   r"imports\errors")).replace("\\", "\\\\")

    lines = [
        "[app]",
        f'name = "{app.get("name", "SaleFlex.OFFICE")}"',
        f'version = "{app.get("version", "0.1.0-alpha")}"',
        f'mode = "{app.get("mode", "standalone")}" # standalone | gate',
        f'store_code = "{app.get("store_code", "STORE-001")}"',
        f'office_code = "{app.get("office_code", "OFFICE-001")}"',
        f'icon = "{icon_escaped}"',
        "",
        "[logging]",
        f'level = "{log.get("level", "INFO")}" # DEBUG | INFO | WARNING | ERROR | CRITICAL',
        f'console = {_bool_toml(bool(log.get("console", True)))}',
        f'file = {_bool_toml(bool(log.get("file", True)))}',
        f'log_dir = "{log.get("log_dir", "logs")}"',
        f'log_file = "{log.get("log_file", "saleflex-office.log")}"',
        "",
        "[database]",
        f'engine = "{db.get("engine", "sqlite")}" # sqlite | postgresql | mysql | oracle | mssql',
        f'driver = "{db.get("driver", "")}"',
        f'user_name = "{db.get("user_name", "")}"',
        f'password = "{db.get("password", "")}"',
        f'database_name = "{db.get("database_name", "office.sqlite3")}"',
        "",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "# POS Server endpoint",
        "# SaleFlex.PyPOS terminals connect to this host:port when running in",
        '# "office" mode (app.mode = "office" in PyPOS settings.toml).',
        '# host = "0.0.0.0" listens on all interfaces; change to a specific IP to',
        "# restrict access.",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "[network]",
        f'host = "{net.get("host", "0.0.0.0")}"',
        f'port = {int(net.get("port", 8710))}',
        f'api_prefix = "{net.get("api_prefix", "/api/v1")}"',
        f'request_timeout_seconds = {int(net.get("request_timeout_seconds", 15))}',
        "",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "# SaleFlex.GATE integration",
        '# Used only when app.mode = "gate".',
        "# OFFICE will periodically pull new data from GATE and push local POS data to",
        "# it (transactions, closures, warehouse movements, etc.).",
        "# ─────────────────────────────────────────────────────────────────────────────",
        "[gate]",
        f'base_url = "{gate.get("base_url", "")}"',
        f'api_key = "{gate.get("api_key", "")}"',
        f'terminal_id = "{gate.get("terminal_id", "")}"',
        f'sync_interval_minutes = {int(gate.get("sync_interval_minutes", 15))}',
        f'retry_attempts = {int(gate.get("retry_attempts", 3))}',
        f'timeout_seconds = {int(gate.get("timeout_seconds", 15))}',
        "",
        "[security]",
        f'password_hash = "{sec.get("password_hash", "bcrypt")}"',
        f'jwt_access_minutes = {int(sec.get("jwt_access_minutes", 30))}',
        f'jwt_refresh_days = {int(sec.get("jwt_refresh_days", 7))}',
        f'session_idle_timeout_minutes = {int(sec.get("session_idle_timeout_minutes", 30))}',
        "",
        "[import]",
        f'csv_enabled = {_bool_toml(bool(imp.get("csv_enabled", True)))}',
        f'xml_enabled = {_bool_toml(bool(imp.get("xml_enabled", True)))}',
        f'max_file_mb = {int(imp.get("max_file_mb", 50))}',
        f'staging_dir = "{staging_escaped}"',
        f'archive_dir = "{archive_escaped}"',
        f'error_dir = "{error_escaped}"',
        "",
        "[reporting]",
        f'dashboard_enabled = {_bool_toml(bool(rep.get("dashboard_enabled", True)))}',
        f'csv_export_enabled = {_bool_toml(bool(rep.get("csv_export_enabled", True)))}',
        f'pdf_export_enabled = {_bool_toml(bool(rep.get("pdf_export_enabled", True)))}',
        f'default_timezone = "{rep.get("default_timezone", "UTC")}"',
        f'currency_code = "{rep.get("currency_code", "USD")}"',
    ]
    _SETTINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────────

def _section_label(text: str) -> QLabel:
    """Return a styled section-header label."""
    lbl = QLabel(text)
    lbl.setObjectName("sectionLabel")
    lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
    return lbl


def _divider() -> QFrame:
    """Return a horizontal dividing line."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setObjectName("divider")
    return line


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("hintLabel")
    lbl.setWordWrap(True)
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
# Main form
# ─────────────────────────────────────────────────────────────────────────────

class SystemSettingsForm(QWidget):
    """
    Configure SaleFlex.OFFICE system settings.

    All settings are shown on a single scrollable page — no tabs — so every
    option is reachable regardless of OS colour theme.
    """

    def __init__(
        self,
        bootstrap_context: BootstrapContext,
        username: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.username = username
        self.setWindowTitle(f"{Settings().app_name} - System Settings")
        self.setMinimumSize(780, 680)

        self._raw: dict = _load_raw()

        # ── scroll area that holds all settings sections ──────────────────
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(10)

        self._build_mode_section(content_layout)
        content_layout.addWidget(_divider())
        self._build_identity_section(content_layout)
        content_layout.addWidget(_divider())
        self._build_pos_server_section(content_layout)
        content_layout.addWidget(_divider())
        self._build_gate_section(content_layout)
        content_layout.addStretch(1)

        scroll_content.setLayout(content_layout)

        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        # ── title bar ─────────────────────────────────────────────────────
        title_lbl = QLabel("System Settings")
        title_lbl.setObjectName("formTitle")
        title_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))

        subtitle_lbl = QLabel(
            f"User: {username}  |  Store: {bootstrap_context.store_code}  |  Office: {bootstrap_context.office_code}"
        )
        subtitle_lbl.setObjectName("formSubtitle")

        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)

        # ── action buttons ────────────────────────────────────────────────
        save_btn = QPushButton("  Save Settings")
        save_btn.setObjectName("saveButton")
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._on_save)

        close_btn = QPushButton("  Close")
        close_btn.setObjectName("closeButton")
        close_btn.setMinimumHeight(38)
        close_btn.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)

        # ── root layout ───────────────────────────────────────────────────
        root = QVBoxLayout()
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(12)
        root.addLayout(header_layout)
        root.addWidget(_divider())
        root.addWidget(scroll, 1)
        root.addWidget(_divider())
        root.addLayout(btn_layout)
        self.setLayout(root)

        self._apply_styles()

    # ── section builders ──────────────────────────────────────────────────

    def _build_mode_section(self, parent: QVBoxLayout) -> None:
        """Section 1 — Application Mode."""
        parent.addWidget(_section_label("1 — Application Mode"))

        app = self._raw.get("app", {})
        current_mode = str(app.get("mode", "standalone"))

        mode_group = QGroupBox()
        mode_group.setObjectName("settingsGroup")
        mode_layout = QVBoxLayout()
        mode_layout.setContentsMargins(14, 14, 14, 14)
        mode_layout.setSpacing(10)

        self._mode_standalone = QRadioButton(
            "Standalone  —  local-only, no synchronization with SaleFlex.GATE"
        )
        self._mode_standalone.setObjectName("modeRadio")

        self._mode_gate = QRadioButton(
            "Gate  —  periodically sync data with SaleFlex.GATE"
        )
        self._mode_gate.setObjectName("modeRadio")

        # Ensure mutual exclusivity
        _btn_group = QButtonGroup(self)
        _btn_group.addButton(self._mode_standalone)
        _btn_group.addButton(self._mode_gate)

        if current_mode == "gate":
            self._mode_gate.setChecked(True)
        else:
            self._mode_standalone.setChecked(True)

        mode_layout.addWidget(self._mode_standalone)
        mode_layout.addWidget(self._mode_gate)
        mode_layout.addWidget(
            _hint(
                "Note: changing the mode requires an application restart "
                "to take full effect. The POS Server and GATE settings below "
                "will be active from the next startup."
            )
        )
        mode_group.setLayout(mode_layout)
        parent.addWidget(mode_group)

    def _build_identity_section(self, parent: QVBoxLayout) -> None:
        """Section 2 — Store Identity."""
        parent.addWidget(_section_label("2 — Store Identity"))

        app = self._raw.get("app", {})

        id_group = QGroupBox()
        id_group.setObjectName("settingsGroup")
        form = QFormLayout()
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self._store_code_edit = QLineEdit(str(app.get("store_code", "STORE-001")))
        self._store_code_edit.setObjectName("settingsInput")
        self._store_code_edit.setPlaceholderText("e.g. STORE-001")

        self._office_code_edit = QLineEdit(str(app.get("office_code", "OFFICE-001")))
        self._office_code_edit.setObjectName("settingsInput")
        self._office_code_edit.setPlaceholderText("e.g. OFFICE-001")

        form.addRow("Store Code:", self._store_code_edit)
        form.addRow("Office Code:", self._office_code_edit)
        id_group.setLayout(form)
        parent.addWidget(id_group)

    def _build_pos_server_section(self, parent: QVBoxLayout) -> None:
        """Section 3 — POS Server (network endpoint for PyPOS terminals)."""
        parent.addWidget(_section_label("3 — POS Server  (PyPOS Connection Endpoint)"))
        parent.addWidget(
            _hint(
                "SaleFlex.PyPOS terminals running in office mode connect to this "
                "host and port to retrieve data and submit transactions. "
                "Use 0.0.0.0 to listen on all network interfaces, or enter the "
                "specific LAN IP of this machine to restrict access."
            )
        )

        net = self._raw.get("network", {})

        srv_group = QGroupBox()
        srv_group.setObjectName("settingsGroup")
        form = QFormLayout()
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self._network_host_edit = QLineEdit(str(net.get("host", "0.0.0.0")))
        self._network_host_edit.setObjectName("settingsInput")
        self._network_host_edit.setPlaceholderText("0.0.0.0  or  192.168.1.x")

        self._network_port_spin = QSpinBox()
        self._network_port_spin.setObjectName("settingsInput")
        self._network_port_spin.setRange(1, 65535)
        self._network_port_spin.setValue(int(net.get("port", 8710)))

        self._network_prefix_edit = QLineEdit(str(net.get("api_prefix", "/api/v1")))
        self._network_prefix_edit.setObjectName("settingsInput")
        self._network_prefix_edit.setPlaceholderText("/api/v1")

        self._network_timeout_spin = QSpinBox()
        self._network_timeout_spin.setObjectName("settingsInput")
        self._network_timeout_spin.setRange(5, 120)
        self._network_timeout_spin.setSuffix(" sec")
        self._network_timeout_spin.setValue(int(net.get("request_timeout_seconds", 15)))

        form.addRow("Bind Host:", self._network_host_edit)
        form.addRow("Port:", self._network_port_spin)
        form.addRow("API Prefix:", self._network_prefix_edit)
        form.addRow("Request Timeout:", self._network_timeout_spin)

        note_row = QLabel(
            "PyPOS settings.toml:  [office]  base_url = \"http://&lt;host&gt;:&lt;port&gt;\""
        )
        note_row.setObjectName("codeHint")
        form.addRow("", note_row)

        srv_group.setLayout(form)
        parent.addWidget(srv_group)

    def _build_gate_section(self, parent: QVBoxLayout) -> None:
        """Section 4 — SaleFlex.GATE integration."""
        parent.addWidget(_section_label("4 — SaleFlex.GATE Integration"))
        parent.addWidget(
            _hint(
                "Active only when Application Mode is set to Gate. "
                "OFFICE will pull master-data updates from GATE at the configured "
                "interval and push local POS data (transactions, closures, "
                "warehouse movements) back to GATE."
            )
        )

        gate = self._raw.get("gate", {})

        # Connection sub-group
        conn_group = QGroupBox("Connection")
        conn_group.setObjectName("settingsGroup")
        conn_form = QFormLayout()
        conn_form.setContentsMargins(14, 14, 14, 14)
        conn_form.setHorizontalSpacing(16)
        conn_form.setVerticalSpacing(10)

        self._gate_url_edit = QLineEdit(str(gate.get("base_url", "")))
        self._gate_url_edit.setObjectName("settingsInput")
        self._gate_url_edit.setPlaceholderText("http://192.168.1.100:8800")

        self._gate_api_key_edit = QLineEdit(str(gate.get("api_key", "")))
        self._gate_api_key_edit.setObjectName("settingsInput")
        self._gate_api_key_edit.setPlaceholderText("API key issued by SaleFlex.GATE")
        self._gate_api_key_edit.setEchoMode(QLineEdit.Password)

        self._gate_show_key_chk = QCheckBox("Show key")
        self._gate_show_key_chk.setObjectName("showKeyCheck")
        self._gate_show_key_chk.toggled.connect(self._toggle_gate_key_visibility)

        self._gate_terminal_id_edit = QLineEdit(str(gate.get("terminal_id", "")))
        self._gate_terminal_id_edit.setObjectName("settingsInput")
        self._gate_terminal_id_edit.setPlaceholderText("e.g. OFFICE-001")

        api_key_row = QHBoxLayout()
        api_key_row.setSpacing(8)
        api_key_row.addWidget(self._gate_api_key_edit, 1)
        api_key_row.addWidget(self._gate_show_key_chk)

        api_key_container = QWidget()
        api_key_container.setLayout(api_key_row)

        conn_form.addRow("GATE Base URL:", self._gate_url_edit)
        conn_form.addRow("API Key:", api_key_container)
        conn_form.addRow("Terminal ID:", self._gate_terminal_id_edit)
        conn_group.setLayout(conn_form)

        # Sync sub-group
        sync_group = QGroupBox("Sync Behaviour")
        sync_group.setObjectName("settingsGroup")
        sync_form = QFormLayout()
        sync_form.setContentsMargins(14, 14, 14, 14)
        sync_form.setHorizontalSpacing(16)
        sync_form.setVerticalSpacing(10)

        self._gate_sync_interval_spin = QSpinBox()
        self._gate_sync_interval_spin.setObjectName("settingsInput")
        self._gate_sync_interval_spin.setRange(1, 1440)
        self._gate_sync_interval_spin.setSuffix(" min")
        self._gate_sync_interval_spin.setValue(int(gate.get("sync_interval_minutes", 15)))

        self._gate_retry_spin = QSpinBox()
        self._gate_retry_spin.setObjectName("settingsInput")
        self._gate_retry_spin.setRange(1, 10)
        self._gate_retry_spin.setValue(int(gate.get("retry_attempts", 3)))

        self._gate_timeout_spin = QSpinBox()
        self._gate_timeout_spin.setObjectName("settingsInput")
        self._gate_timeout_spin.setRange(5, 120)
        self._gate_timeout_spin.setSuffix(" sec")
        self._gate_timeout_spin.setValue(int(gate.get("timeout_seconds", 15)))

        sync_form.addRow("Sync Interval:", self._gate_sync_interval_spin)
        sync_form.addRow("Retry Attempts:", self._gate_retry_spin)
        sync_form.addRow("Request Timeout:", self._gate_timeout_spin)
        sync_group.setLayout(sync_form)

        parent.addWidget(conn_group)
        parent.addWidget(sync_group)

    # ── slot helpers ──────────────────────────────────────────────────────

    def _toggle_gate_key_visibility(self, show: bool) -> None:
        self._gate_api_key_edit.setEchoMode(
            QLineEdit.Normal if show else QLineEdit.Password
        )

    # ── save ──────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        """Collect all widget values, write settings.toml, reload singleton."""
        # Section 1 — mode
        self._raw.setdefault("app", {})
        self._raw["app"]["mode"] = "gate" if self._mode_gate.isChecked() else "standalone"

        # Section 2 — identity
        self._raw["app"]["store_code"]  = self._store_code_edit.text().strip()
        self._raw["app"]["office_code"] = self._office_code_edit.text().strip()

        # Section 3 — POS Server
        self._raw.setdefault("network", {})
        self._raw["network"]["host"]                    = self._network_host_edit.text().strip()
        self._raw["network"]["port"]                    = self._network_port_spin.value()
        self._raw["network"]["api_prefix"]              = self._network_prefix_edit.text().strip()
        self._raw["network"]["request_timeout_seconds"] = self._network_timeout_spin.value()

        # Section 4 — GATE
        self._raw.setdefault("gate", {})
        self._raw["gate"]["base_url"]             = self._gate_url_edit.text().strip()
        self._raw["gate"]["api_key"]              = self._gate_api_key_edit.text().strip()
        self._raw["gate"]["terminal_id"]          = self._gate_terminal_id_edit.text().strip()
        self._raw["gate"]["sync_interval_minutes"] = self._gate_sync_interval_spin.value()
        self._raw["gate"]["retry_attempts"]        = self._gate_retry_spin.value()
        self._raw["gate"]["timeout_seconds"]       = self._gate_timeout_spin.value()

        try:
            _write_toml(self._raw)
            Settings.reload()
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved to settings.toml.\n\n"
                "Note: mode changes and server bindings take full effect "
                "after an application restart.",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not write settings.toml:\n{exc}",
            )

    # ── styles ────────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            /* ── form root ─────────────────────────────────────── */
            QWidget {
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
                color: #1e293b;
            }

            SystemSettingsForm,
            QWidget#scrollContent {
                background-color: #f1f5f9;
            }

            /* ── scroll area ───────────────────────────────────── */
            QScrollArea#mainScroll {
                background-color: #f1f5f9;
                border: none;
            }
            QScrollArea#mainScroll > QWidget > QWidget {
                background-color: #f1f5f9;
            }

            /* ── title / subtitle ──────────────────────────────── */
            QLabel#formTitle {
                color: #0f172a;
            }
            QLabel#formSubtitle {
                color: #64748b;
                font-size: 12px;
            }

            /* ── section headings ──────────────────────────────── */
            QLabel#sectionLabel {
                color: #1d4ed8;
                padding-top: 6px;
            }

            /* ── hint / description text ───────────────────────── */
            QLabel#hintLabel {
                color: #475569;
                font-size: 12px;
                padding: 2px 4px;
            }
            QLabel#codeHint {
                color: #64748b;
                font-size: 11px;
                font-style: italic;
            }

            /* ── horizontal divider ────────────────────────────── */
            QFrame#divider {
                color: #cbd5e1;
            }

            /* ── group boxes ───────────────────────────────────── */
            QGroupBox#settingsGroup {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 6px;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #374151;
                font-weight: 600;
            }

            /* ── input controls ────────────────────────────────── */
            QLineEdit#settingsInput,
            QSpinBox#settingsInput {
                background-color: #ffffff;
                border: 1px solid #94a3b8;
                border-radius: 5px;
                padding: 5px 10px;
                min-height: 28px;
                color: #0f172a;
            }
            QLineEdit#settingsInput:focus,
            QSpinBox#settingsInput:focus {
                border: 2px solid #1d4ed8;
            }
            QSpinBox#settingsInput::up-button,
            QSpinBox#settingsInput::down-button {
                width: 18px;
            }

            /* ── radio buttons ─────────────────────────────────── */
            QRadioButton#modeRadio {
                font-size: 13px;
                spacing: 8px;
                color: #1e293b;
                padding: 3px 0;
            }
            QRadioButton#modeRadio::indicator {
                width: 16px;
                height: 16px;
            }

            /* ── checkbox ──────────────────────────────────────── */
            QCheckBox#showKeyCheck {
                color: #64748b;
                font-size: 12px;
                spacing: 6px;
            }

            /* ── save button ───────────────────────────────────── */
            QPushButton#saveButton {
                background-color: #1d4ed8;
                color: #ffffff;
                border: 1px solid #1e40af;
                border-radius: 6px;
                padding: 6px 24px;
                font-weight: 700;
                min-width: 150px;
            }
            QPushButton#saveButton:hover  { background-color: #1e40af; }
            QPushButton#saveButton:pressed { background-color: #1e3a8a; }

            /* ── close button ──────────────────────────────────── */
            QPushButton#closeButton {
                background-color: #64748b;
                color: #ffffff;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 6px 24px;
                font-weight: 600;
                min-width: 110px;
            }
            QPushButton#closeButton:hover  { background-color: #475569; }
            QPushButton#closeButton:pressed { background-color: #334155; }
            """
        )
