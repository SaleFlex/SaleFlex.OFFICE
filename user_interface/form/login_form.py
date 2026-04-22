"""
Keyboard-first login form for SaleFlex.OFFICE.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from office.service.auth_service import AuthService
from office.service.bootstrap_loader import BootstrapContext
from settings.settings import Settings


class LoginForm(QWidget):
    """Static login form shown after startup bootstrap completes."""

    login_success = Signal(str)

    def __init__(self, bootstrap_context: BootstrapContext, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.bootstrap_context = bootstrap_context
        self.auth_service = AuthService()
        self.setObjectName("loginRoot")
        self.setWindowTitle(f"{Settings().app_name} - Login")
        self.setMinimumSize(1024, 640)

        self._title_label = QLabel("Sign In")
        self._title_label.setObjectName("titleLabel")
        self._title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self._title_label.setAlignment(Qt.AlignHCenter)

        self._subtitle_label = QLabel(
            f"Store: {bootstrap_context.store_id}  |  Office: {bootstrap_context.office_id}"
        )
        self._subtitle_label.setObjectName("subtitleLabel")
        self._subtitle_label.setAlignment(Qt.AlignHCenter)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Username")
        self._username_input.setClearButtonEnabled(True)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Password")
        self._password_input.setEchoMode(QLineEdit.Password)

        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setWordWrap(True)

        self._login_button = QPushButton("Login")
        self._login_button.setObjectName("loginButton")
        self._login_button.setDefault(True)
        self._login_button.clicked.connect(self._on_login_clicked)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        username_label = QLabel("Username")
        username_label.setObjectName("formLabel")
        password_label = QLabel("Password")
        password_label.setObjectName("formLabel")
        form_layout.addRow(username_label, self._username_input)
        form_layout.addRow(password_label, self._password_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self._login_button)

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)
        card_layout.addWidget(self._title_label)
        card_layout.addWidget(self._subtitle_label)
        card_layout.addSpacing(4)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(self._status_label)
        card_layout.addLayout(button_layout)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFrameShape(QFrame.StyledPanel)
        card.setMaximumWidth(560)
        card.setLayout(card_layout)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(80, 60, 80, 60)
        root_layout.addStretch(1)
        root_layout.addWidget(card, alignment=Qt.AlignHCenter)
        root_layout.addStretch(1)
        self.setLayout(root_layout)
        self._apply_styles()

        self._username_input.setFocus()

    def _on_login_clicked(self) -> None:
        """Validate login fields and authenticate with cashier records."""
        username = self._username_input.text().strip()
        password = self._password_input.text()

        if not username or not password:
            self._status_label.setStyleSheet("color: #b91c1c;")
            self._status_label.setText("Please enter both username and password.")
            return

        auth_result = self.auth_service.authenticate(username=username, password=password)
        if auth_result.success:
            self._status_label.setStyleSheet("color: #166534;")
            self._status_label.setText(auth_result.message)
            self.login_success.emit(auth_result.username)
            return

        self._status_label.setStyleSheet("color: #b91c1c;")
        self._status_label.setText(auth_result.message)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.showFullScreen()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#loginRoot {
                background-color: #111827;
            }
            QFrame#loginCard {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
            }
            QLabel#titleLabel {
                color: #0f172a;
                background: transparent;
            }
            QLabel#subtitleLabel {
                color: #475569;
                background: transparent;
            }
            QLabel#formLabel {
                color: #1e293b;
                font-weight: 600;
                background: transparent;
            }
            QLabel#statusLabel {
                color: #b91c1c;
                background: transparent;
            }
            QLineEdit {
                color: #0f172a;
                background-color: #f8fafc;
                border: 1px solid #94a3b8;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #2563eb;
                background-color: #ffffff;
            }
            QPushButton#loginButton {
                color: #ffffff;
                background-color: #2563eb;
                border: 1px solid #1d4ed8;
                border-radius: 8px;
                padding: 8px 20px;
                min-width: 120px;
            }
            QPushButton#loginButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#loginButton:pressed {
                background-color: #1e40af;
            }
            """
        )
